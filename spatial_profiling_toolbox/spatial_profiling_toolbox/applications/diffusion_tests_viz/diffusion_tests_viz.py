#!/usr/bin/env python3
"""
Experimental GUI for examining statistical test results, pairwise outcome comparison of diffusion probability values.
"""
import sys
import os
from os import getcwd
from os.path import exists, abspath, dirname

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.filedialog as fd
from tkinter import ttk


class ColorStack:
    """
    A convenience function for assigning qualitatively distinct colors for the UI elements.
    """
    def __init__(self):
        c = ['green', 'skyblue', 'red', 'white','purple','blue','orange','yellow']
        self.colors = c + c + c + c + c + c + c + c + c + c
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
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        self.fig = fig
        self.axs = axs
        self.significance_threshold = significance_threshold

    def show_figures(self, key, table):
        fig = self.fig
        axs = self.axs
        for ax in axs:
            ax.clear()
        cs = {i : ColorStack() for i in range(len(axs))}

        focus_cols = ['absolute effect', 'multiplicative effect']
        var_cols = ['phenotype', 'effect sign', 'absolute effect', 'multiplicative effect', 'temporal offset', 'tested value 1', 'tested value 2']

        table = table[var_cols]
        for i, col in enumerate(focus_cols):
            for phenotype in set(table['phenotype']):
                table2 = table[table['phenotype'] == phenotype]
                data = list(table2[col])
                label = phenotype
                cs[i].push_label(label)
                color = cs[i].get_color(label)
                axs[i].plot(table2['temporal offset'], data, label=label)

        for phenotype in set(table['phenotype']):
            table2 = table[table['phenotype'] == phenotype]

            data = table2['tested value 1']
            label = phenotype + ' (tested value 1)'
            cs[2].push_label(label)
            color = cs[2].get_color(label)
            axs[2].plot(table2['temporal offset'], data, label=label)

            data = table2['tested value 2']
            label = phenotype + ' (tested value 2)'
            cs[2].push_label(label)
            color = cs[2].get_color(label) # Why this?
            axs[2].plot(table2['temporal offset'], data, label=label)

        axs[0].set_ylabel(focus_cols[0])
        axs[1].set_ylabel(focus_cols[1])
        axs[2].set_ylabel('tested values')

        for i in range(3):
            axs[i].set_xlabel('temporal offset (Markov chain simulation duration)')

        fig.suptitle(''.join([
            key[0],
            ' vs. ',
            key[1],
            ', testing the "',
            key[2],
            '" feature with ',
            key[3],
            ' (only p < ',
            str(self.significance_threshold),
            ')',
        ]))

        axs[0].legend()
        axs[1].legend()
        axs[2].legend()


class DiffusionTestsViz:
    """
    A wrapper around the dynamically-selected combobox variables and other GUI elements.
    """
    def __init__(self, tests_filename=None):
        self.significance_threshold = 0.05

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
        plt.ion()
        plt.show()

    def get_selected_vars(self):
        return {
            val : self.tk_vars[key].get() for key, val in self.table_column_association.items()
        }

    def get_variable_names(self):
        return ['outcome 1', 'outcome 2', 'tested feature function', 'statistical test']

    def start_showing(self):
        self.root.mainloop()
