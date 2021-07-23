#!/usr/bin/env python3
import sys
import re
from math import floor
import os
from os import mkdir
from os.path import join, exists, basename

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


class DiffusionGraphsViz:
    def __init__(self, graph_filename=None, node_color='blue', caption='', interactive=True):
        self.graph_filename = graph_filename
        self.graph = self.retrieve_graph(graph_filename=graph_filename)
        self.node_color = node_color
        self.caption = caption
        self.interactive = interactive
        self.means = {}
        self.weightings = self.get_weighting_names_ordered()
        self.timepoint = -1
        self.max_timepoint = len(self.weightings)-1
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax
        if interactive:
            plt.connect('key_press_event', self.handle_keypress)
        self.positions = None

    def get_weighting_names_ordered(self):
        G = self.graph
        e0 = list(G.edges)[0]
        weighting_names = sorted(list(G.edges[e0].keys()))

        means = {}
        for name in weighting_names:
            means[name] = np.mean([G.edges[edge][name] for edge in G.edges])
            means[name] = self.round_decimal(means[name], 6)
            for edge in G.edges:
                w = G.edges[edge][name]
                G.edges[edge][name] = 1/w if w!=0 else 1.0

        weighting_ids = sorted([int(re.search(r'[\d\.]+$', name).group(0)) for name in weighting_names])

        prefixes = [re.sub(r'[\d\.]+$', '', name) for name in weighting_names]
        if not all([prefix == prefixes[0] for prefix in prefixes]):
            print('Error: Not all prefixes equal to "' + prefixes[0] + '"')
            exit()
        else:
            prefix = prefixes[0]
        weighting_names_ordered = [prefix + str(i) for i in weighting_ids]
        self.means = {i : means[weighting_names_ordered[i]] for i in range(len(weighting_names_ordered))}
        return weighting_names_ordered

    def retrieve_graph(self, graph_filename=None):
        if not re.search(r'\.graphml$', graph_filename):
            print('Need graphml file.')
            exit()
        return nx.readwrite.graphml.read_graphml(graph_filename)

    def handle_keypress(self, event):
        if event.key == 'right':
            self.timepoint += 1
            if self.timepoint > self.max_timepoint:
                self.timepoint -= 1
                return
        if event.key == 'left':
            self.timepoint -= 1
            if self.timepoint < -1:
                self.timepoint += 1
                return

        self.draw_graph()

    def round_decimal(self, value, number_digits):
        return (floor(value * pow(10, number_digits)) / pow(10, number_digits))

    def draw_graph(self):
        G = self.graph
        if self.positions is None:
            self.positions = {}
            initial_pos = {node : [G.nodes[node]['x_coordinate'], G.nodes[node]['y_coordinate']] for node in G.nodes}
            self.positions[-1] = initial_pos
            self.means[-1] = '-'
            for i in range(self.max_timepoint+1):
                self.positions[i] = nx.spring_layout(G, weight = self.weightings[i], seed=7, pos=self.positions[i-1])

        initial_pos = self.positions[-1]
        if self.timepoint >= 0:
            weighting_name = '(' + self.weightings[self.timepoint] + ')'
        else:
            weighting_name = ''

        pos = self.positions[self.timepoint]
        self.ax.clear()
        nx.draw(G, with_labels=False, pos=pos, ax=self.ax, node_size=30, width=0.02, node_color=self.node_color)
        self.ax.set_title(self.caption)
        text = 'Number of nodes = ' + str(len(G.nodes))
        if self.timepoint != -1:
            text += '   Mean diffusion distance = ' + str(self.means[self.timepoint])
        if self.interactive:
            text += '   T='+str(self.timepoint) + ' ' + weighting_name
        self.ax.text(-0.01, -0.1, text, transform=self.ax.transAxes)
        self.ax.collections[0].set_edgecolor("#000000")
        plt.draw()
        if not self.interactive:
            filehandle = basename(self.graph_filename).rstrip('.graphml') + '_timepoint_' + str(self.timepoint)
            out_path = 'matplotlib_outputs'
            if not exists(out_path):
                mkdir(out_path)
            plt.savefig(join(out_path, filehandle + '.svg'))
            plt.savefig(join(out_path, filehandle + '.png'))

    def start_showing(self):
        if self.interactive:
            self.draw_graph()
            plt.show()
        else:
            for t in range(-1, self.max_timepoint + 1):
                self.timepoint = t
                self.draw_graph()
