"""
The core calculator for the proximity calculation on a single source file.
"""
from os.path import join
from math import exp
from math import log
from math import pow as math_pow
from itertools import combinations
import sqlite3

import pandas as pd
import numpy as np
import sklearn
from sklearn.neighbors import BallTree

from ...common.sqlite_context_utility import WaitingDatabaseContextManager
from ..defaults.core import CoreJob
from ....standalone_utilities.log_formats import colorized_logger
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityCoreJob(CoreJob):
    radii = [20, 60, 100]

    def __init__(self, **kwargs):
        super(PhenotypeProximityCoreJob, self).__init__(**kwargs)
        self.fov_lookup = {}

    @staticmethod
    def solicit_cli_arguments(parser):
        pass

    def _calculate(self):
        self.calculate_proximity()

    def initialize_metrics_database(self):
        cell_pair_counts_header = self.computational_design.get_cell_pair_counts_table_header()

        connection = sqlite3.connect(self.computational_design.get_database_uri())
        cursor = connection.cursor()
        cmd = ' '.join([
            'CREATE TABLE IF NOT EXISTS',
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

    def calculate_proximity(self):
        """
        The main exposed entrypoint into the calculation.

        Aggregates and writes counts to database.
        """
        logger.info(
            'Started core calculation, %s, for %s.',
            'balanced' if self.computational_design.balanced else 'unbalanced',
            self.input_filename,
        )
        self.timer.record_timepoint('Started cell table calculation')
        cells = self.create_cell_tables()
        cell_pairs = self.create_cell_trees(cells)
        phenotype_indices, compartment_indices = self.precalculate_masks(cells)
        radius_limited_counts = self.do_aggregation_counting(
            cells,
            cell_pairs,
            phenotype_indices,
            compartment_indices,
        )
        self.write_cell_pair_counts(radius_limited_counts)
        self.timer.record_timepoint('Finished writing pair counts')

    def cache_fov_strings(self, table_file):
        """
        :param table_file: Table with cell data.
        :type table_file: pandas.DataFrame
        """
        fovs = sorted(list(set(table_file[self.dataset_design.get_FOV_column(table=table_file)])))
        for i, fov in enumerate(fovs):
            self.fov_lookup[i] = fov

    def replace_fov_strings_with_index(self, table_file):
        """
        :param table_file: Table with cell data.
        :type table_file: pandas.DataFrame
        """
        fov_column = self.dataset_design.get_FOV_column(table=table_file)
        fovs = sorted(list(set(table_file[fov_column])))
        for i, fov in enumerate(fovs):
            table_file.loc[table_file[fov_column] == fov, fov_column] = i

    def add_compartment_information(self, table):
        """
        :param table: Table with cell data.
        :type table: pandas.DataFrame
        """
        if 'regional compartment' in table.columns:
            logger.error(
                'Woops, name collision in "regional compartment". Trying to create new column.'
            )
            return
        compartments = self.dataset_design.get_compartments()
        table['regional compartment'] = 'Not in ' + ';'.join(compartments)
        for compartment in compartments:
            signature = self.dataset_design.get_compartmental_signature(table, compartment)
            table.loc[signature, 'regional compartment'] = compartment

    def add_box_centers(self, table):
        """
        :param table: Table with cell data.
        :type table: pandas.DataFrame
        """
        xmin, xmax, ymin, ymax = self.dataset_design.get_box_limit_column_names()
        table['x value'] = 0.5 * (table[xmax] + table[xmin])
        table['y value'] = 0.5 * (table[ymax] + table[ymin])

    def add_membership(self, table):
        """
        :param table: Table with cell data.
        :type table: pandas.DataFrame
        """
        signatures_by_name = self.computational_design.get_all_phenotype_signatures(by_name=True)
        for name, signature in signatures_by_name.items():
            table[name + ' membership'] = self.dataset_design.get_pandas_signature(table, signature)

    def restrict_to_pertinent_columns(self, table):
        """
        :param table: Table with cell data.
        :type table: pandas.DataFrame
        """
        signatures_by_name = self.computational_design.get_all_phenotype_signatures(by_name=True)
        phenotype_membership_columns = [
            name + ' membership' for name, _ in signatures_by_name.items()
        ]
        intensity_column_names = self.dataset_design.get_intensity_column_names()
        inverse = {value:key for key, value in intensity_column_names.items()}
        source_columns = list(intensity_column_names.values())
        pertinent_columns = [
            'regional compartment',
            'x value',
            'y value',
        ] + source_columns + phenotype_membership_columns + [self.dataset_design.get_cell_area_column()]
        table.drop(
            [column for column in table.columns if not column in pertinent_columns],
            axis=1,
            inplace=True,
        )
        table.rename(columns = inverse, inplace=True)

    def create_cell_tables(self):
        """
        Create tables, one for each field of view in the given source file, whose
        records correspond to individual cells. The schema is:

        - "regional compartment"
        - "x value"
        - "y value"
        - "<elementary phenotype 1> <cellular site 1> intensity"
        - "<elementary phenotype 2> <cellular site 1> intensity"
        - ...
        - "<elementary phenotype 1> <cellular site 2> intensity"
        - "<elementary phenotype 2> <cellular site 2> intensity"
        - ...
        - "<general phenotype 1> membership"
        - "<general phenotype 2> membership"
        - ...

        :return: Dictionary whose keys are field of view integer indices and values are
            tables of cells.
        :rtype: dict
        """
        self.timer.record_timepoint('Started loading cell table into memory')
        table_file = self.get_table(self.input_filename)
        self.timer.record_timepoint('Finished loading cell table')
        self.dataset_design.normalize_fov_descriptors(table_file)
        self.cache_fov_strings(table_file)
        self.replace_fov_strings_with_index(table_file)

        self.timer.record_timepoint('Done normalizing FOV strings')
        cells = {}
        phenotype_names = self.computational_design.get_all_phenotype_names()
        number_cells_by_phenotype = {phenotype : 0 for phenotype in phenotype_names}
        self.timer.record_timepoint('Started grouping by FOV')
        grouped = table_file.groupby(self.dataset_design.get_FOV_column(table=table_file))
        self.timer.record_timepoint('Finished grouping by FOV')
        for fov_index, table_fov in grouped:
            self.timer.record_timepoint('Started one FOV cell table iteration')
            table = table_fov.copy()
            self.timer.record_timepoint('Done copying table')
            table = table.reset_index(drop=True)
            self.timer.record_timepoint('Done reseting index table')
            self.add_compartment_information(table)
            self.timer.record_timepoint('Done adding compartments')
            self.add_box_centers(table)
            self.timer.record_timepoint('Done adding box center')
            self.add_membership(table)
            self.timer.record_timepoint('Done adding membership columns')
            self.restrict_to_pertinent_columns(table)
            self.timer.record_timepoint('Done restricting to pertinent columns')
            cells[fov_index] = table
            self.timer.record_timepoint('Done saving one FOV cell table')

            for phenotype in phenotype_names:
                number_cells_by_phenotype[phenotype] += sum(table[phenotype + ' membership'])
            self.timer.record_timepoint('Done one FOV recording counts by phenotype')

        most_frequent = sorted(
            list(number_cells_by_phenotype.items()),
            key=lambda x: x[1],
            reverse=True
        )[0]
        logger.debug(
            '%s cells parsed from file. Most frequent signature %s (%s)',
            table_file.shape[0],
            most_frequent[0],
            most_frequent[1],
        )
        logger.debug(
            'Completed cell table collation from input file %s.',
            self.input_filename,
        )
        return cells

    def create_cell_trees(self, cells):
        """
        :param cells: Input collection of cells tables, see
            :py:meth:`create_cell_tables`.
        :type cells: dict

        :return: Dictionary whose keys are field of view integer indices and values are
            sklearn.neighbors.BallTree objects.
        :rtype: dict
        """
        cell_trees = {}
        self.timer.record_timepoint('Started creating cell trees')
        logger.debug(
            'Calculating cell trees for cells from %s.',
            self.input_filename,
        )
        for _, (fov_index, table) in enumerate(cells.items()):
            cell_trees[fov_index] = BallTree(table[['x value', 'y value']].to_numpy())
        logger.debug(
            'Completed (field of view limited) cell tree construction from %s.',
            self.input_filename,
        )
        self.timer.record_timepoint('Done creating cell trees')
        return cell_trees

    def precalculate_masks(self, cells):
        """
        :param cells: Cells tables by field of view integer index.
        :type cells: dict

        :return: A 2-element list, phenotype and compartment masks.
        :rtype: list
        """
        phenotypes = self.computational_design.get_all_phenotype_names()

        phenotype_indices = {
            fov_index : {
                p : table[p + ' membership'] for p in phenotypes
            } for fov_index, table in cells.items()
        }
        self.timer.record_timepoint('Done creating phenotype masks')

        compartments = self.dataset_design.get_compartments()
        compartment_indices = {
            fov_index : {
                c : (table['regional compartment'] == c) for c in compartments
            } for fov_index, table in cells.items()
        }
        self.timer.record_timepoint('Done creating compartment masks')

        return [phenotype_indices, compartment_indices]

    def get_considered_phenotype_pairs(self):
        phenotypes = self.computational_design.get_all_phenotype_names()
        if self.computational_design.balanced:
            return list(combinations(phenotypes, 2))
        else:
            return [(p1, p2) for p1 in phenotypes for p2 in phenotypes]

    def do_aggregation_counting(self,
        cells,
        cell_trees,
        phenotype_indices,
        compartment_indices,
    ):
        """
        :param cell_trees: See :py:meth:`create_cell_trees`.
        :type cell_trees: dict

        :param phenotype_indices: See :py:meth:`precalculate_masks`.
        :type phenotype_indices: dict

        :param compartment_indices: See :py:meth:`precalculate_masks`.
        :type compartment_indices: dict

        :return: Table of radius-limited counts.
        :rtype: pandas.DataFrame
        """
        combinations2 = self.get_considered_phenotype_pairs()
        logger.debug(
            'Creating radius-limited counts for %s phenotype pairs.',
            len(combinations2),
        )
        results = []
        self.timer.record_timepoint('Done retrieving phenotype pairs')
        for combination in combinations2:
            results_combo = self.do_aggregation_one_phenotype_pair(
                combination,
                cells,
                cell_trees,
                phenotype_indices,
                compartment_indices,
            )
            results.append(results_combo)
            logger.debug('Cell pairs of types %s counted.', combination)
        self.timer.record_timepoint('Done aggregating over all phenotype pairs')
        logger.debug('All %s combinations counted.', len(combinations2))
        columns = [
            'sample identifier',
            'input filename',
            'outcome assignment',
            'source phenotype',
            'target phenotype',
            'compartment',
            'distance limit in pixels',
            self.computational_design.get_primary_output_feature_name(),
            'source phenotype count',
        ] # Get this from computational design??
        radius_limited_counts = pd.DataFrame(
            PhenotypeProximityCoreJob.flatten_lists(results),
            columns=columns,
        )
        self.timer.record_timepoint('Done flattening into radius-limit counts')
        logger.debug(
            'Completed counting cell pairs in "%s" under radius constraint.',
            self.input_filename,
        )
        return radius_limited_counts

    def do_aggregation_one_phenotype_pair(self,
        pair,
        cells,
        cell_trees,
        phenotype_indices,
        compartment_indices,
    ):
        """
        :param pairs: Pair of phenotype names.
        :type pairs: 2-tuple

        :param cells: Values are pairs, FOV index and cell table.
        :type cells: dict

        :param cell_trees: See :py:meth:`create_cell_trees`.
        :type cell_trees: dict

        :param phenotype_indices: See :py:meth:`precalculate_masks`.
        :type phenotype_indices: dict

        :param compartment_indices: See :py:meth:`precalculate_masks`.
        :type compartment_indices: dict

        :return: Table of radius-limited counts for just this one phenotype pair.
        :rtype: pandas.DataFrame
        """
        balanced = self.computational_design.balanced
        if balanced:
            source, target = sorted(list(pair))
        else:
            source, target = [pair[0], pair[1]]
        records = []
        for compartment in list(set(self.dataset_design.get_compartments())) + ['all']:
            for radius in PhenotypeProximityCoreJob.get_radii_of_interest():
                count = 0
                source_count = 0
                self.timer.record_timepoint('Started one compartment/radius/phenotype pair')
                for _, (fov_index, table) in enumerate(cells.items()):
                    rows = phenotype_indices[fov_index][source]
                    cols = phenotype_indices[fov_index][target]
                    self.timer.record_timepoint('Retrieved phenotype masks')
                    if compartment != 'all':
                        rows = rows & compartment_indices[fov_index][compartment]
                        cols = cols & compartment_indices[fov_index][compartment]
                        self.timer.record_timepoint('Overlaid compartment masks')
                    tree = cell_trees[fov_index]
                    self.timer.record_timepoint('Retrieved cell tree')
                    source_cell_locations = table.loc[rows][['x value', 'y value']]
                    self.timer.record_timepoint('Retrieved cell locations')
                    if source_cell_locations.shape[0] == 0:
                        continue
                    indices = tree.query_radius(
                        source_cell_locations,
                        radius,
                        return_distance=False,
                    )
                    self.timer.record_timepoint('Completed tree query at radius')
                    target_indices = set([i for i in range(len(cols)) if cols[i]])
                    additional = sum([len(target_indices.intersection(i)) for i in indices])
                    self.timer.record_timepoint('Completed counting result in target phenotype')

                    if np.isnan(additional):
                        continue

                    count += additional
                    count -= sum(rows & cols)
                    source_count += sum(rows)
                    self.timer.record_timepoint('Finished aggregation iteration')

                if balanced:
                    area = sum(table.loc[compartment_indices[fov_index][compartment]][
                        self.dataset_design.get_cell_area_column()
                    ])
                    if area == 0:
                        logger.warning(
                            'Area computation failed for compartment "%s" in "%s".',
                            compartment,
                            self.sample_identifier,
                        )

                if source_count == 0:
                    logger.warning(
                        'No cells of "source" phenotype %s in %s, %s, within %s .',
                        source,
                        self.sample_identifier,
                        compartment,
                        radius,
                    )
                else:
                    if balanced:
                        feature_value = count / area
                    else:
                        feature_value = count / source_count # See GitHub issue #20
                    records.append([
                        self.sample_identifier,
                        self.input_filename,
                        self.outcome,
                        source,
                        target,
                        compartment,
                        radius,
                        feature_value,
                        source_count,
                    ])
        self.timer.record_timepoint('Completed aggregation one phenotype pair')
        return records

    def write_cell_pair_counts(self, radius_limited_counts):
        """
        :param radius_limited_counts: Cell pair counts table.
        :type radius_limited_counts: pandas.DataFrame
        """
        header = self.computational_design.get_cell_pair_counts_table_header()
        keys_list = [column_name for column_name, dtype in header]

        uri = self.computational_design.get_database_uri()
        with WaitingDatabaseContextManager(uri) as manager:
            for _, row in radius_limited_counts.iterrows():
                values_list = [
                    '"' + row['sample identifier'] + '"',
                    '"' + row['input filename'] + '"',
                    '"' + row['outcome assignment'] + '"',
                    '"' + row['source phenotype'] + '"',
                    '"' + row['target phenotype'] + '"',
                    '"' + row['compartment'] + '"',
                    str(int(row['distance limit in pixels'])),
                    str(float(row[self.computational_design.get_primary_output_feature_name()])),
                    str(int(row['source phenotype count'])),
                ] # Make this programmatic over the headers provided by computational design???
                keys = '( ' + ' , '.join(keys_list) + ' )'
                values = '( ' + ' , '.join(values_list) + ' )'
                cmd = ('INSERT INTO %s ' % self.computational_design.get_cell_pair_counts_table_name()) + keys + ' VALUES ' + values +  ' ;'
                try:
                    manager.execute(cmd)
                except sqlite3.OperationalError as exception:
                    logger.error('SQL query failed: %s', cmd)
                    raise exception
        self.timer.record_timepoint('Done writing cell pair counts to file')

    @staticmethod
    def get_radii_of_interest():
        return PhenotypeProximityCoreJob.radii

    @staticmethod
    def flatten_lists(the_lists):
        """
        :param the_lists: List of lists to be flattened into a single list.
        :type the_lists: list

        :return: The flattened list.
        :rtype: list
        """
        result = []
        for _list in the_lists:
            result += _list
        return result
