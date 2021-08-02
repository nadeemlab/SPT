#!/usr/bin/env python3
"""
Experimental GUI for examining statistical test results, pairwise outcome comparison of diffusion probability values.
"""
import sys
import os
from os import getcwd
from os.path import exists, abspath, dirname, join
from os import mkdir
import re
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff

from ...workflows.front_proximity.computational_design import FrontProximityDesign

class ColorStack:
    """
    A convenience function for assigning qualitatively distinct colors for the UI elements.
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
    def __init__(self, distances_db_uri=None):
        self.dataframe = self.retrieve_distances_dataframe(uri=distances_db_uri, table_name='cell_front_distances')

        self.fig = go.Figure()

        # 461ca28c204fac2ac619e2d81902afc4
        # 2779f21192cb0ce1479b2bf7fb20ebba
        # 5e1b6c32494caf1be6c9a68b136a2840
        # 3d25f72e8ca948280b7bfeb9de03944f
        # 33c794a479e571ae50518546555b9480
        # 2cc18c6561b05abb1a1a95d15130a1d3

        # sample_identifier = '2779f21192cb0ce1479b2bf7fb20ebba'
        # fov_index = 0
        # compartment = 'Tumor'
        # other_compartment = 'Non-Tumor'
        # hist_data1, group_labels1 = self.get_distances_along(
        #     sample_identifier=sample_identifier,
        #     fov_index=fov_index,
        #     compartment=compartment,
        #     other_compartment=other_compartment,
        # )

        # caption_text = self.get_caption_text(
        #     sample_identifier = sample_identifier,
        #     fov_index = fov_index,
        #     compartment = compartment,
        #     other_compartment = other_compartment,
        # )

        caption_text = ''

        # sample_identifier2 = '5e1b6c32494caf1be6c9a68b136a2840'
        fov_index = 0
        compartment = 'Tumor'
        other_compartment = 'Non-Tumor'
        # hist_data2, group_labels2 = self.get_distances_along(
        #     sample_identifier=sample_identifier2,
        #     fov_index=fov_index,
        #     compartment=compartment,
        #     other_compartment=other_compartment,
        # )

        sample_identifiers = list(set(self.dataframe['sample_identifier']))

        all_hist_data = []
        all_group_labels = []
        sizes = []
        for sample_identifier in sample_identifiers:
            hist_data, group_labels = self.get_distances_along(
                sample_identifier=sample_identifier,
                fov_index=fov_index,
                compartment=compartment,
                other_compartment=other_compartment,
            )
            all_hist_data = all_hist_data + hist_data
            all_group_labels = all_group_labels + group_labels
            sizes.append(len(group_labels))

        indicator_function = {sample_identifier : [False]*sum(sizes) for sample_identifier in sample_identifiers}
        offset = 0
        for i, sample_identifier in enumerate(sample_identifiers):
            for j in range(sizes[i]):
                indicator_function[sample_identifier][offset + j] = True
            offset += sizes[i]

        self.fig = ff.create_distplot(hist_data=all_hist_data, group_labels=all_group_labels, bin_size=50)

                        # dict(
                        #     args=['visible', indicator_function[sample_identifier]],
                        #     label=sample_identifier,
                        #     method='restyle'
                        # ),
                        # dict(
                        #     args=['visible', indicator_function[sample_identifier2]],
                        #     label=sample_identifier2,
                        #     method='restyle'
                        # )

        self.fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=['visible', indicator_function[sample_identifier]],
                            label=sample_identifier,
                            method='restyle'
                        ) for sample_identifier in sample_identifiers
                    ]),
                    direction="down",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.1,
                    xanchor="right",
                    y=1.1,
                    yanchor="top"
                ),
            ]
        )

        self.fig.update_layout(
            annotations=[
                dict(
                    text=caption_text,
                    showarrow=False,
                    x=0,
                    y=-0.05,
                    yref="paper",
                    align="left",
                )
            ]
        )


        # cs = ColorStack()
        # for p in set(table['phenotype']):
        #     table_p = table[table['phenotype'] == p]
        #     table_p = table_p.sort_values(by='temporal offset')
        #     cs.push_label(p)
        #     self.fig.add_trace(go.Scatter(
        #         x=table_p['temporal offset'],
        #         y=table_p['multiplicative effect'],
        #         mode='lines+markers',
        #         name=p,
        #         line=dict(color=cs.get_color(p), width=2),
        #         connectgaps=False,
        #     ))
        #     table_p = table_p.sort_values(by='temporal offset', ascending=False)
        #     last_values[p] = list(table_p['multiplicative effect'])[0]
        #     rolling_max = max([rolling_max] + list(table_p['multiplicative effect']))

        # self.fig.update_layout(
        #     xaxis=dict(
        #         showline=True,
        #         showgrid=False,
        #         showticklabels=True,
        #         linecolor='rgb(204, 204, 204)',
        #         linewidth=2,
        #         ticks='outside',
        #         tickfont=dict(
        #             family='Arial',
        #             size=12,
        #             color='rgb(82, 82, 82)',
        #         ),
        #     ),
        #     yaxis=dict(
        #         showgrid=False,
        #         zeroline=False,
        #         showline=True,
        #         showticklabels=True,
        #     ),
        #     autosize=False,
        #     margin=dict(
        #         autoexpand=False,
        #         l=100,
        #         r=20,
        #         t=110,
        #     ),
        #     showlegend=False,
        #     plot_bgcolor='white',
        # )


        # # self.fig.write_image(join('plotly_outputs', filename))

        # annotations = []

        # for label in last_values.keys():
        #     annotations.append(dict(
        #         xref='paper',
        #         x=0.95,
        #         y=last_values[label],
        #         xanchor='left',
        #         yanchor='middle',
        #         text=label,
        #         font=dict(family='Arial', size=12),
        #         showarrow=False,
        #     ))

        # annotations.append(dict(
        #     xref='paper',
        #     yref='paper',
        #     x=0.5,
        #     y=1.05,
        #     xanchor='center',
        #     yanchor='bottom',
        #     text=title,
        #     font=dict(family='Arial', size=18, color='rgb(37,37,37)'),
        #     showarrow=False,
        # ))

        #         self.fig.update_layout(
        #             annotations=annotations,
        #         )
        #         self.fig.update_layout(
        #             xaxis_title='Markov chain temporal offset',
        #             yaxis_title='multiplicative effect',
        #             width=800,
        #             height=600,
        #         )

    def get_distances_along(self,
        sample_identifier=None,
        fov_index=None,
        compartment=None,
        other_compartment=None,
    ):
        fov_index = 0
        compartment = 'Tumor'
        other_compartment = 'Non-Tumor'
        df = self.dataframe[
            (self.dataframe['sample_identifier'] == sample_identifier) &
            (self.dataframe['fov_index'] == fov_index) &
            (self.dataframe['compartment'] == compartment) &
            (self.dataframe['other_compartment'] == other_compartment)
        ]
        grouped = df.groupby('phenotype')
        hist_data_labels = [(list(g['distance_to_front_in_pixels']), key) for key, g in grouped]
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
