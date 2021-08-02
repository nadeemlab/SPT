import os
from os.path import exists, join
from os import mkdir
import sqlite3
import re
import math
from warnings import simplefilter
import itertools

import pandas as pd
import numpy as np
import ot
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind, kruskal
from scipy.cluster.hierarchy import ClusterWarning
simplefilter('ignore', ClusterWarning)

from ...environment.settings_wrappers import JobsPaths, DatasetSettings
from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DiffusionAnalysisIntegrator:
    min_probability_value = -0.001
    max_probability_value = 0.05
    histogram_resolution = 50

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
                Design object providing metadata specific to the diffusion pipeline.
        """
        self.output_path = jobs_paths.output_path
        self.dataset_settings = dataset_settings
        self.computational_design = computational_design

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
        if table_name == 'transition_probabilities':
            columns = ['id'] + self.computational_design.get_probabilities_table_header()
        elif table_name == 'job_metadata':
            columns = ['id'] + self.computational_design.get_job_metadata_header()
        elif table_name == 'transition_probabilities_summarized':
            columns = ['id'] + [c[0] for c in self.computational_design.get_transition_probabilities_summarized_header()]
        else:
            logger.error('Table %s is not in the schema.', table_name)
            return None

        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            rows = m.execute('SELECT * FROM ' + table_name)

        df = pd.DataFrame(rows, columns=columns)
        return df

    def create_bins(self, data, min_value, max_value, steps):
        """
        Convenience function to support rasterization of probability distribution known
        through samples.

        Args:
            data (list):
                The samples.
            min_value (float):
                Lower cutoff for lowest bin.
            max_value (float):
                Upper cutoff for highest bin.
            steps (int):
                Number of bins to create.

        Returns:
            list:
                The discrete probability density function supported on the ordered bin set.
        """
        frequencies = [0 for i in range(steps)]
        step = (max_value - min_value ) / steps
        for value in data:
            bin_index = math.floor((value - min_value) / step)
            if bin_index >= 0 and bin_index < len(frequencies):
                frequencies[bin_index] = frequencies[bin_index] + 1
        total = sum(frequencies)
        return [f/total for f in frequencies]

    def guess_round(self, t):
        """
        After passing through conversions in multiple systems (e.g. string
        serialization, saving to a database), exact fixed-precision numbers represented
        as floats can accumulate small errors. This function guesses the original
        fixed-precision number.

        Args:
            t (float):
                A number very close to a decimal number with few decimals.

        Returns:
            float:
                The nearest decimal number with just a few decimals.
        """
        r = round(t, 3)
        if abs(t - r) < 0.00001:
            return r
        else:
            return t

    def camel_case(self, s):
        """
        Args:
            s (str):
                Possibly snake case string.

        Returns:
            str:
                (Almost) camel case version.
        """
        return re.sub('_', ' ', s[0].upper() + s[1:len(s)].lower())

    def calculate(self):
        """
        Gathers computed values into different contextual cases, then delegates to
        ``generate_figures``.
        """
        probabilities = self.get_dataframe_from_db('transition_probabilities')
        job_metadata = self.get_dataframe_from_db('job_metadata')
        logger.info('Value of probabilities.shape: %s', probabilities.shape)
        logger.info('Average transition probability: %s', np.mean(probabilities['transition_probability']))
        self.initialize_output_tables()
        temporal_offsets = probabilities['temporal_offset']
        temporal_offsets = temporal_offsets[~np.isnan(temporal_offsets)]
        t_values = sorted(list(set(temporal_offsets)))
        outcomes_df = pd.read_csv(self.dataset_settings.outcomes_file, sep='\t')
        columns = outcomes_df.columns
        outcomes_dict = {
            row[columns[0]]: row[columns[1]] for i, row in outcomes_df.iterrows()
        }
        markers = sorted(list(set(probabilities['marker'])))
        distance_types = sorted(list(set(probabilities['distance_type'])))
        job_metadata[['job_activity_id']] = job_metadata[['job_activity_id']].apply(pd.to_numeric)
        for marker in markers:
            jobs = job_metadata[(job_metadata['Job status'] == 'COMPLETE') & (job_metadata['Regional compartment'] == 'nontumor')]
            joined = pd.merge(probabilities, jobs, left_on='job_activity_id', right_on='job_activity_id', how='left', suffixes=['', '_right'])
            joined = joined[joined['marker'] == marker]
            for distance_type in distance_types:
                ungrouped = joined[joined['distance_type'] == distance_type]
                grouped = ungrouped.groupby('Sample ID')
                self.record_summary_of_values(marker, distance_type, outcomes_dict, t_values, grouped)
                logger.info('Generating figures for %s in %s case.', marker, distance_type)
                self.generate_figures(marker, distance_type, outcomes_dict, t_values, grouped, ungrouped)
        logger.info('Done generating figures.')
        self.do_outcome_tests()
        logger.info('Done with statistical tests.')

    def initialize_output_tables(self):
        table_name = 'transition_probabilities_summarized'
        schema = self.computational_design.get_transition_probabilities_summarized_header()
        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            m.execute_commit('DROP TABLE IF EXISTS ' + table_name + ' ;')
            cmd = ' '.join([
                'CREATE TABLE',
                table_name,
                '(',
                'id INTEGER PRIMARY KEY AUTOINCREMENT,',
                ', '.join([key + ' ' + data_type for key, data_type in schema]),
                ');',
            ])
            m.execute_commit(cmd)

    def record_summary_of_values(self, marker, distance_type, outcomes_dict, t_values, grouped):
        table_name = 'transition_probabilities_summarized'
        schema = self.computational_design.get_transition_probabilities_summarized_header()
        process_value = {
            'TEXT' : (lambda val: '"' + str(val) + '"'),
            'NUMERIC' : (lambda val: str(val)),
            'INTEGER' : (lambda val: str(val)),
        }
        column_names = [row[0] for row in schema]
        data_types = [row[1] for row in schema]
        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            for sample_id, df in grouped:
                if sample_id in outcomes_dict:
                    outcome = outcomes_dict[sample_id]
                else:
                    logger.warning('Skipping sample %s due to unknown outcome.', sample_id)
                    continue
                if df.shape[0] == 0:
                    logger.warning('Skipping sample %s due to no associated transition probability values.', sample_id)
                    continue
                for t in t_values:
                    temporal_offset = self.guess_round(t)
                    transition_probabilities = list(df[df['temporal_offset'] == t]['transition_probability'])
                    mean_value = np.mean(transition_probabilities)
                    median_value = np.median(transition_probabilities)
                    variance_value = np.var(transition_probabilities)
                    values = [
                        sample_id,
                        outcome,
                        marker,
                        distance_type,
                        temporal_offset,
                        mean_value,
                        median_value,
                        variance_value,
                    ]
                    processed_values = [process_value[data_types[i]](values[i]) for i in range(len(values))]
                    cmd = ' '.join([
                        'INSERT INTO',
                        table_name,
                        '(' + ', '.join(column_names) + ')',
                        'VALUES',
                        '( ' + ' , '.join(processed_values) + ' );'
                    ])
                    m.execute(cmd)
                m.commit()

    def sign(self, value):
        return 1 if value >=0 else -1

    def get_extremum(self, df, sign, statistic):
        """
        Args:
            df (pandas.DataFrame):
                Dataframe with sample-level (i.e. summarized) transition probability
                values, summarized according to 'statistic'.
            sign (int):
                Either 1 or -1. Whether to return the extremely large value (in case of
                1) or the extremely small value (in case of -1).
            statistic (str):
                Currently either 'mean', 'median', or 'variance'.

        Returns:
            list:
                A pair, the extreme sample ID string and the extreme value.
        """
        values_column = statistic + '_transition_probability'
        df_sorted = df.sort_values(by=values_column, ascending=True if sign==-1 else False)
        extreme_sample = list(df_sorted['Sample_ID'])[0]
        extreme_value = float(list(df_sorted[values_column])[0])
        return [extreme_sample, extreme_value]

    def do_outcome_tests(self):
        df = self.get_dataframe_from_db('transition_probabilities_summarized')
        df = df[df['Diffusion_kernel_distance_type'] == 'EUCLIDEAN']

        outcomes = sorted(list(set(df['Outcome_assignment'])))
        phenotypes = sorted(list(set(df['Marker'])))
        t_values = sorted(list(set(df['Temporal_offset'])))
        statistics = ['Mean', 'Median', 'Variance']

        rows = []
        for outcome1, outcome2 in itertools.combinations(outcomes, 2):
            for phenotype in phenotypes:
                for t in t_values:
                        for statistic in statistics:
                            df1 = df[(df['Temporal_offset'] == t) & (df['Outcome_assignment'] == outcome1) & (df['Marker'] == phenotype)]
                            df2 = df[(df['Temporal_offset'] == t) & (df['Outcome_assignment'] == outcome2) & (df['Marker'] == phenotype)]
                            values1 = list(df1[statistic + '_transition_probability'])
                            values2 = list(df2[statistic + '_transition_probability'])

                            if np.var(values1) == 0 or np.var(values2) == 0:
                                continue

                            s, p_ttest = ttest_ind(values1, values2, equal_var=False, nan_policy='omit')
                            mean_difference = np.mean(values2) - np.mean(values1)
                            multiplicative_effect = np.mean(values2) / np.mean(values1)

                            sign = self.sign(mean_difference)
                            extreme_sample1, extreme_value1 = self.get_extremum(df1, -1*sign, statistic)
                            extreme_sample2, extreme_value2 = self.get_extremum(df2, sign, statistic)

                            rows.append({
                                'outcome 1' : outcome1,
                                'outcome 2' : outcome2,
                                'phenotype' : phenotype,
                                'temporal offset' : t,
                                'tested value 1' : np.mean(values1),
                                'tested value 2' : np.mean(values2),
                                'first-summarization statistic tested' : statistic.lower(),
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
                            extreme_sample1, extreme_value1 = self.get_extremum(df1, -1*sign, statistic)
                            extreme_sample2, extreme_value2 = self.get_extremum(df2, sign, statistic)

                            rows.append({
                                'outcome 1' : outcome1,
                                'outcome 2' : outcome2,
                                'phenotype' : phenotype,
                                'temporal offset' : t,
                                'tested value 1' : np.median(values1),
                                'tested value 2' : np.median(values2),
                                'first-summarization statistic tested' : statistic.lower(),
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
        if len(rows) == 0:
            logger.info('No non-trivial tests to perform. Probably too few values.')
            return None
        diffusion_value_tests = pd.DataFrame(rows)
        sort_order = ['outcome 1', 'outcome 2', 'p-value < 0.01', 'p-value']
        ascending = [True, True, False, True]
        diffusion_value_tests.sort_values(by=sort_order, ascending=ascending, inplace=True)
        diffusion_value_tests.to_csv(join(self.output_path, 'diffusion_distance_tests.csv'), index=False)


    def generate_figures(self, marker, distance_type, outcomes_dict, t_values, grouped, ungrouped):
        """
        Write figures to file that constrast distributions of computed values across
        outcome pairs, for a given marker (elementary phenotype) and distance type
        (underlying point-set metric).

        Args:
            marker (str):
                An elementary phenotype name for the phenotype of consideration.
            distance_type (DistanceTypes):
                The point-set metric type with respect to which diffusion was
                calculated.
            outcomes_dict (dict):
                The outcome / label assignment dictionary, whose keys are sample
                identifiers.
            t_values (list):
                The ordered list (non-repeating) of possible temporal offset values,
                those recorded alongside the probability values, denoting the duration
                of run time for the Markov process.
            grouped:
                A version of the "ungrouped" pandas.DataFrame, grouped by sample
                identifier value.
            ungrouped:
                The pandas.DataFrame of recorded transition probability values,
                pre-restricted to the given marker and distance type.
        """
        keys = sorted([sample_id for sample_id, df in grouped])
        outcomes = [outcomes_dict[sample_id] if sample_id in outcomes_dict.keys() else 'unknown' for sample_id in keys]
        unique_outcomes = np.unique(outcomes)
        colors = ['green', 'skyblue', 'red', 'white','purple','blue','orange','yellow']
        colors = colors[0:len(unique_outcomes)]
        color_dict=dict(zip(unique_outcomes, np.array(colors)))
        row_colors = [color_dict[outcome] for outcome in outcomes]

        p = join(self.output_path, distance_type)
        if not exists(p):
            mkdir(p)

        pdf = PdfPages(join(p, 'figure_' + marker + '.pdf'))
        for i, t in enumerate(t_values):
            fig, axs = plt.subplots(1, 2, figsize=(12, 6))
            distributions_t = {}
            for sample_id, df in grouped:
                data = list(df[df['temporal_offset'] == t]['transition_probability'])
                if sample_id in outcomes_dict:
                    outcome = outcomes_dict[sample_id]
                else:
                    outcome = 'unknown'
                if np.var(data) == 0:
                    continue
                g = sns.kdeplot(data, label=outcome, linewidth = 0.5, color=color_dict[outcome], log_scale=(False,True), ax=axs[0])
                distributions_t[sample_id] = self.create_bins(
                    data,
                    DiffusionAnalysisIntegrator.min_probability_value,
                    DiffusionAnalysisIntegrator.max_probability_value,
                    DiffusionAnalysisIntegrator.histogram_resolution,
                )

            for o in np.unique(outcomes):
                if o == 'unknown':
                    continue
                o_mask = [sample_id in outcomes_dict and outcomes_dict[sample_id] == o for sample_id in ungrouped['Sample ID']]
                data = list(ungrouped[(ungrouped['temporal_offset'] == t) & (o_mask)]['transition_probability'])
                if np.var(data) == 0:
                    continue
                g = sns.kdeplot(data, label=o, linewidth = 2.0, color=color_dict[o], log_scale=(False,True), ax=axs[1])

            for j in [0, 1]:
                axs[j].set_xlim(
                    DiffusionAnalysisIntegrator.min_probability_value,
                    DiffusionAnalysisIntegrator.max_probability_value,
                )
                axs[j].set_ylim(0.1, 1000)
                axs[j].set_xlabel('point-to-point diffusion probability after time t=' + str(self.guess_round(t)))
                axs[j].set_ylabel('density')

            axs[1].legend()

            context_title = ', '.join([
                'Regional compartment: Nontumor',
                'Distance type: ' + self.camel_case(distance_type),
                'Marker: ' + marker,
                't=' + str(self.guess_round(t)),
            ])
            fig.suptitle(context_title)

            pdf.savefig(fig)
            plt.close(fig=fig)

            keys = sorted(distributions_t.keys())
            distributions = [distributions_t[key] for key in keys]
            distributions_array = np.array(distributions)
            shape = distributions_array.shape
            if shape[0] <= 1 or shape[1] <= 1:
                logger.warning('No distribution data in case %s, %s, %s', marker, t, distance_type)
                continue
            probabilities = ot.dist(distributions_array)
            g = sns.clustermap(probabilities, cbar_pos=None, row_colors=row_colors, dendrogram_ratio=0.1, xticklabels=[], yticklabels=[])
            g.ax_col_dendrogram.set_title('Optimal transport distance between distributions of diffusion probability values (sample-by-sample)')
            g.fig.subplots_adjust(top=.9)
            g.ax_heatmap.tick_params(right=False, bottom=False)
            pdf.savefig(g.fig)
            plt.close(fig=g.fig)

        pdf.close()
