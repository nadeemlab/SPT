#!/usr/bin/env python3
"""
Experimental GUI for examining statistical test results, pairwise outcome comparison of diffusion probability values.
"""
import sys
import os
from os import getcwd
from os.path import exists, abspath, dirname

import pandas as pd
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk
import plotly.graph_objects as go


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


class FigureWrapper:
    def __init__(self, significance_threshold):
        self.significance_threshold = significance_threshold

    def show_figures(self, key, table):
        cs = ColorStack()
        self.fig = go.Figure()
        for phenotype in set(table['phenotype']):
            table2 = table[table['phenotype'] == phenotype]
            data = list(table2['multiplicative effect'])
            label = phenotype

            df2 = pd.DataFrame({
                'Markov chain temporal offset' : table2['temporal offset'],
                'multiplicative effect' : data,
            }).sort_values(by='Markov chain temporal offset', ascending=False)
            t_values = list(df2['Markov chain temporal offset'])

        last_values = {}
        rolling_max = 0
        for phenotype in set(table['phenotype']):
            table2 = table[table['phenotype'] == phenotype]
            data = list(table2['multiplicative effect'])
            label = phenotype
            cs.push_label(label)
            color = cs.get_color(label)

            df2 = pd.DataFrame({
                'Markov chain temporal offset' : table2['temporal offset'],
                'multiplicative effect' : data,
            }).sort_values(by='Markov chain temporal offset', ascending=False)

            last_values[label] = list(df2['multiplicative effect'])[0]

            self.fig.add_trace(go.Scatter(
                x=df2['Markov chain temporal offset'],
                y=df2['multiplicative effect'],
                mode='lines+markers',
                name=label,
                line=dict(color=color, width=2),
                connectgaps=False,
            ))

            rolling_max = max([rolling_max] + list(df2['multiplicative effect']))

        range_max = max(1.0, rolling_max * 1.05)

        if range_max > 1.0:
            self.fig.add_trace(go.Scatter(
                x=[1.0, 2.8],
                y=[1.0, 1.0],
                mode = 'lines',
                line = dict(color='gray', width=1, dash='dash'),
                connectgaps=True,
            ))

        last_values = self.respace_label_locations(last_values, range_max, 0)

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

        title = ''.join([
            key[0],
            ' vs. ',
            key[1],
            '<br>',
            'Testing the "',
            key[2],
            '" feature with ',
            key[3],
            '<br>',
            '(only showing p < ',
            str(self.significance_threshold),
            ')',
        ])

        annotations = []

        for label in set(table['phenotype']):
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

        self.fig.update_yaxes(range=[0, range_max])

        self.fig.show()

    def respace_label_locations(self, locations, max_value, min_value, label_height_fraction=0.06):
        assumed_label_height = (max_value - min_value) * label_height_fraction
        new_locations = [[key, location] for key, location in locations.items()]
        new_locations = sorted(new_locations, key=lambda pair: pair[1])
        for i in range(1, len(new_locations)):
            if new_locations[i][1] - new_locations[i-1][1] < assumed_label_height:
                new_locations[i][1] = new_locations[i-1][1] + assumed_label_height
        new_locations = {key : location for key, location in new_locations}
        return new_locations


class DiffusionTestsViz:
    """
    A wrapper around the dynamically-selected combobox variables and other GUI elements.
    """
    def __init__(self, tests_filename=None, significance_threshold=0.05):
        self.significance_threshold = significance_threshold

        self.root = tk.Tk()
        self.root.winfo_toplevel().title("Diffusion transition probability values visualization")
        self.dataframe = self.retrieve_tests_dataframe(tests_filename=tests_filename)
        self.tk_vars = {varname : tk.StringVar() for varname in self.get_variable_names()}
        self.table_column_association = {
            'outcome 1' : 'outcome 1',
            'outcome 2' : 'outcome 2',
            'tested feature function' : 'first-summarization statistic tested',
            'statistical test' : 'test',
        }

        varnames = self.get_variable_names()
        comboboxes = {
            varname : ttk.Combobox(self.root, state='readonly', font=("Arial", 20), textvariable=self.tk_vars[varname]) for varname in varnames
        }

        for i, key in enumerate(comboboxes.keys()):
            comboboxes[key].grid(row=i, column=1, padx=(10, 10), pady=(10, 10))
            comboboxes[key].bind("<<ComboboxSelected>>", self.update_selection)
            var = tk.StringVar()
            tk.Label(self.root, textvariable=var, font=("Arial", 20)).grid(sticky='W', row=i, column=0, padx=(10, 10), pady=(10, 10))
            var.set(key)

        for key, val in self.table_column_association.items():
            comboboxes[key]['values'] = sorted(list(set(self.dataframe[val])))
            comboboxes[key].current(0)

        self.figure_wrapper = FigureWrapper(self.significance_threshold)
        self.update_selection(None)

    def retrieve_tests_dataframe(self, tests_filename=None):
        if not tests_filename is None:
            test_results_file = tests_filename
        else:
            test_results_file = self.get_test_results_file()
        df = pd.read_csv(test_results_file)
        df = df.sort_values(by='temporal offset')

        p = self.significance_threshold
        df['multiplicative effect'] = df['tested value 2'] / df['tested value 1']
        df['lower multiplicative effect'] = df['lower absolute deviation']
        df['upper multiplicative effect'] = df['upper absolute deviation']
        df['p-value < ' + str(p)] = (df['p-value'] < p)
        df_significant = df[df['p-value < ' + str(p)]]

        return df_significant

    def get_test_results_file(self):
        if len(sys.argv) == 2:
            test_results_file = sys.argv[1]
            if not exists(test_results_file):
                print('Test results file ' + test_results_file + ' does not exist.')
                exit()
        else:
            test_results_file = fd.askopenfilename(
                initialdir=abspath(getcwd()),
                title='Select "diffusion_distance_tests.csv" file.',
            )
        return test_results_file

    def restrict_dataframe(self, table, selected_variables):
        for key, val in selected_variables.items():
            table = table[table[key] == val]
        return table

    def update_selection(self, event):
        selected_variables = self.get_selected_vars()
        table = self.restrict_dataframe(self.dataframe, selected_variables)
        self.figure_wrapper.show_figures(list(selected_variables.values()), table)

    def get_selected_vars(self):
        return {
            val : self.tk_vars[key].get() for key, val in self.table_column_association.items()
        }

    def get_variable_names(self):
        return ['outcome 1', 'outcome 2', 'tested feature function', 'statistical test']

    def start_showing(self):
        self.root.mainloop()
