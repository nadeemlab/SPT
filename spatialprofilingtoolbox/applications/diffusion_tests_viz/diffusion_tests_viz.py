#!/usr/bin/env python3
"""
This application plots statistical outcome-to-outcome testing of diffusion
distance values, by phenotype and by "temporal offset" or timepoint pertaining
to the diffusion Markov chain.

It runs in interactive mode, generating figures in-browser with plotly as you
select options in a separate window. Optionally, it saves each figure to file as
it is shown.
"""
import sys
import os
from os import getcwd
from os.path import exists, abspath, dirname, join
from os import mkdir
import re

import pandas as pd
try:
    import tkinter as tk
    import tkinter.filedialog as fd
    from tkinter import ttk
except ModuleNotFoundError:
    print('Python standard library module tkinter somehow not available.')
import plotly.graph_objects as go

from ...environment.log_formats import colorized_logger
logger = colorized_logger(__name__)


class ColorStack:
    """
    A convenience function for assigning qualitatively distinct colors for the UI
    elements.
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


class FigureWrapper:
    """
    Class to wrap the plotly figure.
    """
    def __init__(self, significance_threshold):
        self.significance_threshold = significance_threshold

    def show_figure(self,
        outcome1,
        outcome2,
        summarization_statistic,
        test_name,
        table,
        also_save_to_file=False,
    ):
        """
        Shows a plotly figure in the browser depicting the multiplicative effect of the
        given pairwise comparison, against the temporal offset parameter.

        :param outcome1: The first outcome label in pairwise comparison.
        :type outcome1: str

        :param outcome2: The second outcome label in pairwise comparison.
        :type outcome2: str

        :param summarization_statistic: The name of the "first summarization" statistic
            used to reduce the distributional data to a single feature along the sample
            set.
        :type summarization_statistic: str

        :param test_name: The name of the statistical comparison test.
        :type test_name: str

        :param table: A table with columns:
            - "phenotype"
            - "temporal offset"
            - "multiplicative effect"
        :type table: pandas.DataFrame
        """
        self.fig = go.Figure()

        last_values, rolling_max = self.add_phenotype_traces(table)

        t_initial = sorted(list(table['temporal offset']))[0]
        t_final = sorted(list(table['temporal offset']), reverse=True)[0]
        self.add_baseline(t_initial, t_final)

        range_max = max(1.0, rolling_max * 1.05)
        last_values = self.respace_label_locations(last_values, range_max, 0)

        self.format_figure()
        title = ''.join([
            outcome1,
            ' vs. ',
            outcome2,
            '<br>',
            'Testing the ',
            summarization_statistic,
            ' of diffusion distances feature with ',
            test_name,
            '<br>',
            '(only showing p < ',
            str(self.significance_threshold),
            ')',
        ])
        self.annotate_traces(last_values, title)
        self.fig.update_yaxes(range=[0, range_max])
        if also_save_to_file:
            filehandle = '_'.join([
                outcome1,
                outcome2,
                summarization_statistic,
                test_name,
            ])
            filehandle = re.sub(' ', '_', filehandle)
            filename = filehandle + '.svg'
            out_path = 'plotly_outputs'
            if not exists(out_path):
                mkdir(out_path)
            self.fig.write_image(join('plotly_outputs', filename))
        self.fig.show()

    def add_phenotype_traces(self, table):
        last_values = {}
        rolling_max = 0
        cs = ColorStack()
        for p in set(table['phenotype']):
            table_p = table[table['phenotype'] == p]
            table_p = table_p.sort_values(by='temporal offset')
            cs.push_label(p)
            self.fig.add_trace(go.Scatter(
                x=table_p['temporal offset'],
                y=table_p['multiplicative effect'],
                mode='lines+markers',
                name=p,
                line=dict(color=cs.get_color(p), width=2),
                connectgaps=False,
            ))
            table_p = table_p.sort_values(by='temporal offset', ascending=False)
            last_values[p] = list(table_p['multiplicative effect'])[0]
            rolling_max = max([rolling_max] + list(table_p['multiplicative effect']))
        return [last_values, rolling_max]

    def add_baseline(self, t_initial, t_final):
        self.fig.add_trace(go.Scatter(
            x=[t_initial, t_final],
            y=[1.0, 1.0],
            mode = 'lines',
            line = dict(color='gray', width=1, dash='dash'),
            connectgaps=True,
        ))

    def respace_label_locations(self,
        locations,
        max_value,
        min_value,
        label_height_fraction=0.06,
    ):
        assumed_label_height = (max_value - min_value) * label_height_fraction
        new_locations = [[key, location] for key, location in locations.items()]
        new_locations = sorted(new_locations, key=lambda pair: pair[1])
        for i in range(1, len(new_locations)):
            if new_locations[i][1] - new_locations[i-1][1] < assumed_label_height:
                new_locations[i][1] = new_locations[i-1][1] + assumed_label_height
        new_locations = {key : location for key, location in new_locations}
        return new_locations

    def format_figure(self):
        self.fig.update_layout(
            xaxis=dict(
                showline=True,
                showgrid=False,
                showticklabels=True,
                linecolor='rgb(204, 204, 204)',
                linewidth=2,
                ticks='outside',
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showline=True,
                showticklabels=True,
            ),
            autosize=False,
            margin=dict(
                autoexpand=False,
                l=100,
                r=20,
                t=110,
            ),
            showlegend=False,
            plot_bgcolor='white',
        )

    def annotate_traces(self, last_values, title):
        annotations = []

        for label in last_values.keys():
            annotations.append(dict(
                xref='paper',
                x=0.95,
                y=last_values[label],
                xanchor='left',
                yanchor='middle',
                text=label,
                font=dict(family='Arial', size=12),
                showarrow=False,
            ))

        annotations.append(dict(
            xref='paper',
            yref='paper',
            x=0.5,
            y=1.05,
            xanchor='center',
            yanchor='bottom',
            text=title,
            font=dict(family='Arial', size=18, color='rgb(37,37,37)'),
            showarrow=False,
            ))

        self.fig.update_layout(
            annotations=annotations,
        )
        self.fig.update_layout(
            xaxis_title='Markov chain temporal offset',
            yaxis_title='multiplicative effect',
            width=800,
            height=600,
        )


class DiffusionTestsViz:
    """
    The GUI application/window for parameter selection.
    """
    def __init__(self, tests_filename=None, significance_threshold=0.05, interactive_only=True):
        self.significance_threshold = significance_threshold
        self.interactive_only = interactive_only

        self.root = tk.Tk()
        self.root.winfo_toplevel().title("Diffusion transition probability values visualization")
        self.dataframe = self.retrieve_tests_dataframe(tests_filename=tests_filename)
        if len(self.dataframe) == 0:
            logger.error(
                'No statistically significant results to show, at threshold %s',
                significance_threshold,
            )
            return
        self.tk_vars = {varname : tk.StringVar() for varname in self.get_visible_parameter_names()}

        varnames = self.get_visible_parameter_names()
        comboboxes = {
            varname : ttk.Combobox(self.root, state='readonly', font=("Arial", 20), textvariable=self.tk_vars[varname]) for varname in varnames
        }

        for i, key in enumerate(comboboxes.keys()):
            comboboxes[key].grid(row=i, column=1, padx=(10, 10), pady=(10, 10))
            comboboxes[key].bind("<<ComboboxSelected>>", self.update_selection)
            var = tk.StringVar()
            tk.Label(self.root, textvariable=var, font=("Arial", 20)).grid(sticky='W', row=i, column=0, padx=(10, 10), pady=(10, 10))
            var.set(key)

        for key, val in self.get_table_column_association().items():
            comboboxes[key]['values'] = sorted(list(set(self.dataframe[val])))
            comboboxes[key].current(0)

        self.figure_wrapper = FigureWrapper(self.significance_threshold)
        self.update_selection(None)

    def retrieve_tests_dataframe(self, tests_filename=None):
        test_results_file = tests_filename
        df = pd.read_csv(test_results_file)
        df = df.sort_values(by='temporal offset')
        p = self.significance_threshold
        df['multiplicative effect'] = df['tested value 2'] / df['tested value 1']
        df['p-value < ' + str(p)] = (df['p-value'] < p)
        df_significant = df[df['p-value < ' + str(p)]]
        return df_significant

    def restrict_dataframe(self, table, selected_variables):
        for key, val in selected_variables.items():
            table = table[table[key] == val]
        return table

    def update_selection(self, event):
        v = self.get_selected_vars()
        table = self.restrict_dataframe(self.dataframe, v)
        self.figure_wrapper.show_figure(
            v['outcome 1'],
            v['outcome 2'],
            v['first-summarization statistic tested'],
            v['test'],
            table,
            also_save_to_file=not self.interactive_only,
        )

    def get_selected_vars(self):
        return {
            val : self.tk_vars[key].get() for key, val in self.get_table_column_association().items()
        }

    def get_visible_parameter_names(self):
        return self.get_table_column_association().keys()

    def get_table_column_association(self):
        return {
            'outcome 1' : 'outcome 1',
            'outcome 2' : 'outcome 2',
            'tested feature function' : 'first-summarization statistic tested',
            'statistical test' : 'test',
        }

    def start_showing(self):
        self.root.mainloop()
