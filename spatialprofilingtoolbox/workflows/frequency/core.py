"""
The core calculator deals with pulling in cell data from all input data files,
and pushing it into a pipeline-specific database.
"""
from os.path import join
import sqlite3

import pandas as pd

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrequencyCalculator:
    """
    The main class of the core calculator.
    """
    def __init__(
        self,
        sample_identifiers_by_file: dict=None,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        dataset_design=None,
        computational_design=None,
    ):
        """
        :param sample_identifers_by_file: Association of input data files to
            corresponding samples.
        :type sample_identifiers_by_file: dict

        :param jobs_paths: Convenience bundle of filesystem paths pertinent to a
            particular run at the job level.
        :type jobs_paths: JobsPaths

        :param dataset_settings: Convenience bundle of paths to input dataset files.
        :type dataset_settings: DatasetSettings

        :param dataset_design: Design object providing metadata about the *kind* of
            input data being provided.

        :param computational_design: Design object providing metadata specific to the
            frequency workflow.
        """
        self.sample_identifiers_by_file = sample_identifiers_by_file
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    def calculate_frequency(self):
        """
        Writes cell data to the database.

        Note that in the frequency analysis workflow, most calculation takes place in
        the "integration" phase.
        """
        outcomes_dict = self.pull_in_outcome_data(self.outcomes_file)
        logger.info('Pulled outcome data, %s assignments.', len(outcomes_dict))
        cells, fov_lookup = self.create_cell_table(outcomes_dict)
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

    @staticmethod
    def pull_in_outcome_data(outcomes_file):
        """
        :param outcomes_file: Name of file with outcomes data.
        :type outcomes_file: str

        :return outcomes: Dictionary whose keys are sample identifiers, and values are
            outcome labels.
        :rtype outcomes: dict
        """
        outcomes_table = pd.read_csv(outcomes_file, sep='\t')
        columns = outcomes_table.columns
        outcomes_dict = {
            row[columns[0]]: row[columns[1]] for i, row in outcomes_table.iterrows()
        }
        return outcomes_dict

    def get_phenotype_signatures_by_name(self):
        """
        Munges composite phenotype signature names from their markers.

        :return: `signatures_by_name`. Mapping from munged names to signature dicts.
        :rtype: dict
        """
        signatures = self.computational_design.get_all_phenotype_signatures()
        return {self.dataset_design.munge_name(signature) : signature for signature in signatures}

    def get_phenotype_names(self):
        """
        :return: `phenotype_names`. The munged names of composite phenotypes.
        :rtype: list
        """
        signatures_by_name = self.get_phenotype_signatures_by_name()
        pheno_names = sorted(signatures_by_name.keys())
        return pheno_names

    def create_cell_table(self, outcomes_dict):
        """
        :param outcomes_dict: Mapping from sample identifiers to outcome labels.
        :type outcomes_dict: dict

        :return:
            - `cells`. Table of cell data.
            - `fov_lookup`. FOV descriptor strings in terms of pairs (sample identifier,
              FOV index integer).
        :rtype: pandas.DataFrame, dict
        """
        pheno_names = self.get_phenotype_names()

        cell_groups = []
        fov_lookup = {}
        for filename, sample_identifier in self.sample_identifiers_by_file.items():
            table_file = pd.read_csv(filename)
            table_file = self.dataset_design.normalize_fov_descriptors(table_file)

            col = self.dataset_design.get_FOV_column()
            fovs = sorted(list(set(table_file[col])))
            for i, fov in enumerate(fovs):
                fov_lookup[(sample_identifier, i)] = fov
                table_file.loc[table_file[col] == fov, col] = i

            for _, table_fov in table_file.groupby(col):
                table = table_fov.copy()
                table = table.reset_index(drop=True)

                if 'compartment' in table.columns:
                    logger.error('Woops, name collision "compartment".')
                    break
                all_compartments = self.dataset_design.get_compartments()
                table['compartment'] = 'Not in ' + ';'.join(all_compartments)

                for compartment in self.dataset_design.get_compartments():
                    signature = self.dataset_design.get_compartmental_signature(table, compartment)
                    table.loc[signature, 'compartment'] = compartment

                signatures_by_name = self.get_phenotype_signatures_by_name()
                for name in pheno_names:
                    signature = signatures_by_name[name]
                    bools = self.dataset_design.get_pandas_signature(table, signature)
                    ints = [1 if value else 0 for value in bools]
                    table[name + ' membership'] = ints
                phenotype_membership_columns = [name + ' membership' for name in pheno_names]

                table['sample_identifier'] = sample_identifier
                table['outcome_assignment'] = outcomes_dict[sample_identifier]

                pertinent_columns = [
                    'sample_identifier',
                    self.dataset_design.get_FOV_column(),
                    'outcome_assignment',
                    'compartment',
                    self.dataset_design.get_cell_area_column(),
                ] + phenotype_membership_columns

                table = table[pertinent_columns]
                table.rename(columns = {
                    self.dataset_design.get_FOV_column() : 'fov_index',
                    self.dataset_design.get_cell_area_column() : 'cell_area',
                }, inplace=True)

                header1 = self.computational_design.get_cells_header_variable_portion(
                    style='readable',
                )
                header2 = self.computational_design.get_cells_header_variable_portion(
                    style='sql',
                )
                table.rename(columns = {
                    header1[i][0] : header2[i][0] for i in range(len(header1))
                }, inplace=True)

                cell_groups.append(table)
            logger.debug('%s cells parsed from file %s.', table_file.shape[0], filename)
        logger.debug('Completed cell table collation.')
        return pd.concat(cell_groups), fov_lookup

    def write_cell_table(self, cells):
        """
        Writes cell table to database.

        :param cells: Table of cell areas with sample ID, outcome, etc.
        :type cells: pandas.DataFrame
        """
        uri = join(self.output_path, self.computational_design.get_database_uri())
        connection = sqlite3.connect(uri)
        cells.reset_index(drop=True, inplace=True)
        cells.to_sql('cells', connection, if_exists='append', index_label='id')
        connection.commit()
        connection.close()

    def write_fov_lookup_table(self, fov_lookup):
        """
        Writes field of view descriptor string lookup table to database.

        :param fov_lookup: Mapping from pairs (sample identifier, FOV index integer) to
            FOV descriptor strings.
        :type fov_lookup: dict
        """
        keys_list = [
            column_name for column_name, dtype in self.computational_design.get_fov_lookup_header()
        ]
        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as manager:
            for (sample_identifier, fov_index), fov_string in fov_lookup.items():
                values_list = [
                    '"' + sample_identifier + '"',
                    str(fov_index),
                    '"' + fov_string + '"',
                ]
                keys = '( ' + ' , '.join(keys_list) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = 'INSERT INTO fov_lookup ' + keys + ' VALUES ' + values +  ' ;'
                try:
                    manager.execute(cmd)
                except sqlite3.OperationalError as exception:
                    logger.error('SQL query failed: %s', cmd)
                    print(exception)
