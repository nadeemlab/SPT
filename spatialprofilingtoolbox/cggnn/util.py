"""Histological structure graph dataset utility functions."""

from os import makedirs
from os.path import join
from pickle import dump, load
from json import load as json_load
from random import seed
from typing import NamedTuple, Literal
from dataclasses import dataclass, field

from numpy import (
    loadtxt,
    int_,
    float_,
)
from numpy.random import seed as np_seed
from numpy.typing import NDArray
from scipy.sparse import spmatrix, save_npz, load_npz  # type: ignore

SETS = ('train', 'validation', 'test')
SETS_type = Literal['train', 'validation', 'test']


def load_label_to_result(path: str) -> dict[int, str]:
    """Read in label_to_result JSON."""
    return {int(label): result for label, result in json_load(
        open(path, encoding='utf-8')).items()}


@dataclass
class HSGraph:
    """A histological structure graph instance."""
    adj: spmatrix
    node_features: NDArray[float_]
    centroids: NDArray[float_]
    histological_structure_ids: NDArray[int_]
    importances: NDArray[float_] | None = field(default=None)


class GraphData(NamedTuple):
    """Data relevant to a histological structure graph instance."""
    graph: HSGraph
    label: int | None
    name: str
    specimen: str
    set: SETS_type | None


def save_hs_graphs(graphs_data: list[GraphData], output_directory: str) -> None:
    """Save histological structure graphs to a directory.

    Saves the adjacency graph separately from the rest of the graph data for compatibility.
    """
    makedirs(output_directory, exist_ok=True)
    for i, gd in enumerate(graphs_data):
        save_npz(join(output_directory, f'graph_{i}_adj.npz'), gd.graph.adj)
    with open(join(output_directory, 'graphs.pkl'), 'wb') as f:
        for gd in graphs_data:
            gd.graph.adj = None  # type: ignore
        dump(graphs_data, f)


def load_hs_graphs(graph_directory: str) -> tuple[list[GraphData], list[str]]:
    """Load histological structure graphs from a directory.

    Assumes directory contains the files `graphs.pkl`, `feature_names.txt`, and a sparse array for
    every graph in `graphs.pkl`.
    """
    with open(join(graph_directory, 'graphs.pkl'), 'rb') as f:
        graphs_data: list[GraphData] = load(f)
    for i, gd in enumerate(graphs_data):
        gd.graph.adj = load_npz(join(graph_directory, f'graph_{i}_adj.npz'))
    feature_names: list[str] = loadtxt(
        join(graph_directory, 'feature_names.txt'),
        dtype=str,
        delimiter=',',
    ).tolist()
    return graphs_data, feature_names


def split_graph_sets(graphs_data: list[GraphData]) -> tuple[
    tuple[list[HSGraph], list[int]],
    tuple[list[HSGraph], list[int]],
    tuple[list[HSGraph], list[int]],
    list[HSGraph],
]:
    """Split graph data list into train, validation, test, and unlabeled sets."""
    cg_train: tuple[list[HSGraph], list[int]] = ([], [])
    cg_val: tuple[list[HSGraph], list[int]] = ([], [])
    cg_test: tuple[list[HSGraph], list[int]] = ([], [])
    cg_unlabeled: list[HSGraph] = []
    for gd in graphs_data:
        if gd.label is None:
            cg_unlabeled.append(gd.graph)
            continue
        which_set: tuple[list[HSGraph], list[int]] = cg_train
        if gd.set == 'validation':
            which_set = cg_val
        elif gd.set == 'test':
            which_set = cg_test
        which_set[0].append(gd.graph)
        which_set[1].append(gd.label)
    return cg_train, cg_val, cg_test, cg_unlabeled


def set_seeds(random_seed: int) -> None:
    """Set random seeds for all libraries."""
    seed(random_seed)
    np_seed(random_seed)
