"""
The generator of the job scripts and job scheduling scripts for the cell
phenotype frequency analysis workflow.
"""
from math import ceil
import re
import os
from os import chmod
from os.path import join
import stat
import sqlite3

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ...environment.job_generator import JobGenerator
from ...environment.log_formats import colorized_logger
from .computational_design import FrequencyDesign

logger = colorized_logger(__name__)


class FrequencyJobGenerator(JobGenerator):
    """
    The main class of the job generation.
    """
    lsf_template = '''#!/bin/bash
#BSUB -J {{job_name}}
#BSUB -n "1"
#BSUB -W 2:00
#BSUB -R "rusage[mem={{memory_in_gb}}]"
#BSUB -R "span[hosts=1]"
#BSUB -R "select[hname!={{excluded_hostname}}]"
cd {{job_working_directory}}
export DEBUG=1
singularity exec \
 --bind {{input_files_path}}:{{input_files_path}}\
 {{sif_file}} \
 {{cli_call}} \
 &> {{log_filename}} 
'''
    cli_call_template = '''spt-frequency-analysis \
'''

    def __init__(self,
        elementary_phenotypes_file=None,
        complex_phenotypes_file=None,
        skip_integrity_check=False,
        **kwargs,
    ):
        """
        :param elementary_phenotypes_file: Tabular file listing phenotypes of
            consideration. See :py:mod:`spatialprofilingtoolbox.dataset_designs`.
        :type elementary_phenotypes_file: str

        :param complex_phenotypes_file: Tabular file listing composite phenotypes to
            consider. See :py:mod:`spatialprofilingtoolbox.dataset_designs`.
        :type complex_phenotypes_file: str
        """
        super().__init__(**kwargs)
        self.dataset_design = HALOCellMetadataDesign(
            elementary_phenotypes_file,
        )
        self.computational_design = FrequencyDesign(
            dataset_design=self.dataset_design,
            complex_phenotypes_file=complex_phenotypes_file,
        )

        self.lsf_job_filenames = []
        self.sh_job_filenames = []

    def gather_input_info(self):
        pass

    def generate_all_jobs(self):
        all_memory_requirements = []
        for _, row in self.file_metadata.iterrows():
            if row['Data type'] == HALOCellMetadataDesign.get_cell_manifest_descriptor():
                all_memory_requirements.append(self.get_memory_requirements(row))

        job_index = self.register_job_existence()
        job_name = 'frequency_' + str(job_index)
        log_filename = join(self.jobs_paths.logs_path, job_name + '.out')

        contents = FrequencyJobGenerator.lsf_template
        contents = re.sub(
            '{{input_files_path}}',
            self.dataset_settings.input_path,
            contents,
        )
        contents = re.sub(
            '{{job_working_directory}}',
            self.jobs_paths.job_working_directory,
            contents,
        )
        contents = re.sub('{{job_name}}', '"' + job_name + '"', contents)
        contents = re.sub('{{log_filename}}', log_filename, contents)
        contents = re.sub('{{excluded_hostname}}', self.excluded_hostname, contents)
        contents = re.sub('{{sif_file}}', self.runtime_settings.sif_file, contents)
        contents = re.sub('{{memory_in_gb}}', str(max(all_memory_requirements)), contents)
        bsub_job = contents

        cli_call = FrequencyJobGenerator.cli_call_template
        bsub_job = re.sub('{{cli_call}}', cli_call, bsub_job)

        lsf_job_filename = join(self.jobs_paths.jobs_path, job_name + '.lsf')
        self.lsf_job_filenames.append(lsf_job_filename)
        with open(lsf_job_filename, 'w') as file:
            file.write(bsub_job)

        sh_command = ' '.join([
            cli_call,
            re.sub('{{log_filename}}', log_filename, ' &> {{log_filename}}\n')
        ])
        sh_job_filename = join(self.jobs_paths.jobs_path, job_name + '.sh')
        self.sh_job_filenames.append(sh_job_filename)
        with open(sh_job_filename, 'w') as file:
            file.write(sh_command)

        chmod(sh_job_filename, os.stat(sh_job_filename).st_mode | stat.S_IEXEC)

        self.initialize_intermediate_database()

    @staticmethod
    def get_memory_requirements(file_record):
        """
        :param file_record: Record as it would appear in the file metadata table.
        :type file_record: dict-like

        :return: The positive integer number of gigabytes to request for a job involving
            the given input file.
        :rtype: int
        """
        file_size_gb = float(file_record['Size']) / pow(10, 9)
        return 1 + ceil(file_size_gb * 10)

    def generate_scheduler_scripts(self):
        deployment_platform = self.runtime_settings.runtime_platform
        if deployment_platform == 'lsf':
            script_name = 'schedule_lsf_frequency.sh'
            with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
                for lsf_job_filename in self.lsf_job_filenames:
                    schedule_script.write('bsub < ' + lsf_job_filename + '\n')

        if deployment_platform == 'local':
            script_name = 'schedule_local_frequency.sh'
            with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
                for sh_job_filename in self.sh_job_filenames:
                    schedule_script.write(sh_job_filename + '\n')

    def initialize_intermediate_database(self):
        """
        The frequency workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cells_header = self.computational_design.get_cells_header(style='sql')
        connection = sqlite3.connect(
            join(self.jobs_paths.output_path, self.computational_design.get_database_uri())
        )
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS cells ;')
        cmd = ' '.join([
            'CREATE TABLE',
            'cells',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in cells_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

        fov_lookup_header = self.computational_design.get_fov_lookup_header()
        connection = sqlite3.connect(
            join(self.jobs_paths.output_path, self.computational_design.get_database_uri())
        )
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS fov_lookup ;')
        cmd = ' '.join([
            'CREATE TABLE',
            'fov_lookup',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ', '.join([' '.join(entry) for entry in fov_lookup_header]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()
