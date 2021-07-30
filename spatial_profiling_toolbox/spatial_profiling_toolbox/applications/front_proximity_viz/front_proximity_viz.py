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

import pandas as pd
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk
import plotly.graph_objects as go

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
        print(self.dataframe.shape)
        print(self.dataframe)
        self.fig = go.Figure()
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

    def retrieve_distances_dataframe(self, uri: str=None, table_name: str=None):
        connection = sqlite3.connect(uri)
        df = pd.read_sql_table(table_name, connection)
        connection.close()
        return df

    def start_showing(self):
        self.fig.show()
