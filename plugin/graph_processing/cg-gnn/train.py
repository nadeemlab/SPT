#!/usr/bin/env python3
"""Convert SPT graph objects to CG-GNN graph objects and run training and evaluation with them."""

from sys import path
from configparser import ConfigParser
from os import remove
from os.path import join, exists
from configparser import ConfigParser
from warnings import warn

from numpy import nonzero  # type: ignore
from networkx import to_scipy_sparse_array  # type: ignore
from torch import (
    FloatTensor,
    IntTensor,  # type: ignore
)
from dgl import DGLGraph, graph
from cggnn.util import GraphData, save_cell_graphs, load_cell_graphs
from cggnn.util.constants import INDICES, CENTROIDS, FEATURES, IMPORTANCES
from cggnn.run import train_and_evaluate

path.append('/app')  # noqa
from train_cli import parse_arguments, DEFAULT_CONFIG_FILE
from util import HSGraph, GraphData as SPTGraphData, load_hs_graphs, save_hs_graphs


def _convert_spt_graph(g_spt: HSGraph) -> DGLGraph:
    """Convert a SPT HSGraph to a CG-GNN cell graph."""
    num_nodes = g_spt.node_features.shape[0]
    g_dgl = graph([])
    g_dgl.add_nodes(num_nodes)
    g_dgl.ndata[INDICES] = IntTensor(g_spt.histological_structure_ids)
    g_dgl.ndata[CENTROIDS] = FloatTensor(g_spt.centroids)
    g_dgl.ndata[FEATURES] = FloatTensor(g_spt.node_features)
    # Note: channels and phenotypes are binary variables, but DGL only supports FloatTensors
    edge_list = nonzero(g_spt.adj.toarray())
    g_dgl.add_edges(list(edge_list[0]), list(edge_list[1]))
    return g_dgl


def _convert_spt_graph_data(g_spt: SPTGraphData) -> GraphData:
    """Convert a SPT GraphData object to a CG-GNN/DGL GraphData object."""
    return GraphData(
        graph=_convert_spt_graph(g_spt.graph),
        label=g_spt.label,
        name=g_spt.name,
        specimen=g_spt.specimen,
        set=g_spt.set,
    )


def _convert_spt_graphs_data(graphs_data: list[SPTGraphData]) -> list[GraphData]:
    """Convert a list of SPT HSGraphs to CG-GNN cell graphs."""
    return [_convert_spt_graph_data(g_spt) for g_spt in graphs_data]


def _convert_dgl_graph(g_dgl: DGLGraph) -> HSGraph:
    """Convert a DGLGraph to a CG-GNN cell graph."""
    return HSGraph(
        adj=to_scipy_sparse_array(g_dgl.to_networkx()),
        node_features=g_dgl.ndata[FEATURES].detach().cpu().numpy(),
        centroids=g_dgl.ndata[CENTROIDS].detach().cpu().numpy(),
        histological_structure_ids=g_dgl.ndata[INDICES].detach().cpu().numpy(),
        importances=g_dgl.ndata[IMPORTANCES].detach().cpu().numpy() if (IMPORTANCES in g_dgl.ndata)
        else None,
    )


def _convert_dgl_graph_data(g_dgl: GraphData) -> SPTGraphData:
    return SPTGraphData(
        graph=_convert_dgl_graph(g_dgl.graph),
        label=g_dgl.label,
        name=g_dgl.name,
        specimen=g_dgl.specimen,
        set=g_dgl.set,
    )


def _convert_dgl_graphs_data(graphs_data: list[GraphData]) -> list[SPTGraphData]:
    """Convert a list of DGLGraphs to CG-GNN cell graphs."""
    return [_convert_dgl_graph_data(g_dgl) for g_dgl in graphs_data]


def _handle_random_seed_values(random_seed_value: str | None) -> int | None:
    if (random_seed_value is not None) and (str(random_seed_value).strip().lower() != "none"):
        return int(random_seed_value)
    return None


if __name__ == '__main__':
    args = parse_arguments()
    config_file = ConfigParser()
    config_file.read(args.config_file)
    random_seed: int | None = None
    if 'general' in config_file:
        random_seed = _handle_random_seed_values(config_file['general'].get('random_seed', None))
    if 'cg-gnn' not in config_file:
        warn('No cg-gnn section in config file. Using default values.')
        config_file.read(DEFAULT_CONFIG_FILE)
    config = config_file['cg-gnn']

    in_ram: bool = config.getboolean('in_ram', True)
    batch_size: int = config.getint('batch_size', 32)
    epochs: int = config.getint('epochs', 10)
    learning_rate: float = config.getfloat('learning_rate', 1e-3)
    k_folds: int = config.getint('k_folds', 5)
    explainer: str = config.get('explainer', 'pp')
    merge_rois: bool = config.getboolean('merge_rois', True)
    if random_seed is None:
        random_seed = _handle_random_seed_values(config.get('random_seed', None))

    spt_graphs, _ = load_hs_graphs(args.input_directory)
    save_cell_graphs(_convert_spt_graphs_data(spt_graphs), args.output_directory)

    model, graphs_data, hs_id_to_importances = train_and_evaluate(args.output_directory,
                                                                  in_ram,
                                                                  batch_size,
                                                                  epochs,
                                                                  learning_rate,
                                                                  k_folds,
                                                                  explainer,
                                                                  merge_rois,
                                                                  random_seed)

    save_hs_graphs(_convert_dgl_graphs_data(load_cell_graphs(args.output_directory)[0]),
                   args.output_directory)
    for filename in ('graphs.bin', 'graph_info.pkl'):
        graphs_file = join(args.output_directory, filename)
        if exists(graphs_file):
            remove(graphs_file)
