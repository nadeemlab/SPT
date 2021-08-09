import os
from os.path import join
import re
import itertools

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, kruskal

from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.log_formats import colorized_logger
from .data_logging import FrequencyDataLogger

logger = colorized_logger(__name__)


class FrequencyAnalysisIntegrator:
    """
    The integration phase of the cell phenotype frequency workflow combines data
    across samples and performs tests for statistically-significant differences
    between outcome groups.
    """
    def __init__(
        self,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
    ):
        """
        :param jobs_paths: Convenience bundle of filesystem paths pertinent to a
            particular run at the job level.
        :type jobs_paths: JobsPaths

        :param dataset_settings: Convenience bundle of paths to input dataset files.
        :type dataset_settings: DatasetSettings

        :param computational_design: Design object providing metadata specific to the
            frequency workflow.
        """
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.computational_design = computational_design
        self.frequency_tests = None
        self._fov_lookup_dict = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('Starting stats.')
        frequency_tests = self.do_outcome_tests()
        if frequency_tests is not None:
            self.export_results(frequency_tests)
            logger.info('Done exporting stats.')
        else:
            logger.warning('Test results not generated.')

    def do_outcome_tests(self):
        """
        For each phenotype and compartment type:

        1. Sums over FOVs, and over cells, the cell areas belonging to that phenotype and
           compartment type.
        2. Normalizes over the total cell areas independently of phenotype.
        3. Tests resulting feature over sample set for outcome pair comparison. Tests are
           t-test and Kruskal-Wallis.
        """
        cells = self.get_dataframe_from_db('cells')
        phenotype_columns = self.overlay_areas_on_masks(cells)
        FrequencyDataLogger.log_cell_areas_one_fov(cells, self.get_fov_lookup_dict())

        area_sums, sum_columns = self.sum_areas_over_compartments_per_phenotype(
            cells,
            phenotype_columns,
        )
        areas_all_phenotypes_dict = self.overlay_area_total_all_phenotypes(cells, area_sums)
        FrequencyDataLogger.log_normalization_factors(areas_all_phenotypes_dict)

        normalized_sum_columns = self.add_normalized_columns(area_sums, phenotype_columns, sum_columns)
        FrequencyDataLogger.log_normalized_areas(cells, area_sums, normalized_sum_columns)

        outcomes = sorted(list(set(cells['outcome_assignment'])))
        phenotype_names = [re.sub(' membership', '', column) for column in phenotype_columns]
        rows = []
        for compartment, df in area_sums.groupby(['compartment']):
            for outcome1, outcome2 in itertools.combinations(outcomes, 2):
                for phenotype_name in phenotype_names:
                    row, df1, df2 = self.get_test_result_row(
                        compartment,
                        df,
                        outcome1,
                        outcome2,
                        phenotype_name,
                        test='t-test',
                    )
                    if not row is None:
                        rows.append(row)

                    row, df1, df2 = self.get_test_result_row(
                        compartment,
                        df,
                        outcome1,
                        outcome2,
                        phenotype_name,
                        test='Kruskal-Wallis',
                    )
                    if not row is None:
                        rows.append(row)

                    if not row is None:
                        FrequencyDataLogger.log_test_input(row, df1, df2)

        if len(rows) == 0:
            logger.info('No non-trivial tests to perform. Probably too few values.')
            return None
        frequency_tests = pd.DataFrame(rows)
        sort_order = ['outcome 1', 'outcome 2', 'p-value < 0.01', 'p-value']
        ascending = [True, True, False, True]
        frequency_tests.sort_values(by=sort_order, ascending=ascending, inplace=True)
        return frequency_tests

    def overlay_areas_on_masks(self, cells):
        """
        Copies the "cell_area" column over the phenotype membership mask columns.

        :param cells: The cells table with phenotype membership 0/1 masks with column
            names of the form "<phenotype name> membership", as well as column
            "cell_area".
        :type cells: pandas.DataFrame

        :return: ``phenotype_columns`` byproduct, list of membership columns.
        :rtype: list
        """
        phenotype_columns = [
            column for column in cells.columns if re.search('membership$', str(column))
        ]
        for phenotype in phenotype_columns:
            mask = (cells[phenotype] == 1)
            cells.loc[mask, phenotype] = cells['cell_area']
        return phenotype_columns

    def sum_areas_over_compartments_per_phenotype(self, cells, phenotype_columns):
        """
        Sums cell areas over all FOVs for a given named compartment type and phenotype,
        in a given slide/sample.

        :param cells: The cells table with phenotype membership area-weighted masks,
            with column names of the form "<phenotype name> membership", as well as
            columns:

            - "sample_identifier"
            - "compartment"
            - "outcome_assignment"
        :type cells: pandas.DataFrame

        :return:
            - ``area_sums``. Aggregation of the cells table, with new columns given by
              ``sum_columns``.
            - ``sum_columns``. The new columns dictionary, in terms of original columns.
              The values of this dictionary have the form
              "<phenotype name> cell area sum".
        :rtype: pandas.Dataframe, dict
        """
        sum_columns = {
            p : re.sub('membership$', 'cell area sum', p)
            for p in phenotype_columns
        }
        area_aggregation = {
            sum_column : pd.NamedAgg(column=phenotype_column, aggfunc='sum')
            for phenotype_column, sum_column in sum_columns.items()
        }
        select_0 = lambda x: list(x)[0]
        outcome_passthrough = {
            'outcome_assignment' : pd.NamedAgg(column='outcome_assignment', aggfunc=select_0),
        }
        individual_compartments = ['sample_identifier', 'compartment']
        area_sums = cells.groupby(individual_compartments, as_index=False).agg(
            **area_aggregation,
            **outcome_passthrough,
        )
        return [area_sums, sum_columns]

    def overlay_area_total_all_phenotypes(self, cells, area_sums):
        """
        Calculates total cell areas (independent of phenotypes) from ``cells``, and adds
        this data as a new column in-place into the ``area_sums`` table. The new column
        is "compartmental total cell area". 

        :param cells: The cells table.
        :type cells: pandas.DataFrame

        :param area_sums: The ``area_sums`` table. See
            :py:meth:`sum_areas_over_compartments_per_phenotype`.
        :type area_sums: pandas.DataFrame

        :return: ``areas_all_phenotypes_dict``. Dictionary providing the newly-computed
            area values as a function of the pair (sample identifier, compartment).
        :rtype: dict
        """
        sample_combined_compartments = ['sample_identifier', 'compartment']
        areas_all_phenotypes = cells.groupby(sample_combined_compartments, as_index=False).agg(
            **{ 'compartmental total cell area' : pd.NamedAgg(column='cell_area', aggfunc='sum') }
        )
        areas_all_phenotypes_dict = {
            (r['sample_identifier'], r['compartment']) : r['compartmental total cell area']
            for i, r in areas_all_phenotypes.iterrows()
        }
        area_sums['cell area all phenotypes'] = [
            areas_all_phenotypes_dict[(r['sample_identifier'], r['compartment'])]
            for i, r in area_sums.iterrows()
        ]
        return areas_all_phenotypes_dict

    def add_normalized_columns(self, area_sums, phenotype_columns, sum_columns):
        """
        :param area_sums: The table with cell area sums, after
            :py:meth:`overlay_area_total_all_phenotypes` has added the
            phenotype-agnostic normalization factor.
        :type area_sums: pandas.DataFrame

        :param phenotype_columns: The names of the phenotype membership mask columns.
        :type phenotype_columns: list

        :param sum_columns: Mapping from phenotype names to corresponding
            summed-cell-area columns.
        :type sum_columns: dict

        :return: ``normalized_sum_columns``. Byproduct, dictionary providing mapping
            from (the values of) ``sum_columns`` to the column name of the corresponding
            normalized version.
        :rtype: dict
        """
        normalized_sum_columns = {
            p : re.sub('membership', 'normalized cell area sum', p) for p in phenotype_columns
        }
        for p in phenotype_columns:
            normalized = normalized_sum_columns[p]
            summed = sum_columns[p]
            area_sums[normalized] = area_sums[summed] / area_sums['cell area all phenotypes']
        return normalized_sum_columns

    def get_test_result_row(self,
        compartment,
        df,
        outcome1,
        outcome2,
        phenotype_name,
        test: str=None,
    ):
        """
        :param compartment: The compartment/region name in which to consider cells.
        :type compartment: str

        :param df: The table with normalized summed cell areas/fractions,
            already aggregated over cells in each sample/compartment. Must be already
            restricted to ``compartment``. The main column in which numerical data must
            be found is of the form "<phenotype name> normalized cell area sum".
        :type df: pandas.DataFrame

        :param outcome1: Outome label.
        :type outcome1: str

        :param outcome2: The other outcome label.
        :type outcome2: str

        :param phenotype_name: The name of the (composite) phenotype to consider.
        :type phenotype_name: str

        :param test: Either "t-test" or "Kruskal-Wallis".
        :type test: str

        :return:
            - ``row``. Dictionary providing contextual information (compartment,
              phenotype, outcomes, test name), as well as the test result p-values,
              effect sizes, and extreme-sample examples.
            - ``df1``. The phenotype- and compartment-restricted abbreviated area sums
              table, restricted also the outcome 1. Provided for convenience/inspection.
            - ``df2``. The phenotype- and compartment-restricted abbreviated area sums
              table, restricted also the outcome 2. Provided for convenience/inspection.
        :rtype: dict, pandas.DataFrame, pandas.DataFrame
        """
        column = phenotype_name + ' normalized cell area sum'
        df1 = df[df['outcome_assignment'] == outcome1][['sample_identifier', column]]
        df2 = df[df['outcome_assignment'] == outcome2][['sample_identifier', column]]
        values1 = list(df1[column])
        values2 = list(df2[column])
        if np.var(values1) == 0 or np.var(values2) == 0:
            return [None, df1, df2]
        test_tested_functions = {
            't-test' : (ttest_ind, np.mean),
            'Kruskal-Wallis' : (kruskal, np.median),
        }
        test_function = test_tested_functions[test][0]
        tested_function = test_tested_functions[test][1]
        if test == 't-test':
            s, p = test_function(values1, values2, equal_var=False, nan_policy='omit')
        if test == 'Kruskal-Wallis':
            s, p = test_function(values1, values2, nan_policy='omit')
        difference = tested_function(values2) - tested_function(values1)
        if tested_function(values1) != 0:
            multiplicative_effect = tested_function(values2) / tested_function(values1) # check zero
        else:
            multiplicative_effect = 'NaN'
        sign = FrequencyAnalysisIntegrator.sign(difference)
        extreme_sample1, extreme_value1 = FrequencyAnalysisIntegrator.get_extremum(df1, -1*sign, column)
        extreme_sample2, extreme_value2 = FrequencyAnalysisIntegrator.get_extremum(df2, sign, column)
        row = {
            'outcome 1' : outcome1,
            'outcome 2' : outcome2,
            'phenotype' : phenotype_name,
            'compartment' : compartment,
            'tested value 1' : tested_function(values1),
            'tested value 2' : tested_function(values2),
            'test' : test,
            'p-value' : p,
            'absolute effect' : abs(difference),
            'multiplicative effect' : str(multiplicative_effect),
            'effect sign' : sign,
            'p-value < 0.01' : p < 0.01,
            'extreme sample 1' : extreme_sample1,
            'extreme sample 2' : extreme_sample2,
            'extreme value 1' : extreme_value1,
            'extreme value 2' : extreme_value2,
        }
        return [row, df1, df2]

    def export_results(self, frequency_tests):
        """
        Writes the result of the statistical tests to file, in order of statistical
        significance.

        :param frequency_tests: Table of test results.
            See :py:meth:`get_test_result_row`. 
        :type frequency_tests: pandas.DataFrame
        """
        frequency_tests.to_csv(join(self.output_path, self.computational_design.get_stats_tests_file()), index=False)

    def get_dataframe_from_db(self, table_name):
        """
        Retrieves whole dataframe of a given table from the pipeline-specific database.

        :param table_name: Name of a table in the database described in the
            computational design object.
        :type table_name: str

        :return: The whole table, in dataframe form.
        :rtype: pandas.DataFrame
        """
        if table_name == 'cells':
            columns = ['id'] + [entry[0] for entry in self.computational_design.get_cells_header()]
        elif table_name == 'fov_lookup':
            columns = ['id'] + [entry[0] for entry in self.computational_design.get_fov_lookup_header()]
        else:
            logger.error('Table %s is not in the schema.', table_name)
            return None

        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            rows = m.execute('SELECT * FROM ' + table_name)

        df = pd.DataFrame(rows, columns=columns)
        if table_name == 'cells':
            df.rename(columns=self.get_column_renaming('cells'), inplace=True)
        return df

    def get_column_renaming(self, table_name):
        """
        :param table_name: Name of a table in the database described in the
            computational design object.
        :type table_name: str

        :return: ``renaming``. A dictionary that provided a renaming of column names
            from SQL-appropriate escaped versions to their more human-readable versions.
        :rtype: dict
        """
        renaming = {}
        if table_name == 'cells':
            h1 = self.computational_design.get_cells_header_variable_portion(style='sql')
            h2 = self.computational_design.get_cells_header_variable_portion(style='readable')
            renaming = {h1[i][0] : h2[i][0] for i in range(len(h1))}
        return renaming

    @staticmethod
    def get_extremum(df, sign, column):
        """
        :param df: Table with sample-level (i.e. summarized) feature values.
        :type df: pandas.DataFrame

        :param sign: Either 1 or -1. Whether to return the extremely large value (in
            case 1) or the extremely small value (in case -1).
        :type sign: int

        :param column: The name of the column with numerical data to consider.
        :type column: str

        :return:
            - ``extreme_sample``. Sample identifier of the extreme sample.
            - ``extreme_value``. The numeric extreme value.
        :rtype: str, float
        """
        values_column = column
        df_sorted = df.sort_values(by=values_column, ascending=True if sign==-1 else False)
        if df_sorted.shape[0] == 0:
            return ['none', -1]
        extreme_sample = list(df_sorted['sample_identifier'])[0]
        extreme_value = float(list(df_sorted[values_column])[0])
        return [extreme_sample, extreme_value]

    def get_fov_lookup_dict(self):
        """
        :return: The lookup between pairs (sample identifier, fov index integer) and the
            string descriptor of the FOV.
        :rtype: dict
        """
        if self._fov_lookup_dict is None:
            fov_lookup = self.get_dataframe_from_db('fov_lookup')
            self._fov_lookup_dict = {
                (row['sample_identifier'], row['fov_index']) : row['fov_string']
                for i, row in fov_lookup.iterrows()
            }
        return self._fov_lookup_dict

    @staticmethod
    def sign(value):
        return 1 if value >=0 else -1
