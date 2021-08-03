#!/usr/bin/env python3
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots

from ...workflows.front_proximity.computational_design import FrontProximityDesign
from ...environment.log_formats import colorized_logger
logger = colorized_logger(__name__)

class ColorStack:
    """
    A convenience function for assigning qualitatively distinct colors to UI elements.
    """
    def __init__(self):
        c = ['green', 'skyblue', 'red', 'white','purple','blue','orange','yellow']
        self.colors = c*10
        self.stack = {}

    def push_label(self, label):
        """
        Assign a color to the given label.

        :param label: The label for some UI element.
        :type label: str (or other hashable type)
        """
        if label in self.stack:
            return
        else:
            self.stack[label] = self.colors[len(self.stack)]

    def get_color(self, label):
        """
        Retrieve an assigned color.

        :param label: The label to lookup.
        :type label: str (or other hashable type)
        """
        return self.stack[label]


class FrontProximityViz:
    """
    This application allows the user to select a field of view in a given image, and
    a pair of region classes, and then shows a plot of the distribution of the
    distance-to-front values by phenotype.
    """
    def __init__(self, distances_db_uri=None):
        """
        :param distances_db_uri: The URI of the database containing the output of the
            front proximity pipeline.
        :type distances_db_uri: str
        """
        self.dataframe = self.retrieve_distances_dataframe(
            uri=distances_db_uri,
            table_name='cell_front_distances',
        )
        self.fig = go.Figure()

        self.dataframe = self.dataframe.sort_values(by=[
            'sample_identifier',
            'fov_index',
            'compartment',
            'other_compartment',
        ]).reset_index(drop=True)
        tuples_duplicated = [
            (row['sample_identifier'], row['fov_index']) for i, row in self.dataframe.iterrows()
        ]
        case_identifiers = sorted(list(set(tuples_duplicated)))

        compartment_pairs = [
            tuple(sorted([row['compartment'], row['other_compartment']])) for i, row in self.dataframe.iterrows()
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
        for sample_identifier, fov_index in case_identifiers:
            hist_data1, group_labels1 = self.get_distances_along(
                sample_identifier=sample_identifier,
                fov_index=fov_index,
                compartment=compartment_pair[0],
                other_compartment=compartment_pair[1],
            )
            hist_data2, group_labels2 = self.get_distances_along(
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

        indicator_function1 = {case : [False]*(sum(sizes1)) for case in case_identifiers}
        offset = 0
        for i, case in enumerate(case_identifiers):
            for j in range(sizes1[i]):
                indicator_function1[case][offset + j] = True
            offset += sizes1[i]

        indicator_function2 = {case : [False]*(sum(sizes1)) for case in case_identifiers}
        offset = 0
        for i, case in enumerate(case_identifiers):
            for j in range(sizes2[i]):
                indicator_function2[case][offset + j] = True
            offset += sizes2[i]

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

        # fig1.update_layout(
        #     updatemenus=[
        #         dict(
        #             buttons=list([
        #                 dict(
        #                     args=['visible', indicator_function1[case]],
        #                     label=''.join([
        #                         'Sample ID, FOV: ',
        #                         str((case[0],case[1])),
        #                     ]),
        #                     method='restyle',
        #                 ) for case in case_identifiers
        #             ]),
        #             direction="down",
        #             pad={"r": 10, "t": 10},
        #             showactive=True,
        #             x=0.1,
        #             xanchor="right",
        #             y=1.2,
        #             yanchor="top",
        #         ),
        #     ]
        # )

        # fig2.update_layout(
        #     updatemenus=[
        #         dict(
        #             buttons=list([
        #                 dict(
        #                     args=['visible', indicator_function2[case]],
        #                     label=''.join([
        #                         'Sample ID, FOV: ',
        #                         str((case[0],case[1])),
        #                     ]),
        #                     method='restyle',
        #                 ) for case in case_identifiers
        #             ]),
        #             direction="down",
        #             pad={"r": 10, "t": 10},
        #             showactive=True,
        #             x=0.1,
        #             xanchor="right",
        #             y=1.2,
        #             yanchor="top",
        #         ),
        #     ]
        # )


        fig = make_subplots(rows=1, cols=2)

        # fig.add_trace(
        #     go.Histogram(fig1['data'][0], marker_color='blue'),
        #     row=1, col=1,
        # )
        # fig.add_trace(
        #     go.Histogram(fig1['data'][1], marker_color='red'),
        #     row=1, col=1,
        # )
        # fig.add_trace(
        #     go.Scatter(fig1['data'][0 + sum(sizes1)], line=dict(color='blue', width=0.5)),
        #     row=1, col=1,
        # )
        # fig.add_trace(
        #     go.Scatter(fig1['data'][1 + 0 + sum(sizes1)], line=dict(color='red', width=0.5)),
        #     row=1, col=1,
        # )

        count = 0
        case_relevant_indices = {case : [] for case in case_identifiers}

        offset = 0
        for i, size in enumerate(sizes1):
            case = case_identifiers[i]
            for j in range(size):
                fig.add_trace(
                    go.Histogram(fig1['data'][offset + j], nbinsx=25),
                    row=1, col=1
                )
                case_relevant_indices[case].append(count)
                count += 1
                fig.add_trace(
                    go.Scatter(fig1['data'][offset + j + sum(sizes1)], line=dict(width=0.5)),
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
                    go.Histogram(fig2['data'][offset + j], nbinsx=25),
                    row=1, col=2,
                )
                case_relevant_indices[case].append(count)
                count += 1
                fig.add_trace(
                    go.Scatter(fig2['data'][offset + j + sum(sizes2)], line=dict(width=0.5)),
                    row=1, col=2,
                )
                case_relevant_indices[case].append(count)
                count += 1

            offset += size

        indicator_function = {
            case : [(c in case_relevant_indices[case]) for c in range(count)] for case in case_identifiers
        }

        fig.add_trace(
            go.Histogram(fig2['data'][0], marker_color='green'),
            row=1, col=2,
        )
        fig.add_trace(
            go.Histogram(fig2['data'][1], marker_color='orange'),
            row=1, col=2,
        )
        # fig.add_trace(
        #     go.Scatter(fig2['data'][2], line=dict(color='green', width=0.5)),
        #     row=1, col=2,
        # )
        # fig.add_trace(
        #     go.Scatter(fig2['data'][3], line=dict(color='orange', width=0.5)),
        #     row=1, col=2,
        # )

        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=['visible', indicator_function[case]],
                            label=''.join([
                                'Sample ID, FOV: ',
                                str((case[0],case[1])),
                            ]),
                            method='restyle',
                        ) for case in case_identifiers
                    ]),
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.1,
                    xanchor="right",
                    y=1.2,
                    yanchor="top",
                ),
            ]
        )


        self.fig = fig

        # # self.fig.write_image(join('plotly_outputs', filename))

    def get_distances_along(self,
        sample_identifier=None,
        fov_index=None,
        compartment=None,
        other_compartment=None,
    ):
        df = self.dataframe[
            (self.dataframe['sample_identifier'] == sample_identifier) &
            (self.dataframe['fov_index'] == fov_index) &
            (self.dataframe['compartment'] == compartment) &
            (self.dataframe['other_compartment'] == other_compartment)
        ]
        grouped = df.groupby('phenotype')
        hist_data_labels = [(list(g['distance_to_front_in_pixels']), key + ' ' + compartment) for key, g in grouped]
        group_labels = [row[1] for row in hist_data_labels if len(row[0]) > 2]
        hist_data = [row[0] for row in hist_data_labels if len(row[0]) > 2]
        return [hist_data, group_labels]

    def get_caption_text(self,
            sample_identifier = None,
            fov_index = None,
            compartment = None,
            other_compartment = None,
        ):
        return ''.join([
            'Sample ',
            sample_identifier,
            ', ',
            'FOV ',
            str(fov_index),
            ', ',
            'cells in ',
            compartment,
            ' with respect to front with ',
            other_compartment,
        ])

    def retrieve_distances_dataframe(self, uri: str=None, table_name: str=None):
        connection = sqlite3.connect(uri)
        df = pd.read_sql_query('SELECT * from ' + table_name, connection)
        connection.close()
        return df

    def start_showing(self):
        self.fig.show()
