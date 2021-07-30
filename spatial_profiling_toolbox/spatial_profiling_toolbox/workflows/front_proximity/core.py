import os
from os.path import join

import pandas as pd
import scipy
from scipy.spatial import KDTree

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class FrontProximityCalculator:
    def __init__(
        self,
        input_filename: str=None,
        sample_identifier: str=None,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        dataset_design=None,
        computational_design=None,
    ):
        self.input_filename = input_filename
        self.sample_identifier = sample_identifier
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.dataset_design = dataset_design
        self.computational_design = computational_design

    def calculate_front_proximity(self):
        outcomes_dict = self.pull_in_outcome_data()
        outcome = outcomes_dict[self.sample_identifier]
        cells = self.create_cell_tables()
        distance_records = self.calculate_front_distance_records(cells, outcome)
        self.write_cell_front_distance_records(distance_records)
        logger.debug('Finished writing cell front distances in sample %s.', self.sample_identifier)

    def pull_in_outcome_data(self):
        """
        Parses outcome assignments from file.
        Saves to outcomes_dict.
        """
        outcomes_df = pd.read_csv(self.outcomes_file, sep='\t')
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

    def create_cell_tables(self):
        pheno_names = self.get_phenotype_names()

        number_fovs = 0
        filename = self.input_filename
        df_file = pd.read_csv(filename)

        # Normalize FOV strings
        df_file = self.dataset_design.normalize_fov_descriptors(df_file)

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
                number_cells_by_phenotype[phenotype] = n + sum(df[name + ' membership'])
        most_frequent = sorted(
            [(k, v) for k, v in number_cells_by_phenotype.items()],
            key=lambda x: x[1],
            reverse=True
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
                    logger.debug('Fewer then 3 points in %s compartment in %s, %s',
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

        uri = join(self.output_path, self.computational_design.get_database_uri())
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
                    print(e)
