import os
from os.path import exists, join
from os import mkdir
import sqlite3
import re
import math
from warnings import simplefilter

import pandas as pd
import numpy as np
import ot
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import ClusterWarning
simplefilter('ignore', ClusterWarning)

from ...environment.database_context_utility import WaitingDatabaseContextManager
from ...environment.log_formats import colorized_logger

logger = colorized_logger(__name__)


class DiffusionAnalysisIntegrator:
    min_probability_value = -0.001
    max_probability_value = 0.05
    histogram_resolution = 50

    def __init__(self,
        jobs_paths: JobsPaths=None,
        dataset_settings: DatasetSettings=None,
        computational_design=None,
    ):
        self.output_path = jobs_paths.output_path
        self.dataset_settings = dataset_settings
        self.computational_design = computational_design

    def get_dataframe_from_db(self, table_name):
        if table_name == 'transition_probabilities':
            columns = ['id'] + self.computational_design.get_probabilities_table_header()
        elif table_name == 'job_metadata':
            columns=['id'] + self.computational_design.get_job_metadata_header()
        else:
            logger.error('Table %s is not in the schema.', table_name)
            return None

        uri = join(self.output_path, self.computational_design.get_database_uri())
        with WaitingDatabaseContextManager(uri) as m:
            rows = m.execute('SELECT * FROM ' + table_name)

        df = pd.DataFrame(rows, columns=columns)
        return df

    def create_bins(self, data, min_value, max_value, steps):
        frequencies = [0 for i in range(steps)]
        step = (max_value - min_value ) / steps
        for value in data:
            bin_index = math.floor((value - min_value) / step)
            if bin_index >= 0 and bin_index < len(frequencies):
                frequencies[bin_index] = frequencies[bin_index] + 1
        total = sum(frequencies)
        return [f/total for f in frequencies]

    def guess_round(self, t):
        r = round(t, 3)
        if abs(t - r) < 0.00001:
            return r
        else:
            return t

    def camel_case(self, s):
        return re.sub('_', ' ', s[0].upper() + s[1:len(s)].lower())

    def calculate(self):
        probabilities = self.get_dataframe_from_db('transition_probabilities')
        job_metadata = self.get_dataframe_from_db('job_metadata')
        logger.info('probabilities.shape: %s', probabilities.shape)
        logger.info('average transition probability: %s', np.mean(probabilities['transition_probability']))
        if not exists(self.output_path):
            mkdir(self.output_path)
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
                logger.info('Generating figures for %s in %s case.', marker, distance_type)
                self.generate_figures(marker, distance_type, outcomes_dict, t_values, grouped, ungrouped)
        logger.info('Done generating figures.')

    def generate_figures(self, marker, distance_type, outcomes_dict, t_values, grouped, ungrouped):
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
