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

logger = colorized_logger(__name__)


class FrequencyAnalysisIntegrator:
    def __init__(
        self,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
    ):
        """
        Args:
            jobs_paths (JobsPaths):
                Convenience bundle of filesystem paths pertinent to a particular run at the job level.
            dataset_settings (DatasetSettings):
                Convenience bundle of paths to input dataset files.
            computational_design:
                Design object providing metadata specific to the front proximity pipeline.
        """
        self.output_path = jobs_paths.output_path
        self.outcomes_file = dataset_settings.outcomes_file
        self.computational_design = computational_design
        self.frequency_tests = None

    def calculate(self):
        """
        Performs statistical comparison tests and writes results.
        """
        logger.info('Starting stats.')
        frequency_tests = self.do_outcome_tests()
        if frequency_tests is not None:
            self.export_results(frequency_tests)
        logger.info('Done exporting stats.')

    def do_outcome_tests(self):
        cells = self.get_dataframe_from_db('cells')
        phenotype_columns = [column for column in cells.columns if re.search('membership$', str(column))]

        for phenotype in phenotype_columns:
            mask = (cells[phenotype] == 1)
            cells.loc[mask, phenotype] = cells['cell_area']

        fov_lookup = self.get_dataframe_from_db('fov_lookup')
        fov_lookup_dict = {(row['sample_identifier'], row['fov_index']) : row['fov_string'] for i, row in fov_lookup.iterrows()}
        example_sample_identifier = 'S12-35339'
        example_fov_string = 'S12-35339 Colon P20 CD3, Foxp1, PDL1, ICOS, CD8, panCK+CK7+CAM5.2_[52469,12927]_component_data.tif'
        example_fov_index = [fov_index for (s, fov_index), fov in fov_lookup_dict.items() if fov == example_fov_string][0]
        example_phenotype = 'ICOS+ cell area sum'
        logger.debug('FOV %s, i.e. "%s".', example_fov_index, example_fov_string)
        sample_focused_cells = cells[(cells['fov_index'] == example_fov_index)].sort_values(by='cell_area')
        logger.debug('Other values of fov_index: %s', list(cells['fov_index'])[0:5])
        logger.debug(fov_focused_cells)
        logger.debug('(Table has %s rows.)', fov_focused_cells.shape[0])

        sum_columns = {p : re.sub('membership', 'cell area sum', p) for p in phenotype_columns}
        summed_cell_areas = cells.groupby(['sample_identifier', 'fov_index', 'compartment'], as_index=False).agg(
            **{
                column : pd.NamedAgg(column=p, aggfunc='sum') for p, column in sum_columns.items()
            },
            **{
                'outcome_assignment' : pd.NamedAgg(column='outcome_assignment', aggfunc=lambda x:list(x)[0]),
            }
        )

        example_compartment = list(cells['compartment'])[0]
        logger.debug('Logging cell areas of phenotype "%s", in %s.', example_phenotype, example_compartment)
        a = summed_cell_areas
        example_areas = [
            (fov_lookup_dict[(r['sample_identifier'], r['fov_index'])], r[example_phenotype]) for i, r in a.iterrows() if r['compartment'] == example_compartment
        ]
        string_rep = '\n'.join([' '.join([str(elt) for elt in row]) for row in example_areas])
        logger.debug('FOV cell areas: %s', string_rep)

        average_columns = {sum_columns[p] : re.sub('membership', 'cell area average per FOV', p) for p in phenotype_columns}
        averaged_cell_areas = summed_cell_areas.groupby(['sample_identifier', 'compartment'], as_index=False).agg(
            **{
                column : pd.NamedAgg(column=p, aggfunc='mean') for p, column in average_columns.items()
            },
            **{
                'outcome_assignment' : pd.NamedAgg(column='outcome_assignment', aggfunc=lambda x:list(x)[0]),
            }
        )

        outcomes = sorted(list(set(cells['outcome_assignment'])))
        rows = []
        phenotype_names = [re.sub(' membership', '', column) for column in phenotype_columns]

        debug_details = 3
        for compartment, df in averaged_cell_areas.groupby(['compartment']):
            for outcome1, outcome2 in itertools.combinations(outcomes, 2):
                for name in phenotype_names:
                    column = name + ' cell area average per FOV'
                    df1 = df[df['outcome_assignment'] == outcome1][['sample_identifier', column]]
                    df2 = df[df['outcome_assignment'] == outcome2][['sample_identifier', column]]
                    values1 = list(df1[column])
                    values2 = list(df2[column])

                    if np.var(values1) == 0 or np.var(values2) == 0:
                        continue

                    s, p_ttest = ttest_ind(values1, values2, equal_var=False, nan_policy='omit')
                    mean_difference = np.mean(values2) - np.mean(values1)
                    multiplicative_effect = np.mean(values2) / np.mean(values1)

                    sign = self.sign(mean_difference)
                    extreme_sample1, extreme_value1 = self.get_extremum(df1, -1*sign, column)
                    extreme_sample2, extreme_value2 = self.get_extremum(df2, sign, column)

                    rows.append({
                        'outcome 1' : outcome1,
                        'outcome 2' : outcome2,
                        'phenotype' : name,
                        'compartment' : compartment,
                        'tested value 1' : np.mean(values1),
                        'tested value 2' : np.mean(values2),
                        'test' : 't-test',
                        'p-value' : p_ttest,
                        'absolute effect' : abs(mean_difference),
                        'effect sign' : sign,
                        'p-value < 0.01' : p_ttest < 0.01,
                        'extreme sample 1' : extreme_sample1,
                        'extreme sample 2' : extreme_sample2,
                        'extreme value 1' : extreme_value1,
                        'extreme value 2' : extreme_value2,
                    })

                    s, p_kruskal = kruskal(values1, values2, nan_policy='omit')
                    median_difference = np.median(values2) - np.median(values1)
                    multiplicative_effect = np.median(values2) / np.median(values1)

                    sign = self.sign(median_difference)
                    extreme_sample1, extreme_value1 = self.get_extremum(df1, -1*sign, column)
                    extreme_sample2, extreme_value2 = self.get_extremum(df2, sign, column)

                    rows.append({
                        'outcome 1' : outcome1,
                        'outcome 2' : outcome2,
                        'phenotype' : name,
                        'compartment' : compartment,
                        'tested value 1' : np.median(values1),
                        'tested value 2' : np.median(values2),
                        'test' : 'Kruskal-Wallis',
                        'p-value' : p_kruskal,
                        'absolute effect' : abs(median_difference),
                        'effect sign' : sign,
                        'p-value < 0.01' : p_kruskal < 0.01,
                        'extreme sample 1' : extreme_sample1,
                        'extreme sample 2' : extreme_sample2,
                        'extreme value 1' : extreme_value1,
                        'extreme value 2' : extreme_value2,
                    })

                    if debug_details > 0:
                        logger.debug('Logging details in selected statistical test case %s.', debug_details)
                        logger.debug('Outcome pair: %s, %s', outcome1, outcome2)
                        logger.debug('Compartment: %s', compartment)
                        logger.debug('Phenotype: %s', name)
                        dict1 = {row['sample_identifier'] : row[column] for i, row in df1.iterrows()}
                        logger.debug('Cell areas summed over FOVs 1: %s', dict1)
                        dict2 = {row['sample_identifier'] : row[column] for i, row in df2.iterrows()}
                        logger.debug('Cell areas summed over FOVs 2: %s', dict2)
                        logger.debug('Number of values 1: %s', len(dict1))
                        logger.debug('Number of values 2: %s', len(dict2))
                        debug_details -= 1

        if len(rows) == 0:
            logger.info('No non-trivial tests to perform. Probably too few values.')
            return None
        frequency_tests = pd.DataFrame(rows)
        sort_order = ['outcome 1', 'outcome 2', 'p-value < 0.01', 'p-value']
        ascending = [True, True, False, True]
        frequency_tests.sort_values(by=sort_order, ascending=ascending, inplace=True)
        return frequency_tests

    def export_results(self, frequency_tests):
        """
        Writes the result of the statistical tests to file, in order of statistical
        significance.

        Args:
            frequency_tests (pandas.DataFrame):
                Tabular form of test results.
        """
        frequency_tests.to_csv(join(self.output_path, self.computational_design.get_stats_tests_file()), index=False)

    def get_dataframe_from_db(self, table_name):
        """
        Retrieves whole dataframe of a given table from the pipeline-specific database.

        Args:
            table_name (str):
                Name of table in database furnished by computational design.

        Returns:
            pandas.DataFrame:
                The whole table, in dataframe form.
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
        renaming = {}
        if table_name == 'cells':
            h1 = self.computational_design.get_cells_header_variable_portion(style='sql')
            h2 = self.computational_design.get_cells_header_variable_portion(style='readable')
            renaming = {h1[i][0] : h2[i][0] for i in range(len(h1))}
        return renaming

    def get_extremum(self, df, sign, column):
        """
        Args:
            df (pandas.DataFrame):
                Dataframe with sample-level (i.e. summarized) transition probability
                values, summarized according to 'statistic'.
            sign (int):
                Either 1 or -1. Whether to return the extremely large value (in case of
                1) or the extremely small value (in case of -1).
            column (str):
                To consider.

        Returns:
            list:
                A pair, the extreme sample ID string and the extreme value.
        """
        values_column = column
        df_sorted = df.sort_values(by=values_column, ascending=True if sign==-1 else False)
        if df_sorted.shape[0] == 0:
            return ['none', -1]
        extreme_sample = list(df_sorted['sample_identifier'])[0]
        extreme_value = float(list(df_sorted[values_column])[0])
        return [extreme_sample, extreme_value]

    def sign(self, value):
        return 1 if value >=0 else -1
