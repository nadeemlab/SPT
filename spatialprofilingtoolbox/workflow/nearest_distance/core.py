"""
The core/parallelizable functionality of the nearest distance to compartment
workflow.
"""
import sqlite3

import pandas as pd
from scipy.spatial import KDTree

from spatialprofilingtoolbox.workflow.nearest_distance.computational_design import \
    NearestDistanceDesign
from spatialprofilingtoolbox.workflow.common.sqlite_context_utility import \
    WaitingDatabaseContextManager
from spatialprofilingtoolbox.workflow.defaults.core import CoreJob
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceCoreJob(CoreJob):
    """
    Core/parellelizable functionality for the nearest distance to a compartment
    workflow.
    """
    computational_design: NearestDistanceDesign

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.calculate_density()

    def initialize_metrics_database(self):
        """
        The density workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cells_header = self.computational_design.get_cells_header(style='sql')
        connection, cursor = super().connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
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

        # Check if fov_lookup is still used
        fov_lookup_header = self.computational_design.get_fov_lookup_header()
        connection, cursor = super().connect_to_intermediate_database()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
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

    def calculate_density(self):
        """
        Writes cell data to the database.

        Note that in the density analysis workflow, much calculation takes place in
        the "integration" phase.
        """
        self.timer.record_timepoint('Starting calculation of density')
        cells, fov_lookup = self.create_cell_table()
        logger.info('Aggregated %s cells into table.', cells.shape[0])
        self.write_cell_table(cells)
        self.write_fov_lookup_table(fov_lookup)
        logger.info('Finished writing cells and fov lookup helper.')

    def add_nearest_cell_data(self, table, compartment):
        compartments = self.dataset_design.get_compartments()
        cell_indices = list(table.index)
        xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
        table['x value'] = 0.5 * (table[xmax] + table[xmin])
        table['y value'] = 0.5 * (table[ymax] + table[ymin])
        signature = self.dataset_design.get_compartmental_signature(
            table, compartment)
        if sum(signature) == 0:
            for i, cell_index in enumerate(cell_indices):
                table.loc[cell_index, 'distance to nearest cell ' +
                          compartment] = -1
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
            distances, _ = tree.query(all_points)
            for i, cell_index in enumerate(cell_indices):
                compartment_i = table.loc[cell_index, 'compartment']
                if compartment_i == compartment:
                    distance = 0
                elif compartment_i not in compartments:
                    distance = -1
                else:
                    distance = distances[i]
                table.loc[cell_index, 'distance to nearest cell ' +
                          compartment] = distance

    def create_cell_table(self):
        """
        :return:
            - `cells`. Table of cell data.
            - `fov_lookup`. FOV descriptor strings in terms of pairs (sample identifier,
              FOV index integer).
        :rtype: pandas.DataFrame, dict
        """
        cell_groups = []
        fov_lookup = {}
        # for filename, sample_identifier in self.sample_identifiers_by_file.items():
        filename = self.input_filename
        sample_identifier = self.sample_identifier
        self.timer.record_timepoint('Start reading table')
        table_file = self.get_table(filename)
        self.timer.record_timepoint('Finished reading table')
        self.dataset_design.normalize_fov_descriptors(table_file)
        self.timer.record_timepoint(
            'Finished normalizing FOV strings in place')

        col = self.dataset_design.get_fov_column()
        fovs = sorted(list(set(table_file[col])))
        for i, fov in enumerate(fovs):
            fov_lookup[(sample_identifier, i)] = fov
            table_file.loc[table_file[col] == fov, col] = i
        self.timer.record_timepoint('Finished converting FOVs to integers')

        for _, table_fov in table_file.groupby(col):
            self.timer.record_timepoint('Start per-FOV cell table parsing')
            table = table_fov.copy()
            self.timer.record_timepoint('Finished copying FOV cells table')
            table = table.reset_index(drop=True)
            self.timer.record_timepoint('Finished resetting cells table index')

            self.deal_with_compartments(table)
            phenotype_membership_columns = self.add_and_return_membership_columns(table)

            self.timer.record_timepoint('Adding distance-to-nearest data')
            for compartment in self.dataset_design.get_compartments():
                self.add_nearest_cell_data(table, compartment)
            nearest_cell_columns = [
                'distance to nearest cell ' + compartment
                for compartment in self.dataset_design.get_compartments()]
            self.timer.record_timepoint(
                'Finished adding distance-to-nearest data')

            table['sample_identifier'] = sample_identifier
            table['outcome_assignment'] = self.outcome

            table = self.restrict_to_pertinent_columns(table, phenotype_membership_columns,
                                                       nearest_cell_columns)

            cell_groups.append(table)
            self.timer.record_timepoint('Finished parsing one FOV cell table for proximity calc.')
        logger.debug('%s cells parsed from file %s.', table_file.shape[0], filename)
        logger.debug('Completed cell table collation.')
        return pd.concat(cell_groups), fov_lookup

    def write_cell_table(self, cells):
        """
        Writes cell table to database.

        :param cells: Table of cell areas with sample ID, outcome, etc.
        :type cells: pandas.DataFrame
        """
        self.timer.record_timepoint('Writing parsed cells to file')
        uri = self.computational_design.get_database_uri()
        connection = sqlite3.connect(uri)
        cells.reset_index(drop=True, inplace=True)
        cells_columns = cells.columns
        schema_columns = self.computational_design.get_cells_header(
            style='sql')
        if all(cells_columns[i] == schema_columns[i][0] for i in range(len(cells_columns))):
            logger.debug(
                'Cells table to be written has correct (normalized, ordered) sql-style header '
                'values.')
        else:
            logger.debug(
                'Cells table to be written has INCORRECT sql-style header values.')
            if set(cells_columns) == set(schema_columns):
                logger.debug(
                    'At least the sets are the same, only the order is wrong.')
            logger.error('Cannot write cell table with wrong headers.')
        cells.to_sql('cells', connection, if_exists='append', index_label='id')
        connection.commit()
        connection.close()
        self.timer.record_timepoint('Done writing parsed cells to file')

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
                cmd = 'INSERT INTO fov_lookup ' + keys + ' VALUES ' + values + ' ;'
                try:
                    manager.execute(cmd)
                except sqlite3.OperationalError as exception:
                    logger.error('SQL query failed: %s', cmd)
                    print(exception)
        self.timer.record_timepoint('Done writing FOV lookup')
