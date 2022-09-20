from os.path import join
import sqlite3

import pandas as pd
import scipy
from scipy.spatial import KDTree

from ...common.sqlite_context_utility import WaitingDatabaseContextManager
from ..defaults.core import CoreJob
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class NearestDistanceCoreJob(CoreJob):
    def __init__(self, **kwargs):
        super(NearestDistanceCoreJob, self).__init__(**kwargs)

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
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
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
        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
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
                elif compartment_i not in compartments:
                    distance = -1
                else:
                    distance = distances[i]
                table.loc[I, 'distance to nearest cell ' + compartment] = distance

    def create_cell_table(self):
        """
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
        self.timer.record_timepoint('Start reading table')
        table_file = self.get_table(filename)
        self.timer.record_timepoint('Finished reading table')
        self.dataset_design.normalize_fov_descriptors(table_file)
        self.timer.record_timepoint('Finished normalizing FOV strings in place')

        col = self.dataset_design.get_FOV_column()
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
            self.timer.record_timepoint('Finished reseting cells table index')
            if 'compartment' in table.columns:
                logger.error('Woops, name collision "compartment".')
                break
            all_compartments = self.dataset_design.get_compartments()
            table['compartment'] = 'Not in ' + ';'.join(all_compartments)

            for compartment in self.dataset_design.get_compartments():
                signature = self.dataset_design.get_compartmental_signature(table, compartment)
                table.loc[signature, 'compartment'] = compartment
            self.timer.record_timepoint('Copy compartment column')

            signatures_by_name = self.get_phenotype_signatures_by_name()
            self.timer.record_timepoint('Start creating membership column')
            for name in pheno_names:
                signature = signatures_by_name[name]
                bools = self.dataset_design.get_pandas_signature(table, signature)
                ints = [1 if value else 0 for value in bools]
                table[name + ' membership'] = ints
            phenotype_membership_columns = [name + ' membership' for name in pheno_names]
            self.timer.record_timepoint('Finished creating membership columns')

            self.timer.record_timepoint('Adding distance-to-nearest data')
            for compartment in all_compartments:
                self.add_nearest_cell_data(table, compartment)
            nearest_cell_columns = ['distance to nearest cell ' + compartment for compartment in all_compartments]
            self.timer.record_timepoint('Finished adding distance-to-nearest data')
            table['sample_identifier'] = sample_identifier
            table['outcome_assignment'] = self.outcome

            pertinent_columns = [
                'sample_identifier',
                self.dataset_design.get_FOV_column(),
                'outcome_assignment',
                'compartment',
                self.dataset_design.get_cell_area_column(),
            ] + phenotype_membership_columns + nearest_cell_columns

            table = table[pertinent_columns]
            self.timer.record_timepoint('Restricted copy to subset of columns')
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
            self.timer.record_timepoint('Finished parsing one FOV cell table')
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
                cmd = 'INSERT INTO fov_lookup ' + keys + ' VALUES ' + values +  ' ;'
                try:
                    manager.execute(cmd)
                except sqlite3.OperationalError as exception:
                    logger.error('SQL query failed: %s', cmd)
                    print(exception)
        self.timer.record_timepoint('Done writing FOV lookup')
