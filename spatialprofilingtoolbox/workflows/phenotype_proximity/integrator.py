"""
The integration phase of the proximity workflow. Performs statistical tests.
"""
from os.path import join
import sqlite3
import itertools
import re

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, kruskal

from ...environment.file_io import get_outcomes_files
from ...environment.settings_wrappers import DatasetSettings
from ...environment.log_formats import colorized_logger
from .computational_design import PhenotypeProximityDesign

logger = colorized_logger(__name__)


class PhenotypeProximityAnalysisIntegrator:
    """
    The main class of the integration phase.
    """
    def __init__(self,
        dataset_settings: DatasetSettings=None,
        computational_design: PhenotypeProximityDesign=None,
        **kwargs,
    ):
        """
        :param dataset_settings: Dataset-specific paths and settings.
        :type dataset_settings: DatasetSettings

        :param computational_design: The design object for the proximity workflow.
        """
        self.outcomes_file = get_outcomes_files(dataset_settings)[0]
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results to file.
        """
        logger.info(
            'Doing %s phenotype proximity workflow integration phase.',
            'balanced' if self.computational_design.balanced else 'unbalanced',
        )
        cell_proximity_tests = self.do_outcome_tests()
        if cell_proximity_tests is not None:
            self.export_results(cell_proximity_tests)
        else:
            logger.warning('No stats to export for phenotype proximity workflow.')

    def do_outcome_tests(self):
        """
        For each:

        - pair of outcome values
        - compartment
        - pair of phenotypes
        - radius limit value

        calculates p-values and effect size for statistical testing for difference of
        distributions, one for each outcome value, of normalized cell pair counts as the
        source file varies (within a given outcome assignment class).

        The statistical tests are t-test for difference in mean and Kruskal-Wallis test
        for difference in median.

        :return: ``cell_proximity_tests``.
        :rtype: pandas.DataFrame
        """
        records = []
        table = self.retrieve_radius_limited_counts()
        outcomes = sorted(list(set(table['outcome assignment']).difference(set(['unknown']))))
        for outcome1, outcome2 in itertools.combinations(outcomes, 2):
            subselection1 = table[table['outcome assignment'] == outcome1]
            subselection2 = table[table['outcome assignment'] == outcome2]
            columns = [
                'source phenotype',
                'target phenotype',
                'compartment',
                'distance limit in pixels',
            ]
            grouped1 = subselection1.groupby(columns)
            grouped2 = subselection2.groupby(columns)
            cases = set(grouped1.indices.keys()).intersection(set(grouped2.indices.keys()))
            for case in cases:
                [source_phenotype, target_phenotype, compartment, radius] = case
                feature = self.computational_design.get_aggregated_metric_name()
                values1 = grouped1.get_group(case)[feature]
                values2 = grouped2.get_group(case)[feature]
                if len(values1) < 3 or len(values2) < 3:
                    continue
                if np.var(values1) == 0 or np.var(values2) == 0:
                    continue
                _, p_ttest = ttest_ind(values1, values2, equal_var=False, nan_policy='omit')
                mean_difference = values2.mean() - values1.mean()
                _, p_kruskal = kruskal(values1, values2, nan_policy='omit')
                median_difference = values2.median() - values1.median()
                records.append({
                    'outcome 1' : outcome1,
                    'outcome 2' : outcome2,
                    'source phenotype' : source_phenotype,
                    'target phenotype' : target_phenotype,
                    'compartment' : compartment,
                    'distance limit in pixels' : radius,
                    'tested value 1' : values1.mean(),
                    'tested value 2' : values2.mean(),
                    'test' : 't-test',
                    'p-value' : p_ttest,
                    'absolute effect' : abs(mean_difference),
                    'effect sign' : int(np.sign(mean_difference)),
                    'p-value < 0.01' : p_ttest < 0.01,
                })
                records.append({
                    'outcome 1' : outcome1,
                    'outcome 2' : outcome2,
                    'source phenotype' : source_phenotype,
                    'target phenotype' : target_phenotype,
                    'compartment' : compartment,
                    'distance limit in pixels' : radius,
                    'tested value 1' : values1.median(),
                    'tested value 2' : values2.median(),
                    'test' : 'Kruskal-Wallis',
                    'p-value' : p_kruskal,
                    'absolute effect' : abs(median_difference),
                    'effect sign' : int(np.sign(median_difference)),
                    'p-value < 0.01' : p_kruskal < 0.01,
                })

                keyed_values1 = ' '.join([str( (row['sample identifier'], row[feature]) ) for i, row in grouped1.get_group(case).iterrows()])
                keyed_values2 = ' '.join([str( (row['sample identifier'], row[feature]) ) for i, row in grouped2.get_group(case).iterrows()])

                logger.debug(
                    'For "%s" vs "%s", phenotype pair (%s, %s), %s, pixels < %s, did t-test and KW on values: (1) %s   (2) %s',
                    outcome1,
                    outcome2,
                    source_phenotype,
                    target_phenotype,
                    compartment,
                    str(radius),
                    keyed_values1,
                    keyed_values2,
                )
        if len(records) == 0:
            logger.info('No non-trivial tests to perform. Probably too few values.')
            return None
        cell_proximity_tests = pd.DataFrame(records)
        sort_order = ['outcome 1', 'outcome 2', 'p-value < 0.01', 'absolute effect', 'p-value']
        ascending = [True, True, False, False, True]
        cell_proximity_tests.sort_values(by=sort_order, ascending=ascending, inplace=True)
        return cell_proximity_tests

    def export_results(self, cell_proximity_tests):
        """
        Writes the result of the statistical tests to file, in order of statistical
        significance.

        :param cell_proximity_tests: Tabular form of test results.
        :type cell_proximity_tests: pandas.DataFrame
        """
        tests_str = cell_proximity_tests.to_csv(index=False)
        print(tests_str)

    def retrieve_radius_limited_counts(self):
        """
        :return table: Data frame version of all cell pair counts data.
        :type table: pandas.DataFrame
        """
        uri = self.computational_design.get_database_uri()
        connection = sqlite3.connect(uri)
        table_unaggregated = pd.read_sql_query('SELECT * FROM %s' % self.computational_design.get_cell_pair_counts_table_name(), connection)
        connection.close()
        table = self.do_aggregation_over_different_files(table_unaggregated)
        self.add_balance_metadata(table)
        self.save_aggregated_radius_limited_counts(table)
        table = table.rename(columns={key:re.sub('_', ' ', key) for key in table.columns})
        return table

    def do_aggregation_over_different_files(self, table):
        """
        :param table: Table of cell pair counts.
        :type table: pandas.DataFrame

        :return table: Same table, but with main column *weighted-averaged* over cases
            of multiple files associated with the same sample, with weights the source
            phenotype counts in the unbalanced case. In the balanced case, the cell
            pair counts per unit slide area may simply be summed.
        :type table: pandas.DataFrame
        """
        # table.drop('id', 1, inplace=True)

        case_classifiers = [
            'sample_identifier',
            'outcome_assignment',
            'source_phenotype',
            'target_phenotype',
            'compartment',
            'distance_limit_in_pixels',
        ] # Get this from computational design!!
        if self.computational_design.balanced:
            table = table.groupby(case_classifiers, as_index=False).agg('sum')
            f1 = self.computational_design.get_primary_output_feature_name(style='sql')
            f2 = self.computational_design.get_aggregated_metric_name(style='sql')
            table.rename(columns={f1 : f2}, inplace=True)
        else:
            agg = self.custom_per_sample_aggregation_function
            logger.debug(
                'Started grouping %s x %s table by case classifiers: %s',
                table.shape[0],
                table.shape[1],
                case_classifiers,
            )
            table = table.groupby(case_classifiers, as_index=False).apply(agg)
            logger.debug('Done grouping.')

        table.reset_index(inplace=True)
        table.rename(columns={'index' : 'id'}, inplace=True)
        return table

    def custom_per_sample_aggregation_function(self, sub_table):
        metric = self.computational_design.get_primary_output_feature_name(style='sql')
        multiplied = [
            row[metric] * row['source_phenotype_count']
            for i, row in sub_table.iterrows()
        ]
        denominator = sum(sub_table['source_phenotype_count'])
        if denominator == 0:
            frac = -1
        else:
            frac = sum(multiplied) / denominator
        return pd.Series({
            self.computational_design.get_aggregated_metric_name(style='sql') : frac,
            'source_phenotype_count' : denominator,
        })

    def add_balance_metadata(self, table):
        """
        :param table: Table to which to add metadata tag/column indicating the balance
            type.
        :type table: pandas.DataFrame
        """
        table['metric_type'] = self.computational_design.get_metric_description()

    def save_aggregated_radius_limited_counts(self, table):
        """
        :param table: Table of cell pair counts.
        :type table: pandas.DataFrame
        """
        uri = self.computational_design.get_database_uri()
        connection = sqlite3.connect(uri)
        table.to_sql(
            self.computational_design.get_cell_pair_counts_table_name() + '_aggregated',
            connection,
            if_exists='replace',
        )
        connection.close()
