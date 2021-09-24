"""
Generation of the job scripts and job scheduling scripts for the proximity
workflow.
"""
import math
import re
import os
from os import chmod
from os.path import join
import stat
import sqlite3

from ...dataset_designs.multiplexed_imaging.halo_cell_metadata_design import HALOCellMetadataDesign
from ...environment.job_generator import JobGenerator
from ...environment.log_formats import colorized_logger
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityJobGenerator(JobGenerator):
    """
    The main class of the job generator.
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
 > {{log_filename}} 2>&1
'''
    cli_call_template = '''spt-cell-phenotype-proximity-analysis \
 --input-file-identifier "{{input_file_identifier}}" \
 --job-index {{job_index}} \
'''

    def __init__(self,
        dataset_design=None,
        computational_design: PhenotypeProximityDesign=None,
        **kwargs,
    ):
        """
        :param elementary_phenotypes_file: Tabular file listing phenotypes of
            consideration.
        :type elementary_phenotypes_file: str

        :param complex_phenotypes_file: Tabular file listing composite phenotypes to
            consider.
        :type complex_phenotypes_file: str

        :param balanced: Whether to use balanced or unbalanced treatment of phenotype
            pairs.
        :type balanced: bool
        """
        super(PhenotypeProximityJobGenerator, self).__init__(**kwargs)
        self.dataset_design = dataset_design
        self.computational_design = computational_design

        self.lsf_job_filenames = []
        self.sh_job_filenames = []

    def gather_input_info(self):
        pass

    def generate_all_jobs(self):
        self.initialize_intermediate_database()
        for _, row in self.file_metadata.iterrows():
            if row['Data type'] == HALOCellMetadataDesign.get_cell_manifest_descriptor():
                job_index = self.register_job_existence()
                job_name = 'cell_proximity_' + str(job_index)
                log_filename = join(self.jobs_paths.logs_path, job_name + '.out')
                memory = PhenotypeProximityJobGenerator.get_memory_requirements(row)

                bsub_job = JobGenerator.apply_replacements(
                    PhenotypeProximityJobGenerator.lsf_template,
                    {
                        '{{input_files_path}}' : self.dataset_settings.input_path,
                        '{{job_working_directory}}' : self.jobs_paths.job_working_directory,
                        '{{job_name}}': '"' + job_name + '"',
                        '{{log_filename}}': log_filename,
                        '{{excluded_hostname}}': self.excluded_hostname,
                        '{{sif_file}}' : self.runtime_settings.sif_file,
                        '{{memory_in_gb}}' : str(memory),
                    }
                )

                cli_call = JobGenerator.apply_replacements(
                    PhenotypeProximityJobGenerator.cli_call_template,
                    {
                        '{{input_file_identifier}}' : row['File ID'],
                        '{{job_index}}' : str(job_index),
                    }
                )

                bsub_job = re.sub('{{cli_call}}', cli_call, bsub_job)

                lsf_job_filename = join(self.jobs_paths.jobs_path, job_name + '.lsf')
                self.lsf_job_filenames.append(lsf_job_filename)
                with open(lsf_job_filename, 'w') as file:
                    file.write(bsub_job)

                sh_job_filename = join(self.jobs_paths.jobs_path, job_name + '.sh')
                self.sh_job_filenames.append(sh_job_filename)
                with open(sh_job_filename, 'w') as file:
                    file.write(''.join([
                        cli_call,
                        '\n ',
                        re.sub('{{log_filename}}', log_filename, '> {{log_filename}} 2>&1'),
                    ]))

                chmod(sh_job_filename, os.stat(sh_job_filename).st_mode | stat.S_IEXEC)

    @staticmethod
    def get_memory_requirements(file_record):
        """
        :param file_record: Record as it would appear in the file metadata table.
        :type file_record: dict

        :return: ``memory_in_gb``. The positive integer number of gigabytes to request
            for a job involving the given input file.
        :rtype: int
        """
        file_size_gb = float(file_record['Size']) / pow(10, 9)
        return 1 + math.ceil(file_size_gb * 10)

    def initialize_intermediate_database(self):
        """
        The phenotype proximity workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cell_pair_counts_header = self.computational_design.get_cell_pair_counts_table_header()

        connection = sqlite3.connect(
            join(
                self.jobs_paths.output_path,
                self.computational_design.get_database_uri(),
            )
        )
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS %s ;' % self.computational_design.get_cell_pair_counts_table_name())
        cmd = ' '.join([
            'CREATE TABLE',
            self.computational_design.get_cell_pair_counts_table_name(),
            '(',
            'id INTEGER PRIMARY KEY AUTOINCREMENT,',
            ' , '.join([
                column_name + ' ' + data_type_descriptor
                for column_name, data_type_descriptor in cell_pair_counts_header
            ]),
            ');',
        ])
        cursor.execute(cmd)
        cursor.close()
        connection.commit()
        connection.close()

    def generate_scheduler_scripts(self):
        script_name = 'schedule_lsf_cell_proximity.sh'
        with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
            for lsf_job_filename in self.lsf_job_filenames:
                schedule_script.write('bsub < ' + lsf_job_filename + '\n')

        script_name = 'schedule_local_cell_proximity.sh'
        with open(join(self.jobs_paths.schedulers_path, script_name), 'w') as schedule_script:
            for sh_job_filename in self.sh_job_filenames:
                schedule_script.write(sh_job_filename + '\n')
