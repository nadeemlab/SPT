#!/usr/bin/env python3
import sys
import re

import networkx as nx
import matplotlib.pyplot as plt

class DiffusionGraphsViz:
    def __init__(self):
        self.graph = self.retrieve_graph()
        self.weightings = self.get_weighting_names_ordered()
        self.timepoint = 0
        self.max_timepoint = len(self.weightings)-1
        fig, ax = plt.subplots()
        self.fig = fig
        self.ax = ax
        plt.connect('key_press_event', self.handle_keypress)

    def get_weighting_names_ordered(self):
        G = self.graph
        e0 = list(G.edges)[0]
        weighting_names = sorted(list(G.edges[e0].keys()))
        weighting_ids = sorted([float(re.search(r'[\d\.]+$', name).group(0)) for name in weighting_names])

        prefixes = [re.sub(r'[\d\.]+$', '', name for name in weighting_names)]
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
            if self.timepoint < 0:
                self.timepoint += 1
                return

        G = self.graph
        pos = nx.spring_layout(G, weight = self.weightings[self.timepoint], seed=7)
        ax.clear()
        nx.draw(G, with_labels=True, font_weight='bold', pos=pos, ax=ax)
        ax.text(-0.01, -0.1, 't='+str(self.timepoint) + ' (' + self.weightings[self.timepoint] + ')', transform=ax.transAxes)
        plt.draw()

    def start_showing(self):
        plt.show()

