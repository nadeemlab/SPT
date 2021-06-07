import os
from os.path import dirname, join, basename, abspath
import functools
from functools import lru_cache
import re
import math 
import itertools
import sqlite3
import hashlib

import pandas as pd
import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.sparse import coo_matrix

from ...dataset_designs.multiplexed_immunofluorescence.design import HALOCellMetadataDesign
from ...environment.single_job_analyzer import SingleJobAnalyzer
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger
from .integrator import PhenotypeProximityAnalysisIntegrator
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityAnalyzer(SingleJobAnalyzer):
    radius_pixels_lower_limit = 10
    radius_pixels_upper_limit = 100
    radius_number_increments = 4

    def __init__(self,
        outcomes_file: str=None,
        output_path: str=None,
        elementary_phenotypes_file=None,
        complex_phenotypes_file=None,
        **kwargs,
    ):
        super(PhenotypeProximityAnalyzer, self).__init__(**kwargs)
        self.outcomes_file = outcomes_file
        self.output_path = output_path
        self.design = HALOCellMetadataDesign(elementary_phenotypes_file, complex_phenotypes_file)
        self.computational_design = PhenotypeProximityDesign()

        self.retrieve_input_filename()
        self.retrieve_sample_identifier()

    def first_job_started(self):
        logger.info(
            'Beginning multiplexed immunofluorescence cell propinquity analysis.'
        )
        logger.info(
            'Using multiple pixel distance thresholds: %s',
            self.get_radii_of_interest(),
        )
        logger.info(
            'Input files located at %s.',
            dirname(self.get_input_filename()),
        )
        logger.info(
            'Found outcomes file at %s',
            self.outcomes_file,
        )
        logger.info(
            'Will write results to %s',
            self.output_path,
        )

    def _calculate(self):
        self.pull_in_outcome_data()
        self.create_cell_tables()
        self.create_cell_pairs_tables()
        self.cache_masks()
        self.do_aggregation_counting()
        # self.cell_counts_and_intensity_averages()

    def start_post_jobs_step(self):
        cell_proximity_integration = PhenotypeProximityAnalysisIntegrator(
            output_path=self.output_path,
            design=self.design,
        )
        cell_proximity_integration.calculate()

    def pull_in_outcome_data(self):
        """
        Parses outcome assignments from file.
        Saves to outcomes_dict.
        """
        outcomes_df = pd.read_csv(self.outcomes_file, sep='\t')
        columns = outcomes_df.columns
        self.outcomes_dict = {
            row[columns[0]]: row[columns[1]] for i, row in outcomes_df.iterrows()
        }

    def create_cell_tables(self):
        """
        Create tables, one for each source file / field of view index pair, whose
        records correspond to individual cells, with schema:
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
        self.cells = {}

        signatures = self.design.get_all_phenotype_signatures()
        signatures_by_name = {self.design.munge_name(signature) : signature for signature in signatures}
        pheno_names = sorted(signatures_by_name.keys())

        number_fovs = 0
        filename = self.get_input_filename()
        df_file = pd.read_csv(filename)

        # Replace original FOV string descriptor with index
        col = self.design.get_FOV_column()
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
            df['regional compartment'] = 'Not in ' + ';'.join(self.design.get_compartments())
            for compartment in self.design.get_compartments():
                signature = self.design.get_compartmental_signature(df, compartment)
                df.loc[signature, 'regional compartment'] = compartment

            # Create (x,y) values
            xmin, xmax, ymin, ymax = self.design.get_box_limit_column_names()
            df['x value'] = 0.5 * (df[xmax] + df[xmin])
            df['y value'] = 0.5 * (df[ymax] + df[ymin])

            # Add general phenotype membership columns
            for name in pheno_names:
                signature = signatures_by_name[name]
                df[name + ' membership'] = self.design.get_pandas_signature(df, signature)
            phenotype_membership_columns = [name + ' membership' for name in pheno_names]

            # Select pertinent columns and rename
            intensity_column_names = self.design.get_intensity_column_names()
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
            df.rename(columns = {self.design.get_FOV_column() : 'field of view index'}, inplace=True)
            self.cells[(filename, fov_index)] = df

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

    def create_cell_pairs_tables(self):
        """
        Precalculates the distances between cell pairs lying in the same field of view.
        One table is created for each source file and field of view.
        The table schema is:
          - cell 1 index
          - cell 2 index
          - distance in pixels
        """
        self.cell_pairs = {}
        logger.debug('Calculating cell pair distances.')
        logger.debug(
            'Logging: (number of cells in fov, number of cell pairs used, fraction of possible pairs)'
        )
        L = PhenotypeProximityAnalyzer.radius_pixels_upper_limit
        logger.debug('Only using pairs of pixel distance less than %s', L)
        K = len(self.cells)
        for i, ((filename, fov_index), df) in enumerate(self.cells.items()):
            distance_matrix = cdist(df[['x value', 'y value']], df[['x value', 'y value']])
            D = distance_matrix
            D[D > L] = 0
            D = coo_matrix(D)
            self.cell_pairs[(filename, fov_index)] = D
            N = int(len(D.data) / 2)
            M = df.shape[0]
            number_all_pairs = M * (M - 1) / 2
            logger.debug(
                'File,fov %s/%s: (%s, %s, %s%%)',
                i, K, M, N,
                int(100 * 100 * N / number_all_pairs) / 100,
            )
        logger.debug('Completed (field of view limited) cell pair distances calculation.')

    def cache_masks(self):
        signatures = self.design.get_all_phenotype_signatures()
        phenotypes = [self.design.munge_name(signature) for signature in signatures]
        self.phenotype_indices = {
            (f, fov_index) : {
                p : df.index[df[p + ' membership']] for p in phenotypes
            } for (f, fov_index), df in self.cells.items()
        }

        compartments = self.design.get_compartments()
        self.compartment_indices = {
            (f, fov_index) : {
                c : df.index[df['regional compartment'] == c] for c in compartments
            } for (f, fov_index), df in self.cells.items()
        }

    def do_aggregation_counting(self):
        """
        Calculates the number of cell pairs satisfying criteria:
          - source file fixed
          - source/target compartment membership
          - source phenotype membership
          - target phenotype membership
          - radius limitation
        for a range of parameter values.

        Also calculates the number of cells satisfying criteria:
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
        signatures = self.design.get_all_phenotype_signatures()
        phenotypes = [self.design.munge_name(signature) for signature in signatures]
        combinations = list(itertools.combinations(phenotypes, 2))
        logger.debug('Creating radius-limited data sets for %s phenotype pairs.', len(combinations))
        results = []
        for combination in combinations:
            results_combo = self.do_aggregation_one_phenotype_pair(combination)
            results.append(results_combo)
        logger.debug('All %s combinations aggregated.', len(combinations))
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
        self.write_job_results(radius_limited_counts)
        logger.debug('Completed counting cell pairs in "%s" under radius constraint.', self.input_file_identifier)

    def do_aggregation_one_phenotype_pair(self, pair):
        source, target = sorted(list(pair))
        records = []
        sample_identifier = self.get_sample_identifier() # Need to refactor the below to explicitly involve 1 source file
        for compartment in list(set(self.design.get_compartments())) + ['all']:
            for radius in self.get_radii_of_interest():
                count = 0
                for (source_filename, fov_index), distance_matrix in self.cell_pairs.items():
                    outcome = self.outcomes_dict[sample_identifier]
                    rows = self.phenotype_indices[(source_filename, fov_index)][source]
                    cols = self.phenotype_indices[(source_filename, fov_index)][target]
                    if compartment != 'all':
                        rows = rows.intersection(self.compartment_indices[(source_filename, fov_index)][compartment])
                        cols = cols.intersection(self.compartment_indices[(source_filename, fov_index)][compartment])
                    p2p_distance_matrix = distance_matrix.toarray()[rows][:, cols]
                    count += np.sum( (p2p_distance_matrix < radius) & (p2p_distance_matrix > 0) )
                number_fovs = len(self.cell_pairs)
                records.append([sample_identifier, outcome, source, target, compartment, radius, count / number_fovs])

        # logger.debug('%s, %s aggregation and cell pair selection complete.', source, target)
        return records

    def write_job_results(self, radius_limited_counts):
        df = radius_limited_counts

        # Need to do the waiting thing, in case db is locked

        connection = sqlite3.connect(join(self.output_path, self.computational_design.get_database_uri()))
        cursor = connection.cursor()

        for i, row in df.iterrows():
            keys_list = [column_name for column_name, dtype in self.computational_design.get_cell_pair_counts_table_header()]
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
            cursor.execute(cmd)

        cursor.close()
        connection.commit()
        connection.close()

    def cell_counts_and_intensity_averages(self):
        """
        Needs to be refactored based on new indexing aggregation level.
        """
        signatures = self.design.get_all_phenotype_signatures()
        phenotypes = [self.design.munge_name(signature) for signature in signatures]
        records = []
        intensity_column_names = list(self.design.get_intensity_column_names().keys())
        for phenotype in phenotypes:

            for i, (filename, single_file_cells) in enumerate(self.cells.items()):
                by_file_fov = single_file_cells.groupby('field of view index')
                for fov_index, df in by_file_fov:
                    index = list(df.index)

                    marked_fov_cells_indices = set(index).intersection(self.phenotype_indices[filename][phenotype])
                    for compartment in list(set(self.design.get_compartments())) + ['all']:
                        if compartment != 'all':
                            marked_fov_cells_indices = marked_fov_cells_indices.intersection(self.compartment_indices[filename][compartment])

                    marked_fov_cells = df[marked_fov_cells_indices]

                    average_intensities = dict(df[intensity_column_names].mean())


            select_phenotype = self.cells.loc[
                (self.cells[phenotype + ' membership'])
            ]

            for compartment in list(set(self.cells['regional compartment'])) + ['all']:
                if compartment != 'all':
                    subselection = select_phenotype[select_phenotype['regional compartment'] == compartment]
                else:
                    subselection = select_phenotype
                c = ['source file name', 'field of view index']
                for [source_filename, fov], df in subselection.groupby(c):
                    average_intensities = dict(df[intensity_column_names].mean())
                    if compartment == 'all':
                        total_in_field = self.get_total_in_field(source_filename, fov)
                        fraction = df.shape[0] / total_in_field
                    else:
                        fraction = None
                    records.append({**
                        {
                            'phenotype' : phenotype,
                            'source file name' : source_filename,
                            'field of view index' : fov,
                            'regional compartment' : compartment,
                            'count' : df.shape[0],
                            'count fraction of all cells in FOV' : fraction,
                        },
                        **average_intensities,
                    })
        cell_counts_and_intensity_averages = pd.DataFrame(records)
        logger.debug('Completed cell counts and intensity average over FOVs.')

    def get_radii_of_interest(self):
        """
        Creates a scale-adjusted range of values between the stipulated lower and upper
        limits, with the stipulated number of increments.
        """
        r = PhenotypeProximityAnalyzer.radius_pixels_lower_limit
        R = PhenotypeProximityAnalyzer.radius_pixels_upper_limit
        N = PhenotypeProximityAnalyzer.radius_number_increments

        a = math.exp((math.log(R / r) / N))
        return [int(r * math.pow(a, i)) for i in range(N + 1)]

    def flatten_lists(self, the_lists):
        result = []
        for _list in the_lists:
            result += _list
        return result
