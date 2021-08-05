import os
from os.path import join
import sqlite3

import pandas as pd

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrequencyCalculator:
    def __init__(
        self,
        sample_identifiers_by_file: dict=None,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        dataset_design=None,
        computational_design=None,
    ):
        self.sample_identifiers_by_file = sample_identifiers_by_file
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    def calculate_frequency(self):
        outcomes_dict = self.pull_in_outcome_data(self.outcomes_file)
        logger.info('Pulled outcome data, %s assignments.', len(outcomes_dict))
        cells, fov_lookup = self.create_cell_table(outcomes_dict)
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

    def pull_in_outcome_data(self, outcomes_file):
        """
        :param outcomes_file: Name of file with outcomes data.
        :type outcomes_file: str

        :return outcomes: Dictionary whose keys are sample identifiers, and values are
            outcome labels.
        :rtype outcomes: dict
        """
        outcomes_df = pd.read_csv(outcomes_file, sep='\t')
        columns = outcomes_df.columns
        outcomes_dict = {
            row[columns[0]]: row[columns[1]] for i, row in outcomes_df.iterrows()
        }
        return outcomes_dict

    def get_phenotype_signatures_by_name(self):
        signatures = self.computational_design.get_all_phenotype_signatures()
        return {self.dataset_design.munge_name(signature) : signature for signature in signatures}

    def get_phenotype_names(self):
        signatures_by_name = self.get_phenotype_signatures_by_name()
        pheno_names = sorted(signatures_by_name.keys())
        return pheno_names

    def create_cell_table(self, outcomes_dict):
        pheno_names = self.get_phenotype_names()

        cell_groups = []
        fov_lookup = {}
        for filename, sample_identifier in self.sample_identifiers_by_file.items():
            df_file = pd.read_csv(filename)
            df_file = self.dataset_design.normalize_fov_descriptors(df_file)

            col = self.dataset_design.get_FOV_column()
            fovs = sorted(list(set(df_file[col])))
            for i, fov in enumerate(fovs):
                fov_lookup[(sample_identifier, i)] = fov
                df_file.loc[df_file[col] == fov, col] = i

            for fov_index, df_fov in df_file.groupby(col):
                df = df_fov.copy()
                df = df.reset_index(drop=True)

                if 'compartment' in df.columns:
                    logger.error('Woops, name collision "compartment".')
                    break
                all_compartments = self.dataset_design.get_compartments()
                df['compartment'] = 'Not in ' + ';'.join(all_compartments)

                for compartment in self.dataset_design.get_compartments():
                    signature = self.dataset_design.get_compartmental_signature(df, compartment)
                    df.loc[signature, 'compartment'] = compartment

                signatures_by_name = self.get_phenotype_signatures_by_name()
                for name in pheno_names:
                    signature = signatures_by_name[name]
                    bools = self.dataset_design.get_pandas_signature(df, signature)
                    ints = [1 if value else 0 for value in bools]
                    df[name + ' membership'] = ints
                phenotype_membership_columns = [name + ' membership' for name in pheno_names]

                df['sample_identifier'] = sample_identifier
                df['outcome_assignment'] = outcomes_dict[sample_identifier]

                pertinent_columns = [
                    'sample_identifier',
                    self.dataset_design.get_FOV_column(),
                    'outcome_assignment',
                    'compartment',
                    self.dataset_design.get_cell_area_column(),
                ] + phenotype_membership_columns

                df = df[pertinent_columns]
                df.rename(columns = {
                    self.dataset_design.get_FOV_column() : 'fov_index',
                    self.dataset_design.get_cell_area_column() : 'cell_area',
                }, inplace=True)

                h1 = self.computational_design.get_cells_header_variable_portion(style='readable')
                h2 = self.computational_design.get_cells_header_variable_portion(style='sql')
                df.rename(columns = {
                    h1[i][0] : h2[i][0] for i in range(len(h1))
                }, inplace=True)

                cell_groups.append(df)
            logger.debug('%s cells parsed from file %s.', df_file.shape[0], filename)
        logger.debug('Completed cell table collation.')
        return pd.concat(cell_groups), fov_lookup

    def write_cell_table(self, cells):
        header = self.computational_design.get_cells_header(style='sql')
        keys_list = [column_name for column_name, dtype in header]
        uri = join(self.output_path, self.computational_design.get_database_uri())
        connection = sqlite3.connect(uri)
        chunksize = int(999 / len(header)) - 1
        logger.info('Writing to cells table, using chunk size %s.', chunksize)
        cells.to_sql('cells', connection, if_exists='replace', method='multi', chunksize=chunksize)
        connection.commit()
        connection.close()

    def write_fov_lookup_table(self, fov_lookup):
        keys_list = [column_name for column_name, dtype in self.computational_design.get_fov_lookup_header()]
        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            for (sample_identifier, fov_index), fov_string in fov_lookup.items():
                values_list = [
                    '"' + sample_identifier + '"',
                    str(fov_index),
                    '"' + fov_string + '"',
                ]
                keys = '( ' + ' , '.join([k for k in keys_list]) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = 'INSERT INTO fov_lookup ' + keys + ' VALUES ' + values +  ' ;'
                try:
                    m.execute(cmd)
                except Exception as e:
                    logger.error('SQL query failed: %s', cmd)
                    print(e)

