#!/usr/bin/env python3
"""
This application allows the user to select a field of view in a given image, and
a pair of region classes, and then shows a plot of the distribution of the
distance-to-front values by phenotype.

If outcome data is provided, outcome-specific distribution plots are available.
"""
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

from ...workflows.front_proximity.computational_design import FrontProximityDesign
from ...environment.log_formats import colorized_logger
logger = colorized_logger(__name__)


class FrontProximityViz:
    """
    The main class of the front proximity visualization application.
    """
    def __init__(self, distances_db_uri=None, drop_compartments=[]):
        """
        :param distances_db_uri: The URI of the database containing the output of the
            front proximity pipeline.
        :type distances_db_uri: str

        :param drop_compartments: A list of compartments for which the corresponding
            cells should be dropped from the table before plots are attempted. Note that
            only 2 compartments are allowed in the table, so you may need to use this
            parameter to drop any excess beyond 2.
        :type drop_compartments: list
        """
        dataframe = self.retrieve_distances_dataframe(
            uri=distances_db_uri,
            drop_compartments=drop_compartments,
        )

        logger.info('Creating indices into the figure trace groups.')
        tuples_duplicated = [
            (row['sample_identifier'], row['fov_index']) for i, row in dataframe.iterrows()
        ]
        case_identifiers = sorted(list(set(tuples_duplicated)))

        compartment_pairs = [
            tuple(sorted([row['compartment'], row['other_compartment']])) for i, row in dataframe.iterrows()
        ]
        compartment_pairs = list(set(compartment_pairs))
        if len(compartment_pairs) > 1:
            logger.error('Encountered more than 1 possible compartment pair: %s', compartment_pairs)
            return
        compartment_pair = compartment_pairs[0]

        all_hist_data1 = []
        all_group_labels1 = []
        sizes1 = []

        all_hist_data2 = []
        all_group_labels2 = []
        sizes2 = []

        logger.info('Preparing data in groups exactly as needed by the figure factory.')
        count = 1
        for sample_identifier, fov_index in case_identifiers:
            logger.debug('Prepared case %s/%s.', count, len(case_identifiers))
            count += 1
            hist_data1, group_labels1 = self.get_distances_along(
                dataframe,
                sample_identifier=sample_identifier,
                fov_index=fov_index,
                compartment=compartment_pair[0],
                other_compartment=compartment_pair[1],
            )
            hist_data2, group_labels2 = self.get_distances_along(
                dataframe,
                sample_identifier=sample_identifier,
                fov_index=fov_index,
                compartment=compartment_pair[1],
                other_compartment=compartment_pair[0],
            )

            all_hist_data1 = all_hist_data1 + hist_data1
            all_group_labels1 = all_group_labels1 + group_labels1
            sizes1.append(len(group_labels1))

            all_hist_data2 = all_hist_data2 + hist_data2
            all_group_labels2 = all_group_labels2 + group_labels2
            sizes2.append(len(group_labels2))

        logger.info('Creating distplots.')
        fig1 = ff.create_distplot(
            hist_data=all_hist_data1,
            group_labels=all_group_labels1,
            bin_size=25,
        )
        fig2 = ff.create_distplot(
            hist_data=all_hist_data2,
            group_labels=all_group_labels2,
            bin_size=25,
        )

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=(
                compartment_pair[0] + ' cells, distance to ' + compartment_pair[1] + ' region',
                compartment_pair[1] + ' cells, distance to ' + compartment_pair[0] + ' region',
            ),
        )

        logger.info('Copying distplot data into subplottable figure.')
        case_relevant_indices = {case : [] for case in case_identifiers}
        offset = 0
        count = 0
        for i, size in enumerate(sizes1):
            case = case_identifiers[i]
            for j in range(size):
                fig.add_trace(
                    go.Histogram(fig1['data'][offset + j], nbinsx=20, visible=(i == 0)),
                    row=1, col=1,
                )
                case_relevant_indices[case].append(count)
                count += 1
                fig.add_trace(
                    go.Scatter(fig1['data'][offset + j + sum(sizes1)], line=dict(width=0.5), visible=(i == 0)),
                    row=1, col=1,
                )
                case_relevant_indices[case].append(count)
                count += 1

            offset += size

        offset = 0
        for i, size in enumerate(sizes2):
            case = case_identifiers[i]
            for j in range(size):
                fig.add_trace(
                    go.Histogram(fig2['data'][offset + j], nbinsx=20, visible=(i == 0)),
                    row=1, col=2,
                )
                case_relevant_indices[case].append(count)
                count += 1
                fig.add_trace(
                    go.Scatter(fig2['data'][offset + j + sum(sizes2)], line=dict(width=0.5), visible=(i == 0)),
                    row=1, col=2,
                )
                case_relevant_indices[case].append(count)
                count += 1

            offset += size

        logger.info('Adding combobox and update-on-select mechanism.')
        indicator_function = {
            case : [(c in case_relevant_indices[case]) for c in range(count)] for case in case_identifiers
        }

        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=['visible', indicator_function[case]],
                            label=''.join([
                                'Sample ID: ',
                                case[0],
                                '   ',
                                'FOV: ',
                                str(case[1]),
                            ]),
                            method='restyle',
                        ) for case in case_identifiers
                    ]),
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=False,
                    x=0.1,
                    xanchor="right",
                    y=1.2,
                    yanchor="top",
                ),
            ]
        )

        self.fig = fig

    def get_distances_along(self,
        dataframe,
        sample_identifier=None,
        fov_index=None,
        compartment=None,
        other_compartment=None,
    ):
        """
        :param sample_identifier: A sample identifier value.
        :type sample_identifier: str

        :param fov_index: A field of view index value.
        :type fov_index: int

        :param compartment: The compartment whose cells will be the domain of the
            distance values retrieved.
        :type compartment: str

        :param other_compartment: The other compartment, whose boundary or front with
            the main compartment is considered.
        :type other_compartment: str

        :return: The pair [histogram data, group labels] as required for a plotly
            distplot, for the distance data restricted to the given context's value.
        :rtype: list
        """
        df = dataframe[
            (dataframe['sample_identifier'] == sample_identifier) &
            (dataframe['fov_index'] == fov_index) &
            (dataframe['compartment'] == compartment) &
            (dataframe['other_compartment'] == other_compartment)
        ]
        grouped = df.groupby('phenotype')
        hist_data_labels = [(list(set(g['distance_to_front_in_pixels'])), key + ' ' + compartment) for key, g in grouped] # A dangerous use of "set"; try to fix instead the upstream subsampling issue
        group_labels = [row[1] for row in hist_data_labels if len(row[0]) > 2]
        hist_data = [row[0] for row in hist_data_labels if len(row[0]) > 2]
        return [hist_data, group_labels]

    def retrieve_distances_dataframe(self, uri: str=None, drop_compartments=[]):
        """
        :param uri: The URI of the database containing the output of the front proximity
            pipeline.
        :type uri: str

        :param drop_compartments: A list of compartments for which the corresponding
            cells should be dropped from the table before plots are attempted.
        :type drop_compartments: list

        :return: The table of distance-to-front values, by sample, field of view, and
            compartment pair.
        :rtype: pandas.DataFrame
        """
        connection = sqlite3.connect(uri)
        table_name='cell_front_distances'
        logger.info('Reading in dataframe from %s .', uri)
        df = pd.read_sql_query('SELECT * from ' + table_name, connection)
        logger.info('Finished reading.')
        connection.close()

        if len(drop_compartments) > 0:
            c0 = drop_compartments[0]
            droppable = (df['compartment'] == c0) | (df['other_compartment'] == c0)
            if len(drop_compartments) > 1:
                for c in drop_compartments[1:-1]:
                    droppable = droppable | (df['compartment'] == c) | (df['other_compartment'] == c)
            droppable = df.loc[droppable].index
            df.drop(index=droppable, inplace=True)
            logger.info('Dropped %s rows for compartmental membership.', len(droppable))
            if df.shape[0] == 0:
                logger.error('Dropped all rows!')
                return None

        grouped = df.groupby([
                'sample_identifier',
                'fov_index',
                'compartment',
                'other_compartment',
            ]
        )

        subsample_size = 200
        number_cells = df.shape[0]
        if number_cells > len(grouped)*subsample_size:
            df = grouped.sample(n=subsample_size, replace=True)
            logger.info(
                'Subsampled from %s to %s rows, based on a per-group limit of %s.',
                number_cells,
                df.shape[0],
                subsample_size,
            )

        if len(set(df['outcome_assignment'])) > 1:
            all_samples = df.copy()
            all_samples['sample_identifier'] = [
                '(all ' + outcome + ')' for outcome in all_samples['outcome_assignment']
            ]
            all_samples['fov_index'] = [
                '(all ' + outcome + ')' for outcome in all_samples['outcome_assignment']
            ]
            df = pd.concat([df, all_samples])

        df = df.sort_values(by=[
            'sample_identifier',
            'fov_index',
            'compartment',
            'other_compartment',
        ]).reset_index(drop=True)
        logger.info('Finished preprocessing distances table.')
        return df

    def start_showing(self):
        """
        Begins displaying the plots.
        """
        self.fig.show()
