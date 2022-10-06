import os
from os.path import join
import sqlite3

import pandas as pd
import scipy
from scipy.spatial import KDTree

from ..defaults.core import CoreJob
from ...common.sqlite_context_utility import WaitingDatabaseContextManager
from ....standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityCoreJob(CoreJob):
    def __init__(self, **kwargs):
        super(FrontProximityCoreJob, self).__init__(**kwargs)

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.calculate_front_proximity()

    def initialize_metrics_database(self):
        """
        The front proximity workflow uses a pipeline-specific database to store its
        intermediate outputs. This method initializes this database's tables.
        """
        cell_front_distances_header = self.computational_design.get_cell_front_distances_header()

        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
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

    def calculate_front_proximity(self):
        self.timer.record_timepoint('Started front proximity one job')
        cells = self.create_cell_tables()
        self.timer.record_timepoint('Finished cell table creation')
        distance_records = self.calculate_front_distance_records(cells, self.outcome)
        self.timer.record_timepoint('Finished calculating front distance')
        self.write_cell_front_distance_records(distance_records)
        self.timer.record_timepoint('Finished writing front distance')
        logger.debug('Finished writing cell front distances in sample %s.', self.sample_identifier)
        self.timer.record_timepoint('Completed front proximity one job')

    def get_phenotype_signatures_by_name(self):
        signatures = self.computational_design.get_all_phenotype_signatures()
        return {self.dataset_design.munge_name(signature) : signature for signature in signatures}

    def get_phenotype_names(self):
        signatures_by_name = self.get_phenotype_signatures_by_name()
        pheno_names = sorted(signatures_by_name.keys())
        return pheno_names

    def create_cell_tables(self):
        pheno_names = self.get_phenotype_names()

        number_fovs = 0
        filename = self.input_filename
        df_file = self.get_table(filename)

        self.dataset_design.normalize_fov_descriptors(df_file)

        # Cache original (*normalized) FOV strings
        self.fov_lookup = {}
        col = self.dataset_design.get_FOV_column()
        fovs = sorted(list(set(df_file[col])))
        for i, fov in enumerate(fovs):
            self.fov_lookup[i] = fov

        # Replace original FOV string descriptor with index
        col = self.dataset_design.get_FOV_column()
        fovs = sorted(list(set(df_file[col])))
        for i, fov in enumerate(fovs):
            df_file.loc[df_file[col] == fov, col] = i
        number_fovs += len(fovs)

        number_cells_by_phenotype = {phenotype : 0 for phenotype in pheno_names}
        cells = {}
        for fov_index, df_fov in df_file.groupby(col):
            df = df_fov.copy()
            df = df.reset_index(drop=True)

            # Create compartment assignment stipulated by design
            if 'regional compartment' in df.columns:
                logger.error('Woops, name collision in "regional compartment". Trying to create new column.')
                break
            df['regional compartment'] = 'Not in ' + ';'.join(self.dataset_design.get_compartments())

            for compartment in self.dataset_design.get_compartments():
                signature = self.dataset_design.get_compartmental_signature(df, compartment)
                df.loc[signature, 'regional compartment'] = compartment

            xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
            df['x value'] = 0.5 * (df[xmax] + df[xmin])
            df['y value'] = 0.5 * (df[ymax] + df[ymin])

            # Add general phenotype membership columns
            signatures_by_name = self.get_phenotype_signatures_by_name()
            for name in pheno_names:
                signature = signatures_by_name[name]
                df[name + ' membership'] = self.dataset_design.get_pandas_signature(df, signature)
            phenotype_membership_columns = [name + ' membership' for name in pheno_names]

            # Select pertinent columns and rename
            intensity_column_names = self.dataset_design.get_intensity_column_names()
            if any([not c in df.columns for c in intensity_column_names.values()]):
                intensity_column_names = self.dataset_design.get_intensity_column_names(with_sites=False)

            inverse = {value:key for key, value in intensity_column_names.items()}
            source_columns = list(intensity_column_names.values())
            pertinent_columns = [
                'regional compartment',
                'x value',
                'y value',
            ] + source_columns + phenotype_membership_columns

            # Omit data not used in this pipeline
            df = df[pertinent_columns]

            # Convert column names into normal form as stipulated by this module
            df.rename(columns = inverse, inplace=True)
            df.rename(columns = {self.dataset_design.get_FOV_column() : 'field of view index'}, inplace=True)
            cells[(filename, fov_index)] = df

            for phenotype in pheno_names:
                n = number_cells_by_phenotype[phenotype]
                number_cells_by_phenotype[phenotype] = n + sum(df[phenotype + ' membership'])
        most_frequent = sorted(
            [(k, v) for k, v in number_cells_by_phenotype.items()],
            key=lambda x: x[1],
            reverse=True,
        )[0]
        logger.debug(
            '%s cells parsed from file. Most frequent signature %s (%s)',
            df_file.shape[0],
            most_frequent[0],
            most_frequent[1],
        )
        logger.debug('Completed cell table collation.')
        return cells

    def calculate_front_distance_records(self, cells, outcome):
        distance_records = []
        for (filename, fov_index), df in cells.items():
            cell_indices = list(df.index)
            x_values = list(df['x value'])
            y_values = list(df['y value'])
            compartment_assignments = list(df['regional compartment'])
            all_points = [(x_values[i], y_values[i]) for i in range(len(cell_indices))]
            for compartment in self.dataset_design.get_compartments():
                compartment_points = [(x_values[i], y_values[i]) for i in range(len(cell_indices)) if compartment_assignments[i] == compartment]
                if len(compartment_points) < 3:
                    logger.debug('Fewer than 3 points in %s compartment in %s, %s',
                        compartment,
                        self.sample_identifier,
                        fov_index,
                    )
                    continue
                tree = KDTree(compartment_points)
                distances, indices = tree.query(all_points)
                for i in range(len(cell_indices)):
                    compartment_i = compartment_assignments[i]
                    if compartment_i == compartment:
                        continue
                    I = cell_indices[i]
                    for phenotype in self.get_phenotype_names():
                        if df.loc[I, phenotype + ' membership']:
                            distance_records.append([
                                self.sample_identifier,
                                int(fov_index),
                                str(outcome),
                                str(phenotype),
                                str(compartment_i),
                                str(compartment),
                                float(distances[i]),
                            ])
        return distance_records

    def write_cell_front_distance_records(self, distance_records):
        keys_list = [column_name for column_name, dtype in self.computational_design.get_cell_front_distances_header()]

        uri = self.computational_design.get_database_uri()
        with WaitingDatabaseContextManager(uri) as m:
            for row in distance_records:
                values_list = [
                    '"' + row[0] + '"',
                    str(row[1]),
                    '"' + row[2] + '"',
                    '"' + row[3] + '"',
                    '"' + row[4] + '"',
                    '"' + row[5] + '"',
                    str(float(row[6])),
                ]
                keys = '( ' + ' , '.join([k for k in keys_list]) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = 'INSERT INTO cell_front_distances ' + keys + ' VALUES ' + values +  ' ;'
                try:
                    m.execute(cmd)
                except Exception as e:
                    logger.error('SQL query failed: %s', cmd)
                    raise e
