import sys
import os
from os.path import basename
from os.path import exists
from os.path import join
import re
import glob
import json
import datetime
import collections
from collections import OrderedDict
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
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return(repr(self.message))


class LSFPreambleSkipper:
    def __init__ (self, filename):
        with open(filename, 'rt') as f:
            header = f.readline().rstrip('\n')
        if re.match('^Sender: LSF System <[\w\d\_\.\@\-]+>$', header):
            seek_to_stdout_capture = True
        else:
            seek_to_stdout_capture = False
        self.f = open(filename, 'rt')
        if seek_to_stdout_capture:
            line = None
            while line != 'The output (if any) follows:\n': # There is a failure mode; need to put a guard based on the line length for the expected preambles. Failure mode when job was cancelled, different message intervenes here.
                line = self.f.readline()
            self.f.readline()
            position = self.f.tell()

            line = self.f.readline()
            line = ansi_escape.sub('', line)
            while re.search('^WARNING: ', line):
                position = self.f.tell()
                line = self.f.readline()
                line = ansi_escape.sub('', line)
            self.f.seek(position)

    def __enter__ (self):
        return self.f

    def __exit__ (self, exc_type, exc_value, traceback):
        self.f.close()


class LogParser:
    def __init__(self, path):
        self.path = path
        self.extractions = {}
        self.performance_report_base64 = ''
        self.performance_report_contents = ''

    def get_path(self):
        return self.path

    def get_inputs(self):
        path = self.get_path()
        filenames = {
            'config' : join(path, 'nextflow.config'),
            'nextflow log' : join(path, '.nextflow.log'),
            'performance report' : join(path, 'results', 'performance_report.md'),
            'run configuration log' : join(path, 'results', 'run_configuration.log'),
        }
        self.config_file = self.check_file(filenames['config'])
        self.nextflow_log = self.check_file(filenames['nextflow log'])
        self.performance_report = self.check_file(filenames['performance report'])
        self.run_configuration_log = self.check_file(filenames['run configuration log'])
        self.log_files = glob.glob(join(path, 'work/*/*/.command.log'))
        if len(self.log_files) == 0:
            raise LogParsingError('No log files found.')

    def check_file(self, target):
        if exists(target):
            return target
        else:
            raise LogParsingError('Essential log or config file not found: %s' % target)

    def remove_prefix(self, prefix, text):
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    def parse(self):
        self.get_inputs()
        self.extract_from_run_configuration_log()

        nf_header = open(self.nextflow_log, 'rt').readline().rstrip('\n')
        search = re.search('^(\w+)\-(\d+) \d+:\d+:\d+\.\d+', nf_header)
        if search:
            month = search.groups(1)[0]
            day = search.groups(1)[1]
            self.extractions['Run date'] = ' '.join([month, day, self.year])

        job_reports = self.extract_job_reports()
        self.extractions['Largest file size'] = str(int(sorted(
            job_reports,
            key=lambda x: -x['source file bytes'],
        )[0]['source file bytes'] / 1000000)) + 'MB'

        runtime = self.get_total_runtime()
        self.extractions['Total runtime'] = self.format_duration(runtime)

        number_cells = sum([
            job_report['number of cells'] for job_report in job_reports
        ])
        self.extractions['# cells'] = number_cells

        self.extractions['Time per 1M cells'] = self.format_duration(
            runtime / (number_cells / 1000000)
        )

        self.extractions['Longest job time'] = sorted(job_reports, key=lambda x: -x['duration']
        )[0]['duration minutes']

        self.performance_report_contents = open(self.performance_report, 'rt').read()

        message_bytes = self.performance_report_contents.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        self.performance_report_base64 = base64_bytes.decode('ascii')

        self.validate_all_extractions_found()

    def extract_from_run_configuration_log(self):
        self.year = None
        with open(self.run_configuration_log, 'rt') as f:
            for line in f:
                parts = self.parse_log_line(line.rstrip('\n'))
                if len(parts) != 0:
                    match = re.match('^Machine host: ([\w\d\-\.\(\)\[\]\&\,]+)$', parts['Message'])
                    if match:
                        self.extractions['Hostname'] = match.groups(1)[0]
                        continue

                    match = re.match('^Version: SPT v([\d\.]+)$', parts['Message'])
                    if match:
                        self.extractions['SPT'] = 'v' + match.groups(1)[0]
                        continue

                    match = re.match('^Dataset/project: "([\w \d\,\./\?\(\)\-]+)"$', parts['Message'])
                    if match:
                        self.extractions['Dataset'] = match.groups(1)[0]
                        continue

                    match = re.match('^Number of cell manifest files: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['# cell files'] = match.groups(1)[0]
                        continue

                    match = re.match('^Workflow: "([\w\d\- \.\(\)\[\]\&\,]+)"$', parts['Message'])
                    if match:
                        self.extractions['Workflow'] = match.groups(1)[0]
                        continue

                    match = re.match('^Number of channels: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['Channels'] = match.groups(1)[0]
                        continue

                    match = re.match('^Number of phenotypes considered: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['Phenotypes'] = match.groups(1)[0]
                        continue

                    match = re.match('^Number of compartments: (\d+)$', parts['Message'])
                    if match:
                        self.extractions['Compartments'] = match.groups(1)[0]
                        continue

                    match = re.match('^Run date year: (\d+)$', parts['Message'])
                    if match:
                        self.year = match.groups(1)[0]
                        continue
        if not self.year:
            self.year = 'YYYY'

    def validate_all_extractions_found(self):
        failed = [
            key for key in LogParser.get_order()
            if (not key in self.extractions) or (self.extractions[key] in self.extractions)
        ]
        if len(failed) > 0:
            raise LogParsingError('Some extractions not made: %s' % str(sorted(failed)))

    def get_total_runtime(self):
        nf_header = open(self.nextflow_log, 'rt').readline().rstrip('\n')
        timestamp1 = self.parse_nextflow_timestamp(nf_header)
        timestamp2 = self.parse_nextflow_timestamp(self.get_last_line(self.nextflow_log))
        return self.get_timedelta(timestamp1, timestamp2)

    def parse_nextflow_timestamp(self, line):
        search = re.search('^(\w+)\-0?(\d+) 0?(\d+):0?(\d+):0?(\d+\.\d+)', line)
        if search:
            month = 0 # Not parsing month abbreviation
            day = int(search.groups(1)[1])
            hour = int(search.groups(1)[2])
            minute = int(search.groups(1)[3])
            second = float(search.groups(1)[4])
            return (month, day, hour, minute, second)
        raise LogParsingError('Could not parse Nextflow log timestamp.')

    def get_last_line(self, filename):
        with open(filename, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()        
        return last_line

    def format_duration(self, duration):
        minutes = str(
            int(10 * duration.total_seconds() / 60) / 10
        ) 
        return re.sub('\.0', '', minutes) + 'm'

    def extract_exact(self, pattern, lines_limit=1):
        for log in self.log_files:
            with LSFPreambleSkipper(log) as f:
                line_count = 0
                line = None
                while line_count < lines_limit and line != '':
                    line = f.readline()
                    line_count = line_count + 1
                    match = re.search(pattern, line)
                    if match:
                        break
                if match:
                    return match.groups(1)
        raise LogParsingError('Essential pattern not found in log files: %s' % pattern)

    def extract_job_reports(self):
        job_reports = []
        for log in self.log_files:
            with open(log, 'rt') as f:
                job_report = {}
                start_time = None
                stop_time = None
                for line in f:
                    parts = self.parse_log_line(line.rstrip('\n'))
                    if len(parts) != 0:
                        if parts['Message'] == 'Started core calculator job.':
                            start_time = (parts['Month numeric'], parts['Day numeric'], parts['Hour'], parts['Minute'], parts['Second'])
                        if parts['Message'] == 'Completed core calculator job.':
                            stop_time = (parts['Month numeric'], parts['Day numeric'], parts['Hour'], parts['Minute'], parts['Second'])
                        match = re.match('^(\d+) cells to be parsed from source file "[\w\d\.\- \(\)\_\=]+".$', parts['Message'])
                        if match:
                            job_report['number of cells'] = int(match.groups(1)[0])

                        match = re.match('^Cells source file has size (\d+) bytes.$', parts['Message'])
                        if match:
                            job_report['source file bytes'] = int(match.groups(1)[0])
                if (not start_time is None) and (not stop_time is None):
                    # Will produce misleading result at year boundary, or leap year Feb boundary
                    duration = self.get_timedelta(start_time, stop_time)
                    job_report['duration'] = duration
                    job_report['duration minutes'] = self.format_duration(duration)
                if len(job_report) > 0:
                    if 'duration' in job_report:
                        job_reports.append(job_report)
        if len(job_reports) == 0:
            raise LogParsingError('No job info could be extracted.')
        return job_reports

    def days_diff(self, month1, month2, day1, day2):
        if month1 == month2:
            return day2 - day1
        elif month2 > month1:
            days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            return day2 + days_in_month[month1 - 1] - day1
        else:
            raise LogParsingError('Month duration unreasonable, from %s to %s.' % (month1, month2))

    def get_timedelta(self, t1, t2):
        duration = datetime.timedelta(
            days = self.days_diff(t1[0], t2[0], t1[1], t2[1]),
            hours = t2[2] - t1[2],
            minutes = t2[3] - t1[3],
            seconds = t2[4] - t1[4],
        )
        return duration

    def parse_log_line(self, line):
        ansi_cleaned = ansi_escape.sub('', line)
        pattern = '^0?(\d+)-0?(\d+) 0?(\d+):0?(\d+):0?(\d+) \[ *(\w+) *\] [\w\d\.\_]+: (.*)$'
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
    def __init__(self, format_handle=None):
        working_directories = []
        for root, dirs, files in os.walk('.'):
            if ('work' in dirs) and ('.nextflow.log' in files) and ('nextflow.config' in files):
                working_directories.append(root)
        self.parsers = [LogParser(path) for path in working_directories]
        self.format_handle = format_handle

        jinja_environment = jinja2.Environment(loader=jinja2.BaseLoader)
        def quote_hash(input):
            return re.sub('\#', '\\#', input)
        jinja_environment.filters['quote_hash'] = quote_hash

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
            except LogParsingError as e:
                print('Warning: Parsing error for run located at: %s' % parser.get_path(), file=sys.stderr)
                print(e, file=sys.stderr)

    def aggregate_reports_dataframe(self):
        rows = [parser.get_extractions_ordered() for parser in self.parsers]
        column_names = LogParser.get_order()
        return pd.DataFrame(rows, columns=column_names).sort_values(by=['Dataset', 'Workflow'])

    def textual_render(self, format_description):
        table = self.aggregate_reports_dataframe()
        rendered = ''
        if format_description == 'tex':
            with importlib.resources.path('spatialprofilingtoolbox.templates', 'log_table.tex.jinja') as path:
                log_report_template = open(path, 'rt').read()
                template = self.jinja_environment.from_string(log_report_template)
                rows = [LogParser.get_order()] + [parser.get_extractions_ordered() for parser in self.parsers]
                rendered = template.render(rows=rows)
        if format_description == 'HTML':
            with importlib.resources.path('spatialprofilingtoolbox.templates', 'log_table.html.jinja') as path:
                log_report_template = open(path, 'rt').read()
                template = self.jinja_environment.from_string(log_report_template)
                ordered_parsers = sorted(self.parsers, key=lambda p: p.get_sort_key())
                rendered = template.render(
                    header=LogParser.get_order() + ['CPU usage'],
                    rows=[parser.get_extractions_ordered() + [i] for i, parser in enumerate(ordered_parsers)],
                    base64_contents=[parser.performance_report_base64 for parser in ordered_parsers],
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
    exit()

if __name__=='__main__':
    args = sys.argv
    if len(args) > 1:
        if args[1] == '--help':
            show_help()
            exit()
    format_handle = None
    if len(args) > 1:
        if args[1] in LogReportAggregator.get_formats():
            format_handle = args[1]
            args = args[1:]
    if len(args) > 1:
        show_help()
        exit()
    else:
        import spatialprofilingtoolbox
        from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException

        try:
            import pandas as pd
            import jinja2
        except ModuleNotFoundError as e:
            SuggestExtrasException(e, 'workflow')

        aggregator = LogReportAggregator(format_handle=format_handle)
        aggregator.retrieve_reports()
        aggregator.report_on_all()

