"""Create a report on the Nextflow logs. For debugging and archival purposes."""
import sys
import os
from os.path import exists
from os.path import join
import re
import glob
import datetime
import importlib.resources
import base64

ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)


class LogParsingError(Exception):
    """Custom exception for log parsing. To simply printing error messages."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return repr(self.message)


class LSFPreambleSkipper:
    """File reading that skips possible 'LSF' system-generated preamble."""

    def __init__(self, filename):
        with open(filename, 'rt', encoding='utf-8') as file:
            header = file.readline().rstrip('\n')
        seek_to_stdout_capture = bool(re.match(r'^Sender: LSF System <[\w\d\_\.\@\-]+>$', header))
        self.file = open(filename, 'rt', encoding='utf-8')  # pylint: disable=consider-using-with
        if seek_to_stdout_capture:
            line = None
            # There is a failure mode; need to put a guard based on the line length for the
            # expected preambles. Failure mode when job was cancelled, different message intervenes
            # here.
            while line != 'The output (if any) follows:\n':
                line = self.file.readline()
            self.file.readline()
            position = self.file.tell()

            line = self.file.readline()
            line = ansi_escape.sub('', line)
            while re.search('^WARNING: ', line):
                position = self.file.tell()
                line = self.file.readline()
                line = ansi_escape.sub('', line)
            self.file.seek(position)

    def __enter__(self):
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()


class LogParser:
    """Parse logs generated during a Nextflow run of an SPT workflow."""

    def __init__(self, path):
        self.path = path
        self.extractions = {}
        self.year = ''
        self.performance_report = {'file': '', 'base64': '', 'contents': ''}
        self.source_files = {'config': '', 'nextflow log': '', 'logs': [], 'run configuration': ''}

    def get_path(self):
        return self.path

    def get_inputs(self):
        path = self.get_path()
        filenames = {
            'config': join(path, 'nextflow.config'),
            'nextflow log': join(path, '.nextflow.log'),
            'performance report': join(path, 'results', 'performance_report.md'),
            'run configuration log': join(path, 'results', 'run_configuration.log'),
        }
        self.source_files['config'] = self.check_file(filenames['config'])
        self.source_files['nextflow log'] = self.check_file(filenames['nextflow log'])
        self.performance_report['file'] = self.check_file(
            filenames['performance report'])
        self.source_files['run configuration'] = self.check_file(
            filenames['run configuration log'])
        self.source_files['logs'] = glob.glob(join(path, 'work/*/*/.command.log'))
        if len(self.source_files['log']) == 0:
            raise LogParsingError('No log files found.')

    def check_file(self, target):
        if exists(target):
            return target
        raise LogParsingError(f'Essential log or config file not found: {target}')

    def remove_prefix(self, prefix, text):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    def parse(self):
        self.get_inputs()
        self.extract_from_run_configuration_log()

        with open(self.source_files['nextflow log'], 'rt', encoding='utf-8') as file:
            nf_header = file.readline().rstrip('\n')
        search = re.search(r'^(\w+)\-(\d+) \d+:\d+:\d+\.\d+', nf_header)
        if search:
            month = str(search.groups(1)[0])
            day = str(search.groups(1)[1])
            self.extractions['Run date'] = ' '.join([month, day, self.year])

        job_reports = self.extract_job_reports()
        self.extractions['Largest file size'] = str(int(sorted(
            job_reports,
            key=lambda x: -x['source file bytes'],
        )[0]['source file bytes'] / 1000000)) + 'MB'

        runtime = self.get_total_runtime()
        self.extractions['Total runtime'] = self.format_duration(runtime)

        number_cells = sum(job_report['number of cells'] for job_report in job_reports)
        self.extractions['# cells'] = number_cells

        self.extractions['Time per 1M cells'] = self.format_duration(
            runtime / (number_cells / 1000000)
        )

        self.extractions['Longest job time'] = sorted(job_reports, key=lambda x: -x['duration']
                                                      )[0]['duration minutes']

        with open(self.performance_report['file'], 'rt', encoding='utf-8') as file:
            self.performance_report['contents'] = file.read()

        message_bytes = self.performance_report['contents'].encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        self.performance_report['base64'] = base64_bytes.decode('ascii')

        self.validate_all_extractions_found()

    def extract_from_run_configuration_log(self):
        self.year = ''
        with open(self.source_files['run configuration'], 'rt', encoding='utf-8') as file:
            for line in file:
                parts = self.parse_log_line(line.rstrip('\n'))
                if len(parts) != 0:
                    match = re.match(
                        r'^Machine host: ([\w\d\-\.\(\)\[\]\&\,]+)$', parts['Message'])
                    if match:
                        self.extractions['Hostname'] = match.groups(1)[0]
                        continue

                    match = re.match(
                        r'^Version: SPT v([\d\.]+)$', parts['Message'])
                    if match:
                        self.extractions['SPT'] = 'v' + str(match.groups(1)[0])
                        continue

                    match = re.match(
                        r'^Dataset/project: "([\w \d\,\./\?\(\)\-]+)"$', parts['Message'])
                    if match:
                        self.extractions['Dataset'] = match.groups(1)[0]
                        continue

                    match = re.match(
                        r'^Number of cell manifest files: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['# cell files'] = match.groups(1)[0]
                        continue

                    match = re.match(
                        r'^Workflow: "([\w\d\- \.\(\)\[\]\&\,]+)"$', parts['Message'])
                    if match:
                        self.extractions['Workflow'] = match.groups(1)[0]
                        continue

                    match = re.match(
                        r'^Number of channels: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['Channels'] = match.groups(1)[0]
                        continue

                    match = re.match(
                        r'^Number of phenotypes considered: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['Phenotypes'] = match.groups(1)[0]
                        continue

                    match = re.match(r'^Run date year: (\d+)$',
                                     parts['Message'])
                    if match:
                        self.year = str(match.groups(1)[0])
                        continue
        if self.year == '':
            self.year = 'YYYY'

    def validate_all_extractions_found(self):
        failed = [
            key for key in LogParser.get_order()
            if (not key in self.extractions) or (self.extractions[key] in self.extractions)
        ]
        if len(failed) > 0:
            raise LogParsingError(
                f'Some extractions not made: {str(sorted(failed))}')

    def get_total_runtime(self):
        with open(self.source_files['nextflow log'], 'rt', encoding='utf-8') as file:
            nf_header = file.readline().rstrip('\n')
        timestamp1 = self.parse_nextflow_timestamp(nf_header)
        timestamp2 = self.parse_nextflow_timestamp(
            self.get_last_line(self.source_files['nextflow log']))
        return self.get_timedelta(timestamp1, timestamp2)

    def parse_nextflow_timestamp(self, line):
        search = re.search(
            r'^(\w+)\-0?(\d+) 0?(\d+):0?(\d+):0?(\d+\.\d+)', line)
        if search:
            month = 0  # Not parsing month abbreviation
            day = int(search.groups(1)[1])
            hour = int(search.groups(1)[2])
            minute = int(search.groups(1)[3])
            second = float(search.groups(1)[4])
            return (month, day, hour, minute, second)
        raise LogParsingError('Could not parse Nextflow log timestamp.')

    def get_last_line(self, filename):
        with open(filename, 'rb') as file:
            try:
                file.seek(-2, os.SEEK_END)
                while file.read(1) != b'\n':
                    file.seek(-2, os.SEEK_CUR)
            except OSError:
                file.seek(0)
            last_line = file.readline().decode()
        return last_line

    def format_duration(self, duration):
        minutes = str(
            int(10 * duration.total_seconds() / 60) / 10
        )
        return re.sub(r'\.0', '', minutes) + 'm'

    def extract_exact(self, pattern, lines_limit=1):
        for log in self.source_files['logs']:
            with LSFPreambleSkipper(log) as file:
                line_count = 0
                line = None
                match = None
                while line_count < lines_limit and line != '':
                    line = file.readline()
                    line_count = line_count + 1
                    match = re.search(pattern, line)
                    if match:
                        break
                if match:
                    return match.groups(1)
        raise LogParsingError(
            f'Essential pattern not found in log files: {pattern}')

    def extract_job_reports(self):
        job_reports = []
        for log in self.source_files['logs']:
            with open(log, 'rt', encoding='utf-8') as file:
                job_report = {}
                start_time = None
                stop_time = None
                for line in file:
                    parts = self.parse_log_line(line.rstrip('\n'))
                    if len(parts) != 0:
                        if parts['Message'] == 'Started core calculator job.':
                            start_time = (parts['Month numeric'], parts['Day numeric'],
                                          parts['Hour'], parts['Minute'], parts['Second'])
                        if parts['Message'] == 'Completed core calculator job.':
                            stop_time = (parts['Month numeric'], parts['Day numeric'],
                                         parts['Hour'], parts['Minute'], parts['Second'])
                        match = re.match(
                            r'^(\d+) cells to be parsed from source file "[\w\d\.\- \(\)\_\=]+".$',
                            parts['Message'])
                        if match:
                            job_report['number of cells'] = int(
                                match.groups(1)[0])

                        match = re.match(
                            r'^Cells source file has size (\d+) bytes.$', parts['Message'])
                        if match:
                            job_report['source file bytes'] = int(
                                match.groups(1)[0])
                if (not start_time is None) and (not stop_time is None):
                    # Will produce misleading result at year boundary, or leap year Feb boundary
                    duration = self.get_timedelta(start_time, stop_time)
                    job_report['duration'] = duration
                    job_report['duration minutes'] = self.format_duration(
                        duration)
                if len(job_report) > 0:
                    if 'duration' in job_report:
                        job_reports.append(job_report)
        if len(job_reports) == 0:
            raise LogParsingError('No job info could be extracted.')
        return job_reports

    def days_diff(self, month1, month2, day1, day2):
        if month1 == month2:
            return day2 - day1
        if month2 > month1:
            days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return day2 + days_in_month[month1 - 1] - day1
        raise LogParsingError(
            f'Month duration unreasonable, from {month1} to {month2}.')

    def get_timedelta(self, time1, time2):
        duration = datetime.timedelta(
            days=self.days_diff(time1[0], time2[0], time1[1], time2[1]),
            hours=time2[2] - time1[2],
            minutes=time2[3] - time1[3],
            seconds=time2[4] - time1[4],
        )
        return duration

    def parse_log_line(self, line):
        ansi_cleaned = ansi_escape.sub('', line)
        pattern = r'^0?(\d+)-0?(\d+) 0?(\d+):0?(\d+):0?(\d+) \[ *(\w+) *\] [\w\d\.\_]+: (.*)$'
        match = re.match(pattern, ansi_cleaned)
        parsed_tokens = {}
        if match:
            parsed_tokens['Month numeric'] = int(match.groups(1)[0])
            parsed_tokens['Day numeric'] = int(match.groups(1)[1])
            parsed_tokens['Hour'] = int(match.groups(1)[2])
            parsed_tokens['Minute'] = int(match.groups(1)[3])
            parsed_tokens['Second'] = float(match.groups(1)[4])
            parsed_tokens['Message class'] = match.groups(1)[5]
            parsed_tokens['Message'] = match.groups(1)[6]
        return parsed_tokens

    def get_extractions(self):
        return self.extractions

    def get_sort_key(self):
        return (
            self.extractions['Dataset'] if 'Dataset' in self.extractions else '*',
            self.extractions['Workflow'] if 'Workflow' in self.extractions else '*',
        )

    @staticmethod
    def get_order():
        order = [
            'Run date',
            'Hostname',
            'Dataset',
            'Channels',
            'Phenotypes',
            'Compartments',
            '# cell files',
            '# cells',
            'Largest file size',
            'Workflow',
            'SPT',
            'Total runtime',
            'Time per 1M cells',
            'Longest job time',
        ]
        return order

    def get_extractions_ordered(self):
        return [
            str(self.extractions[key]) if key in self.extractions else '*'
            for key in LogParser.get_order()
        ]


class LogReportAggregator:
    """Aggregate together many log files that are created by a Nextflow run of an
    SPT workflow.
    """

    def __init__(self, format_handle=None):
        working_directories = []
        for root, dirs, files in os.walk('.'):
            if ('work' in dirs) and ('.nextflow.log' in files) and ('nextflow.config' in files):
                working_directories.append(root)
        self.parsers = [LogParser(path) for path in working_directories]
        self.format_handle = format_handle

        self.jinja_environment = jinja2.Environment(loader=jinja2.BaseLoader())

        def quote_hash(input_string):
            return re.sub(r'\#', r'\\#', input_string)
        self.jinja_environment.filters['quote_hash'] = quote_hash

    @staticmethod
    def get_formats():
        return [
            'tex',
            'HTML',
            'TSV',
            'JSON',
            'markdown',
        ]

    def retrieve_reports(self):
        for parser in self.parsers:
            try:
                parser.parse()
            except LogParsingError as exception:
                print(f'Warning: Parsing error for run located at: {parser.get_path()}',
                      file=sys.stderr)
                print(exception, file=sys.stderr)

    def aggregate_reports_dataframe(self):
        rows = [parser.get_extractions_ordered() for parser in self.parsers]
        column_names = LogParser.get_order()
        return pd.DataFrame(rows, columns=column_names).sort_values(by=['Dataset', 'Workflow'])

    def textual_render(self, format_description):
        table = self.aggregate_reports_dataframe()
        rendered = ''
        if format_description == 'tex':
            with importlib.resources.path('spatialprofilingtoolbox.workflow.assets',
                                          'log_table.tex.jinja') as path:
                with open(path, 'rt', encoding='utf-8') as file:
                    log_report_template = file.read()
                template = self.jinja_environment.from_string(log_report_template)
                rows = [LogParser.get_order()] + [parser.get_extractions_ordered()
                                                  for parser in self.parsers]
                rendered = template.render(rows=rows)
        if format_description == 'HTML':
            with importlib.resources.path('spatialprofilingtoolbox.workflow.assets',
                                          'log_table.html.jinja') as path:
                with open(path, 'rt', encoding='utf-8') as file:
                    log_report_template = file.read()
                template = self.jinja_environment.from_string(log_report_template)
                ordered_parsers = sorted(
                    self.parsers, key=lambda p: p.get_sort_key())
                rendered = template.render(
                    header=LogParser.get_order() + ['CPU usage'],
                    rows=[parser.get_extractions_ordered() + [i]
                          for i, parser in enumerate(ordered_parsers)],
                    base64_contents=[
                        parser.performance_report['base64'] for parser in ordered_parsers],
                )
        if format_description == 'TSV':
            rendered = table.to_csv(index=False, sep='\t')
        if format_description == 'JSON':
            rendered = table.to_json(orient='records', indent=4)
        if format_description == 'markdown':
            rendered = table.to_markdown(index=False)
        return rendered.rstrip('\n')

    def report_on_all(self):
        if self.format_handle:
            print(self.textual_render(self.format_handle))
        else:
            for format_description in LogReportAggregator.get_formats():
                print('')
                print('[ ' + format_description + ' ]')
                print(self.textual_render(format_description))


def show_help():
    print('Optional argument one of:\n%s' % '\n'.join(
        ['  ' + f for f in LogReportAggregator.get_formats()]
    ))
    sys.exit()


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        if args[1] == '--help':
            show_help()
            sys.exit()
    FORMAT_HANDLE_ARG = None
    if len(args) > 1:
        if args[1] in LogReportAggregator.get_formats():
            FORMAT_HANDLE_ARG = args[1]
            args = args[1:]
    if len(args) > 1:
        show_help()
        sys.exit()
    else:
        from spatialprofilingtoolbox.standalone_utilities.module_load_error import \
            SuggestExtrasException

        try:
            import pandas as pd
            import jinja2
        except ModuleNotFoundError as e:
            SuggestExtrasException(e, 'workflow')

        aggregator = LogReportAggregator(format_handle=FORMAT_HANDLE_ARG)
        aggregator.retrieve_reports()
        aggregator.report_on_all()
