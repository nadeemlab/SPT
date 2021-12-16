"""
The core calculator deals with pulling in cell data from all input data files,
and pushing it into a pipeline-specific database.
"""
from os.path import join
import sqlite3

import pandas as pd
import scipy
from scipy.spatial import KDTree

from ...environment.file_io import get_outcomes_files
from ...environment.settings_wrappers import DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.calculator import Calculator
from ...environment.log_formats import colorized_logger
from .data_logging import DensityDataLogger

logger = colorized_logger(__name__)


class DensityCalculator(Calculator):
    """
    The main class of the core calculator.
    """
    def __init__(
        self,
        input_filename: str=None,
        sample_identifier: str=None,
        dataset_settings: DatasetSettings=None,
        **kwargs,
    ):
        """
        :param input_filename: The filename for the source file with cell data.
        :type input_filename: str

        :param sample_identifier: The sample associated with this source file.
        :type sample_identifier: str

        :param dataset_settings: Convenience bundle of paths to input dataset files.
        :type dataset_settings: DatasetSettings
        """
        super(DensityCalculator, self).__init__(**kwargs)
        self.input_filename = input_filename
        self.sample_identifier = sample_identifier
        self.outcomes_file = get_outcomes_files(dataset_settings)[0]

    def calculate_density(self):
        """
        Writes cell data to the database.

        Note that in the density analysis workflow, most calculation takes place in
        the "integration" phase.
        """
        outcomes_dict = self.pull_in_outcome_data(self.outcomes_file)
        logger.info('Pulled outcome data, %s assignments.', len(outcomes_dict))
        cells, fov_lookup = self.create_cell_table(outcomes_dict)
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        DensityDataLogger.log_number_by_type(self.computational_design, cells)
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

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

    def add_nearest_cell_data(self, table, compartment):
        compartments = self.dataset_design.get_compartments()
        cell_indices = list(table.index)
        xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
        table['x value'] = 0.5 * (table[xmax] + table[xmin])
        table['y value'] = 0.5 * (table[ymax] + table[ymin])
        signature = self.dataset_design.get_compartmental_signature(table, compartment)
        if sum(signature) == 0:
            for i in range(len(cell_indices)):
                I = cell_indices[i]
                distance = -1
                table.loc[I, 'distance to nearest cell ' + compartment] = distance
        else:
            compartment_cells = table[signature]
            compartment_points = [
                (row['x value'], row['y value'])
                for i, row in compartment_cells.iterrows()
            ]
            all_points = [
                (row['x value'], row['y value'])
                for i, row in table.iterrows()
            ]
            tree = KDTree(compartment_points)
            distances, indices = tree.query(all_points)
            for i in range(len(cell_indices)):
                I = cell_indices[i]
                compartment_i = table.loc[I, 'compartment']
                if compartment_i == compartment:
                    distance = 0
                if compartment_i not in compartments:
                    distance = -1
                else:
                    distance = distances[i]
                table.loc[I, 'distance to nearest cell ' + compartment] = distance

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
        # for filename, sample_identifier in self.sample_identifiers_by_file.items():
        filename = self.input_filename
        sample_identifier = self.sample_identifier
        table_file = self.get_table(filename)
        self.dataset_design.normalize_fov_descriptors(table_file)

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

            for compartment in all_compartments:
                self.add_nearest_cell_data(table, compartment)
            nearest_cell_columns = ['distance to nearest cell ' + compartment for compartment in all_compartments]

            table['sample_identifier'] = sample_identifier
            table['outcome_assignment'] = outcomes_dict[sample_identifier]

            if self.computational_design.use_intensities:
                self.overlay_intensities(table)
            intensity_columns = self.computational_design.get_intensity_columns(values_only=True)

            pertinent_columns = [
                'sample_identifier',
                self.dataset_design.get_FOV_column(),
                'outcome_assignment',
                'compartment',
                self.dataset_design.get_cell_area_column(),
            ] + phenotype_membership_columns + intensity_columns + nearest_cell_columns

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

    def overlay_intensities(self, table):
        intensity_columns = self.computational_design.get_intensity_columns()
        for phenotype_name, column_name in intensity_columns:
            I = self.dataset_design.get_combined_intensity(table, phenotype_name)
            table[column_name] = I

    def write_cell_table(self, cells):
        """
        Writes cell table to database.

        :param cells: Table of cell areas with sample ID, outcome, etc.
        :type cells: pandas.DataFrame
        """
        uri = self.computational_design.get_database_uri()
        connection = sqlite3.connect(uri)
        cells.reset_index(drop=True, inplace=True)
        c = cells.columns
        schema_columns = self.computational_design.get_cells_header(style='sql')
        if all([c[i] == schema_columns[i][0] for i in range(len(c))]):
            logger.debug('Cells table to be written has correct (normalized, ordered) sql-style header values.')
        else:
            logger.debug('Cells table to be written has INCORRECT sql-style header values.')
            if set(c) == set(schema_columns):
                logger.debug('At least the sets are the same, only the order is wrong.')
            logger.error('Cannot write cell table with wrong headers.')
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
        uri = self.computational_design.get_database_uri()
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
