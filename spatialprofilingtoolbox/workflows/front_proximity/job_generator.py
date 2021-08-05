import math
import re
import os
from os.path import join, exists, abspath
import stat
import sqlite3

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ...environment.job_generator import JobGenerator, JobActivity
from ...environment.log_formats import colorized_logger
from .computational_design import FrontProximityDesign

logger = colorized_logger(__name__)


class FrontProximityJobGenerator(JobGenerator):
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
 > {{log_filename}} 2>&1
'''
    cli_call_template = '''spt-front-proximity-analysis \
 --input-file-identifier "{{input_file_identifier}}" \
 --job-index {{job_index}} \
'''

    def __init__(self,
        elementary_phenotypes_file=None,
        complex_phenotypes_file=None,
        **kwargs,
    ):
        """
        Args:

            elementary_phenotypes_file (str):
                Tabular file listing phenotypes of consideration. See dataset designs.

            complex_phenotypes_file (str):
                Tabular file listing composite phenotypes to consider. See
                ``phenotype_proximity.computational_design``.
        """
        super(FrontProximityJobGenerator, self).__init__(**kwargs)
        self.dataset_design = HALOCellMetadataDesign(
            elementary_phenotypes_file,
        )
        self.computational_design = FrontProximityDesign(
            dataset_design=self.dataset_design,
            complex_phenotypes_file=complex_phenotypes_file,
        )

        self.lsf_job_filenames = []
        self.sh_job_filenames = []

    def gather_input_info(self):
        pass

    def generate_all_jobs(self):
        self.initialize_intermediate_database()
        job_working_directory = self.jobs_paths.job_working_directory

        for i, row in self.file_metadata.iterrows():
            if row['Data type'] == HALOCellMetadataDesign.get_cell_manifest_descriptor():
                file_id = row['File ID']

                job_index = self.register_job_existence()
                job_name = 'cell_proximity_' + str(job_index)
                log_filename = join(self.jobs_paths.logs_path, job_name + '.out')
                memory_in_gb = self.get_memory_requirements(row)

                contents = FrontProximityJobGenerator.lsf_template
                contents = re.sub('{{input_files_path}}', self.dataset_settings.input_path, contents)
                contents = re.sub('{{job_working_directory}}', job_working_directory, contents)
                contents = re.sub('{{job_name}}', '"' + job_name + '"', contents)
                contents = re.sub('{{log_filename}}', log_filename, contents)
                contents = re.sub('{{excluded_hostname}}', self.excluded_hostname, contents)
                contents = re.sub('{{sif_file}}', self.runtime_settings.sif_file, contents)
                contents = re.sub('{{memory_in_gb}}', str(memory_in_gb), contents)
                bsub_job = contents

                contents = FrontProximityJobGenerator.cli_call_template
                contents = re.sub('{{input_file_identifier}}', file_id, contents)
                contents = re.sub('{{job_index}}', str(job_index), contents)
                cli_call = contents

                bsub_job = re.sub('{{cli_call}}', cli_call, bsub_job)

                lsf_job_filename = join(self.jobs_paths.jobs_path, job_name + '.lsf')
                self.lsf_job_filenames.append(lsf_job_filename)
                with open(lsf_job_filename, 'w') as file:
                    file.write(bsub_job)

                sh_job_filename = join(self.jobs_paths.jobs_path, job_name + '.sh')
                self.sh_job_filenames.append(sh_job_filename)
                with open(sh_job_filename, 'w') as file:
                    file.write(cli_call)

                st = os.stat(sh_job_filename)
                os.chmod(sh_job_filename, st.st_mode | stat.S_IEXEC)

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

    def initialize_intermediate_database(self):
        """
        The front proximity workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cell_front_distances_header = self.computational_design.get_cell_front_distances_header()

        connection = sqlite3.connect(join(self.jobs_paths.output_path, self.computational_design.get_database_uri()))
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS cell_front_distances ;')
        cmd = ' '.join([
            'CREATE TABLE',
            'cell_front_distances',
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ' , '.join([
                column_name + ' ' + data_type_descriptor for column_name, data_type_descriptor in cell_front_distances_header
            ]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def generate_scheduler_scripts(self):
        script_name = 'schedule_lsf_front_proximity.sh'
        with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
            for lsf_job_filename in self.lsf_job_filenames:
                schedule_script.write('bsub < ' + lsf_job_filename + '\n')

        script_name = 'schedule_local_front_proximity.sh'
        with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
            for sh_job_filename in self.sh_job_filenames:
                schedule_script.write(sh_job_filename + '\n')
