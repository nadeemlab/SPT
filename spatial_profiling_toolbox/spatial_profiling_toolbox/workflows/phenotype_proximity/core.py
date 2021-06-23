import os
from os.path import join
import math
from math import exp, log, pow
import itertools
from itertools import combinations

import pandas as pd
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.sparse import coo_matrix

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityCalculator:
    radius_pixels_lower_limit = 10
    radius_pixels_upper_limit = 100
    radius_number_increments = 4

    def __init__(
        self,
        input_filename: str=None,
        sample_identifier: str=None,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        dataset_design=None,
        computational_design=None,
        regional_areas_file: str=None,
    ):
        self.input_filename = input_filename
        self.sample_identifier = sample_identifier
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.dataset_design = dataset_design
        self.computational_design = computational_design
        self.areas = dataset_design.areas_provider(
            dataset_design=dataset_design,
            regional_areas_file=regional_areas_file,
        )

    def calculate_proximity(self):
        outcomes_dict = self.pull_in_outcome_data()
        cells = self.create_cell_tables()
        cell_pairs = self.create_cell_pairs_tables(cells)
        phenotype_indices, compartment_indices = self.precalculate_masks(cells)
        radius_limited_counts = self.do_aggregation_counting(
            cell_pairs,
            outcomes_dict,
            phenotype_indices,
            compartment_indices,
        )
        self.write_cell_pair_counts(radius_limited_counts)

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

    def create_cell_tables(self):
        """
        Create tables, one for each source file / field of view index pair, whose
        records correspond to individual cells, with schema

          - regional compartment
          - x value
          - y value
          - (elementary phenotype 1) (cellular site 1) intensity
          - (elementary phenotype 2) (cellular site 1) intensity
          - ...
          - (elementary phenotype 1) (cellular site 2) intensity
          - (elementary phenotype 2) (cellular site 2) intensity
          - ...
          - (general phenotype 1) membership
          - (general phenotype 2) membership
          - ...

        """
        cells = {}

        signatures = self.computational_design.get_all_phenotype_signatures()
        signatures_by_name = {self.dataset_design.munge_name(signature) : signature for signature in signatures}
        pheno_names = sorted(signatures_by_name.keys())

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

            # Create (x,y) values
            xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
            df['x value'] = 0.5 * (df[xmax] + df[xmin])
            df['y value'] = 0.5 * (df[ymax] + df[ymin])

            # Add general phenotype membership columns
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

    def create_cell_pairs_tables(self, cells):
        """
        Precalculates the distances between cell pairs lying in the same field of view.
        One table is created for each source file and field of view.
        The table schema is

          - cell 1 index
          - cell 2 index
          - distance in pixels
        """
        cell_pairs = {}
        logger.debug('Calculating cell pair distances.')
        logger.debug(
            'Logging: (number of cells in fov, number of cell pairs used, fraction of possible pairs)'
        )
        L = PhenotypeProximityCalculator.radius_pixels_upper_limit
        logger.debug('Only using pairs of pixel distance less than %s', L)
        K = len(cells)
        for i, ((filename, fov_index), df) in enumerate(cells.items()):
            distance_matrix = cdist(df[['x value', 'y value']], df[['x value', 'y value']])
            D = distance_matrix
            D[D > L] = 0
            cell_pairs[(filename, fov_index)] = D
            D_sparse = coo_matrix(D)
            N = int(len(D_sparse.data) / 2)
            M = df.shape[0]
            number_all_pairs = M * (M - 1) / 2
            logger.debug(
                'File,fov %s/%s: (%s, %s, %s%%)',
                i, K, M, N,
                int(100 * 100 * N / number_all_pairs) / 100,
            )
        logger.debug('Completed (field of view limited) cell pair distances calculation.')
        return cell_pairs

    def precalculate_masks(self, cells):
        signatures = self.computational_design.get_all_phenotype_signatures()
        phenotypes = [self.dataset_design.munge_name(signature) for signature in signatures]
        phenotype_indices = {
            (f, fov_index) : {
                p : df[p + ' membership'] for p in phenotypes
            } for (f, fov_index), df in cells.items()
        }
        # phenotype_indices = {
        #     (f, fov_index) : {
        #         p : sorted(list(df.index[df[p + ' membership']])) for p in phenotypes
        #     } for (f, fov_index), df in cells.items()
        # }

        compartments = self.dataset_design.get_compartments()
        compartment_indices = {
            (f, fov_index) : {
                c : (df['regional compartment'] == c) for c in compartments
            } for (f, fov_index), df in cells.items()
        }
        # compartment_indices = {
        #     (f, fov_index) : {
        #         c : sorted(list(df.index[df['regional compartment'] == c])) for c in compartments
        #     } for (f, fov_index), df in cells.items()
        # }
        return [phenotype_indices, compartment_indices]

    def do_aggregation_counting(self, cell_pairs, outcomes_dict, phenotype_indices, compartment_indices):
        """
        Calculates the number of cell pairs satisfying criteria

          - source file fixed
          - source/target compartment membership
          - source phenotype membership
          - target phenotype membership
          - radius limitation

        for a range of parameter values.

        Also calculates the number of cells satisfying criteria

          - source file fixed
          - compartment membership
          - general phenotype membership
          - field of view membership

        In the above, also calculates
          - (elementary phenotype 1) membership intensity average
          - (elementary phenotype 2) membership intensity average
          - ...

        the averages being over the cells meeting the criteria. Also calculates the
        number of cells over the total number of cells in the given field of view.
        """
        signatures = self.computational_design.get_all_phenotype_signatures()
        phenotypes = [self.dataset_design.munge_name(signature) for signature in signatures]
        combinations2 = list(combinations(phenotypes, 2))
        logger.debug('Creating radius-limited data sets for %s phenotype pairs.', len(combinations2))
        results = []
        for combination in combinations2:
            results_combo = self.do_aggregation_one_phenotype_pair(
                combination,
                cell_pairs,
                outcomes_dict,
                phenotype_indices,
                compartment_indices,
            )
            results.append(results_combo)
            logger.debug('Cell pairs of types %s aggregated.', combination)
        logger.debug('All %s combinations aggregated.', len(combinations2))
        columns = [
            'sample identifier',
            'outcome assignment',
            'source phenotype',
            'target phenotype',
            'compartment',
            'distance limit in pixels',
            'cell pair count per FOV',
        ]
        radius_limited_counts = pd.DataFrame(self.flatten_lists(results), columns=columns)
        logger.debug('Completed counting cell pairs in "%s" under radius constraint.', self.input_filename)
        return radius_limited_counts

    def do_aggregation_one_phenotype_pair(self, pair, cell_pairs, outcomes_dict, phenotype_indices, compartment_indices):
        """
        Now, normalized by compartment area.
        """
        source, target = sorted(list(pair))
        records = []
        sample_identifier = self.sample_identifier # Need to refactor the below to explicitly involve 1 source file
        for compartment in list(set(self.dataset_design.get_compartments())) + ['all']:
            for radius in self.get_radii_of_interest():
                count = 0
                area = 0
                for (source_filename, fov_index), distance_matrix in cell_pairs.items():
                    rows = phenotype_indices[(source_filename, fov_index)][source]
                    cols = phenotype_indices[(source_filename, fov_index)][target]
                    if compartment != 'all':
                        rows = rows & compartment_indices[(source_filename, fov_index)][compartment]
                        cols = cols & compartment_indices[(source_filename, fov_index)][compartment]
                    p2p_distance_matrix = distance_matrix[rows][:, cols]
                    additional = np.sum( (p2p_distance_matrix < radius) & (p2p_distance_matrix > 0) )
                    if np.isnan(additional):
                        continue
                    count += additional

                    fov = self.fov_lookup[fov_index]
                    if compartment == 'all':
                        area0 = self.areas.get_total_compartmental_area(fov=fov)
                    else:
                        area0 = self.areas.get_area(fov=fov, compartment=compartment)
                    if area0 is None:
                        logger.warning(
                            'Did not find area for "%s" compartment in field of view "%s". Skipping field of view "%s" in "%s".',
                            compartment,
                            fov_index,
                            fov_index,
                            sample_identifier,
                        )
                        continue
                    area += area0
                if area == 0:
                    logger.warning(
                        'Did not find ANY area for "%s" compartment in "%s".',
                        compartment,
                        sample_identifier,
                    )
                else:
                    records.append([sample_identifier, outcomes_dict[sample_identifier], source, target, compartment, radius, count / area])

        return records

    def write_cell_pair_counts(self, radius_limited_counts):
        keys_list = [column_name for column_name, dtype in self.computational_design.get_cell_pair_counts_table_header()]

        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            for i, row in radius_limited_counts.iterrows():
                values_list = [
                    '"' + row['sample identifier'] + '"',
                    '"' + row['outcome assignment'] + '"',
                    '"' + row['source phenotype'] + '"',
                    '"' + row['target phenotype'] + '"',
                    '"' + row['compartment'] + '"',
                    str(int(row['distance limit in pixels'])),
                    str(float(row['cell pair count per FOV'])),
                ]
                keys = '( ' + ' , '.join([k for k in keys_list]) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = 'INSERT INTO cell_pair_counts ' + keys + ' VALUES ' + values +  ' ;'
                try:
                    m.execute(cmd)
                except Exception as e:
                    logger.error('SQL query failed: %s', cmd)
                    print(e)

    def get_radii_of_interest(self):
        """
        Creates a scale-adjusted range of values between the stipulated lower and upper
        limits, with the stipulated number of increments.
        """
        r = PhenotypeProximityCalculator.radius_pixels_lower_limit
        R = PhenotypeProximityCalculator.radius_pixels_upper_limit
        N = PhenotypeProximityCalculator.radius_number_increments

        a = math.exp((math.log(R / r) / N))
        return [int(r * math.pow(a, i)) for i in range(N + 1)]

    def flatten_lists(self, the_lists):
        result = []
        for _list in the_lists:
            result += _list
        return result
