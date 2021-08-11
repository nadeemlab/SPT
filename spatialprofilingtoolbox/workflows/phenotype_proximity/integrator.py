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

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class PhenotypeProximityAnalysisIntegrator:
    """
    The main class of the integration phase.
    """
    def __init__(
        self,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
    ):
        """
        :param jobs_paths: Convenience bundle of paths.
        :type jobs_paths: JobsPaths

        :param dataset_settings: Dataset-specific paths and settings.
        :type dataset_settings: DatasetSettings

        :param computational_design: The design object for the proximity workflow.
        """
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.computational_design = computational_design
        self.cell_proximity_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results to file.
        """
        cell_proximity_tests = self.do_outcome_tests()
        if cell_proximity_tests is not None:
            self.export_results(cell_proximity_tests)
            logger.info(
                'Done exporting stats for phenotype proximity workflow to %s.',
                self.computational_design.get_stats_tests_file(),
            )
        else:
            logger.info('No stats to export for phenotype proximity workflow.')

    def do_outcome_tests(self):
        """
        For each

          - pair of outcome values
          - compartment
          - pair of phenotypes
          - radius limit value

        calculates p-values and effect size for statistical testing for difference of
        distributions, one for each outcome value, of normalized cell pair counts the
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
                values1 = grouped1.get_group(case)['cell pair count per FOV']
                values2 = grouped2.get_group(case)['cell pair count per FOV']
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
        cell_proximity_tests.to_csv(
            join(
                self.output_path,
                self.computational_design.get_stats_tests_file(),
            ),
            index=False,
        )

    def retrieve_radius_limited_counts(self):
        """
        :return table: Data frame version of all cell pair counts data.
        :type table: pandas.DataFrame
        """
        uri = join(self.output_path, self.computational_design.get_database_uri())
        connection = sqlite3.connect(uri)
        table = pd.read_sql_query('SELECT * FROM cell_pair_counts', connection)
        table = table.rename(columns={key:re.sub('_', ' ', key) for key in table.columns})
        connection.close()
        return table
