#!/usr/bin/env python3
import sys
import re

import networkx as nx
import matplotlib.pyplot as plt


class DiffusionGraphsViz:
    def __init__(self):
        self.graph = self.retrieve_graph()
        self.weightings = self.get_weighting_names_ordered()
        self.timepoint = -1
        self.max_timepoint = len(self.weightings)-1
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax
        plt.connect('key_press_event', self.handle_keypress)
        self.positions = None

    def get_weighting_names_ordered(self):
        G = self.graph
        e0 = list(G.edges)[0]
        weighting_names = sorted(list(G.edges[e0].keys()))

        for name in weighting_names:
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
        return weighting_names_ordered

    def retrieve_graph(self, graph_filename=None):
        if graph_filename is None:
            if len(sys.argv) < 2:
                print('Need graphml file.')
                exit()
            graph_filename = sys.argv[1]

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

    def draw_graph(self):
        G = self.graph
        initial_pos = {node : [G.nodes[node]['x_coordinate'], G.nodes[node]['y_coordinate']] for node in G.nodes}
        if self.positions is None:
            self.positions = {}
            self.positions[-1] = initial_pos
            for i in range(self.max_timepoint+1):
                self.positions[i] = nx.spring_layout(G, weight = self.weightings[self.timepoint], seed=7, pos=self.positions[i-1])

        if self.timepoint >= 0:
            weighting_name = '(' + self.weightings[self.timepoint] + ')'
        else:
            weighting_name = ''

        pos = self.positions[self.timepoint]
        self.ax.clear()
        nx.draw(G, with_labels=False, pos=pos, ax=self.ax, node_size=30, width=0.5)
        self.ax.text(-0.01, -0.1, 'T='+str(self.timepoint) + ' ' + weighting_name, transform=self.ax.transAxes)
        plt.draw()

    def start_showing(self):
        self.draw_graph()
        plt.show()

