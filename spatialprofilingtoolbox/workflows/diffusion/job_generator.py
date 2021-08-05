import math
import os
from os.path import join, exists, abspath
from os import mkdir
import stat
import errno
import re
import sqlite3

import pandas as pd

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ...environment.job_generator import JobGenerator, JobActivity
from ...environment.log_formats import colorized_logger
from .computational_design import DiffusionDesign

logger = colorized_logger(__name__)


class DiffusionJobGenerator(JobGenerator):
    lsf_template = '''#!/bin/bash
#BSUB -J {{job_name}}
#BSUB -n "1"
#BSUB -W 4:00
#BSUB -R "rusage[mem={{memory_in_gb}}]"
#BSUB -R "span[hosts=1]"
#BSUB -R "select[hname!={{excluded_hostname}}]"
cd {{job_working_directory}}
export DEBUG=1
singularity exec \
 --bind {{input_files_path}}:{{input_files_path}}\
 {{sif_file}} \
 {{cli_call}} \
 > {{log_filename}} 2>&1
'''
    cli_call_template = '''spt-diffusion-analysis \
 --input-file-identifier {{input_file_identifier}} \
 --fov {{fov_index}} \
 --regional-compartment {{regional_compartment}} \
 --job-index {{job_index}} \
'''
    file_metadata_header = '''file id\tnumber of FOVs\n
'''

    def __init__(self,
        elementary_phenotypes_file: str=None,
        complex_phenotypes_file: str=None,
        **kwargs,
    ):
        """
        Args:
            elementary_phenotypes_file (str):
                Tabular file listing phenotypes of consideration. See dataset designs.
            complex_phenotypes_file (str):
                Tabular file listing composite phenotypes to consider. See
                ``diffusion.computational_design``.
        """
        super(DiffusionJobGenerator, self).__init__(**kwargs)
        self.dataset_design = HALOCellMetadataDesign(
            elementary_phenotypes_file,
        )
        self.computational_design = DiffusionDesign(
            dataset_design=self.dataset_design,
            complex_phenotypes_file=complex_phenotypes_file,
        )

        self.number_fovs = {}
        self.submit_calls = {rc: [] for rc in self.get_regional_compartments()}
        self.local_run_calls = {rc: [] for rc in self.get_regional_compartments()}

    def get_regional_compartments(self):
        return ('tumor', 'edge', 'nontumor')

    def gather_input_info(self):
        for i, row in self.file_metadata.iterrows():
            filename = row['File name']
            if not exists(join(self.dataset_settings.input_path, filename)):
                logger.warning('Data file could not be located: %s', filename)
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

        cache_filename = '.file_metadata.cache'
        if not exists(cache_filename):
            with open(cache_filename, 'w') as cache:
                cache.write(DiffusionJobGenerator.file_metadata_header)
        file_metadata = pd.read_csv(cache_filename, sep='\t', index_col=0)

        number_files = self.file_metadata.shape[0]
        for i, row in self.file_metadata.iterrows():
            if row['Data type'] == HALOCellMetadataDesign.get_cell_manifest_descriptor():
                file_id = row['File ID']
                if file_id in file_metadata.index:
                    n = file_metadata.loc[file_id]['number of FOVs']
                    self.number_fovs[file_id] = n
                    logger.debug('Using cached info about file %s / %s  ... %s', str(i+1), str(number_files), file_id)
                else:
                    filename = row['File name']
                    fovs = cut_by_header(join(self.dataset_settings.input_path, filename), column=self.dataset_design.get_FOV_column())
                    n = len(sorted(list(set(fovs))))
                    self.number_fovs[file_id] = n
                    file_metadata.loc[file_id] = {'number of FOVs' : str(n)}
                    logger.debug('Gathered input info from file %s / %s  ... %s', str(i+1), str(number_files), file_id)

        file_metadata.to_csv(cache_filename, sep='\t')

    def generate_all_jobs(self):
        self.number_arrays_of_jobs = 0
        self.initialize_intermediate_database()
        for i, row in self.file_metadata.iterrows():
            if row['Data type'] == HALOCellMetadataDesign.get_cell_manifest_descriptor():
                self.generate_array_of_jobs(row)
        logger.info('%s input files considered.', str(self.file_metadata.shape[0]))
        logger.info('%s (arrays of) job scripts generated, written to dir %s', str(self.number_arrays_of_jobs), self.jobs_paths.jobs_path)
        average = sum(self.number_fovs.values()) / len(self.number_fovs)
        logger.debug('Average size of job arrays is %s.', str(average))

    def initialize_intermediate_database(self):
        """
        The diffusion workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        probabilities_header = self.computational_design.get_probabilities_table_header()

        connection = sqlite3.connect(join(self.jobs_paths.output_path, self.computational_design.get_database_uri()))
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS transition_probabilities ;')
        cmd = ' '.join([
            'CREATE TABLE',
            'transition_probabilities',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            probabilities_header[0] + ' NUMERIC,',
            probabilities_header[1] + ' VARCHAR(25),',
            probabilities_header[2] + ' INTEGER,',
            probabilities_header[3] + ' NUMERIC,',
            probabilities_header[4] + ' TEXT',
            ');',
        ])
        cursor.execute(cmd)

        cursor.execute('DROP TABLE IF EXISTS job_metadata ;')
        keys = self.computational_design.get_job_metadata_header()
        keys = [re.sub(' ', '_', key) for key in keys]
        cmd = ' '.join([
            'CREATE TABLE',
            'job_metadata',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([key + ' TEXT' for key in keys]),
            ');',
        ])
        cursor.execute(cmd)

        cursor.close()
        connection.commit()
        connection.close()

    def generate_array_of_jobs(self, file_record):
        """
        Generates all the jobs, one for each field of view, for the indicated file.

        Args:
            file_id (str):
                Input file identifier, as it would appear in the file manifest file.
        """
        file_id = file_record['File ID']

        job_working_directory = self.jobs_paths.job_working_directory
        input_file_identifier = file_id
        number_fovs = self.number_fovs[input_file_identifier]
        logger.debug('Number of FOVs for %s: %s', input_file_identifier, str(number_fovs))

        for rc in self.get_regional_compartments():
            if rc == 'nontumor':
                for i in range(number_fovs):
                    fov_index = i + 1
                    job_index = self.register_job_existence()
                    job_name = 'diffusion_' + str(job_index)
                    log_filename = join(self.jobs_paths.logs_path, job_name + '.out')
                    memory_in_gb = self.get_memory_requirements(file_record)

                    contents = DiffusionJobGenerator.lsf_template
                    contents = re.sub('{{input_files_path}}', self.dataset_settings.input_path, contents)
                    contents = re.sub('{{job_working_directory}}', job_working_directory, contents)
                    contents = re.sub('{{job_name}}', job_name, contents)
                    contents = re.sub('{{log_filename}}', log_filename, contents)
                    contents = re.sub('{{sif_file}}', self.runtime_settings.sif_file, contents)
                    contents = re.sub('{{memory_in_gb}}', str(memory_in_gb), contents)
                    contents = re.sub('{{excluded_hostname}}', self.excluded_hostname, contents)
                    bsub_job = contents

                    contents = DiffusionJobGenerator.cli_call_template
                    contents = re.sub('{{input_file_identifier}}', '"' + input_file_identifier + '"', contents)
                    contents = re.sub('{{fov_index}}', str(fov_index), contents)
                    contents = re.sub('{{regional_compartment}}', rc, contents)
                    contents = re.sub('{{job_index}}', str(job_index), contents)
                    cli_call = contents

                    bsub_job = re.sub('{{cli_call}}', cli_call, bsub_job)

                    lsf_job_filename = join(self.jobs_paths.jobs_path, job_name + '.lsf')
                    with open(lsf_job_filename, 'w') as file:
                        file.write(bsub_job)

                    sh_job_filename = join(self.jobs_paths.jobs_path, job_name + '.sh')
                    with open(sh_job_filename, 'w') as file:
                        file.write(cli_call)

                    st = os.stat(sh_job_filename)
                    os.chmod(sh_job_filename, st.st_mode | stat.S_IEXEC)

                    self.submit_calls[rc].append('bsub < ' + lsf_job_filename)
                    self.local_run_calls[rc].append(sh_job_filename)

                self.number_arrays_of_jobs += 1

    def get_memory_requirements(self, file_record):
        """
        Args:
            file_record (dict-like):
                Record as it would appear in the file metadata table.

        Returns:
            int:
                The positive integer number of gigabytes to request for a job involving
                the given input file.
        """
        file_size_gb = float(file_record['Size']) / pow(10, 9)
        return 1 + math.ceil(file_size_gb * 10)

    def generate_scheduler_scripts(self):
        for rc in self.get_regional_compartments():
            if rc == 'nontumor':
                script_name = 'schedule_lsf_' + rc + '.sh'
                with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
                    num_rows = 0
                    for row in self.submit_calls[rc]:
                        schedule_script.write(row + '\n')
                        num_rows+=1
                logger.info('Wrote %s, which schedules %s jobs.', script_name, str(num_rows))

                script_name = 'schedule_local_' + rc + '.sh'
                with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
                    num_rows = 0
                    for row in self.local_run_calls[rc]:
                        schedule_script.write(row + '\n')
                        num_rows+=1
                logger.info('Wrote %s, which schedules %s jobs locally.', script_name, str(num_rows))


def cut_by_header(input_filename, delimiter=',', column: str=None):
    """
    This function attempts to emulate the speed and function of the UNIX-style
    ``cut`` command for a single field. The implementation here uses Pandas to read
    the whole table into memory; a future implementation may avert this.

    Args:
        input_filename (str):
            Input CSV-style file.
        delimiter (str):
            Delimiter character.
        column (str):
            The header value for the column you want returned.

    Returns:
        values (list):
            The single column of values.
    """
    if not column:
        logger.error('"column" is a mandatory argument.')
        raise ValueError
    df = pd.read_csv(input_filename, delimiter=delimiter)
    return list(df[column])
