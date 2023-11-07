"""Cell/tissue graph dataset utility functions."""

from os.path import join
from json import load as json_load
from random import seed
from typing import NamedTuple, Callable

from numpy import loadtxt
from numpy.random import seed as np_seed
from torch import (
    Tensor,  # type: ignore
    LongTensor,  # type: ignore
    IntTensor,  # type: ignore
    manual_seed,  # type: ignore
    use_deterministic_algorithms,
)
from torch.cuda import is_available, manual_seed_all
from torch.cuda import manual_seed as cuda_manual_seed  # type: ignore
from torch.backends import cudnn  # type: ignore
from dgl import batch, DGLGraph  # type: ignore
from dgl import seed as dgl_seed  # type: ignore
from dgl.data.utils import (  # type: ignore
    save_graphs,  # type: ignore
    save_info,  # type: ignore
    load_graphs,  # type: ignore
    load_info,  # type: ignore
)

from spatialprofilingtoolbox.cggnn.util.constants import SETS_type


IS_CUDA = is_available()
DEVICE = 'cuda:0' if IS_CUDA else 'cpu'
COLLATE_USING: dict[str, Callable] = {
    'DGLGraph': batch,
    'DGLHeteroGraph': batch,
    'Tensor': lambda x: x,
    'int': lambda x: IntTensor(x).to(DEVICE),
    'int64': lambda x: IntTensor(x).to(DEVICE),
    'float': lambda x: LongTensor(x).to(DEVICE),
}


def load_label_to_result(path: str) -> dict[int, str]:
    """Read in label_to_result JSON."""
    return {int(label): result for label, result in json_load(
        open(path, encoding='utf-8')).items()}


class GraphData(NamedTuple):
    """Data relevant to a cell graph instance."""
    graph: DGLGraph
    label: int | None
    name: str
    specimen: str
    set: SETS_type | None


class GraphMetadata(NamedTuple):
    """Data relevant to a cell graph instance."""
    name: str
    specimen: str
    set: SETS_type | None


def save_cell_graphs(graphs_data: list[GraphData], output_directory: str) -> None:
    """Save cell graphs to a directory."""
    graphs: list[DGLGraph] = []
    labels: list[int] = []
    metadata: list[GraphMetadata] = []
    unlabeled_graphs: list[DGLGraph] = []
    unlabeled_metadata: list[GraphMetadata] = []
    for graph_data in graphs_data:
        if graph_data.label is not None:
            graphs.append(graph_data.graph)
            metadata.append(GraphMetadata(
                graph_data.name,
                graph_data.specimen,
                graph_data.set,
            ))
            labels.append(graph_data.label)
        else:
            unlabeled_graphs.append(graph_data.graph)
            unlabeled_metadata.append(GraphMetadata(
                graph_data.name,
                graph_data.specimen,
                graph_data.set,
            ))
    _save_dgl_graphs(
        output_directory,
        graphs + unlabeled_graphs,
        metadata + unlabeled_metadata,
        labels,
    )


def _save_dgl_graphs(
    output_directory: str,
    graphs: list[DGLGraph],
    metadata: list[GraphMetadata],
    labels: list[int],
) -> None:
    """Save DGL cell graphs to a directory."""
    save_graphs(join(output_directory, 'graphs.bin'),
                graphs,
                {'labels': IntTensor(labels)})
    save_info(join(output_directory, 'graph_info.pkl'), {'info': metadata})


def load_cell_graphs(graph_directory: str) -> tuple[list[GraphData], list[str]]:
    """Load cell graph information from a directory.

    Assumes directory contains the files `graphs.bin`, `graph_info.pkl`, and `feature_names.txt`.
    """
    graphs, labels, metadata = _load_dgl_graphs(graph_directory)
    graph_data: list[GraphData] = []
    for i, graph in enumerate(graphs):
        graph_data.append(GraphData(
            graph,
            labels[i] if i < len(labels) else None,
            metadata[i].name,
            metadata[i].specimen,
            metadata[i].set,
        ))
    feature_names: list[str] = loadtxt(
        join(graph_directory, 'feature_names.txt'),
        dtype=str,
        delimiter=',',
    ).tolist()
    return graph_data, feature_names


def _load_dgl_graphs(graph_directory: str) -> tuple[list[DGLGraph], list[int], list[GraphMetadata]]:
    """Load cell graphs saved as DGL files from a directory."""
    graphs, labels = load_graphs(join(graph_directory, 'graphs.bin'))
    graphs: list[DGLGraph]
    labels: dict[str, IntTensor]
    metadata: list[GraphMetadata] = load_info(join(graph_directory, 'graph_info.pkl'))['info']
    return graphs, labels['labels'].tolist(), metadata


def split_graph_sets(graphs_data: list[GraphData]) -> tuple[
    tuple[list[DGLGraph], list[int]],
    tuple[list[DGLGraph], list[int]],
    tuple[list[DGLGraph], list[int]],
    list[DGLGraph],
]:
    """Split graph data list into train, validation, test, and unlabeled sets."""
    cg_train: tuple[list[DGLGraph], list[int]] = ([], [])
    cg_val: tuple[list[DGLGraph], list[int]] = ([], [])
    cg_test: tuple[list[DGLGraph], list[int]] = ([], [])
    cg_unlabeled: list[DGLGraph] = []
    for gd in graphs_data:
        if gd.label is None:
            cg_unlabeled.append(gd.graph)
            continue
        which_set: tuple[list[DGLGraph], list[int]] = cg_train
        if gd.set == 'validation':
            which_set = cg_val
        elif gd.set == 'test':
            which_set = cg_test
        which_set[0].append(gd.graph)
        which_set[1].append(gd.label)
    return cg_train, cg_val, cg_test, cg_unlabeled


def collate(example_batch: Tensor) -> tuple[tuple, LongTensor]:
    """Collate a batch.

    Args:
        example_batch (torch.tensor): a batch of examples.
    Returns:
        data: (tuple)
        labels: (torch.LongTensor)
    """
    if isinstance(example_batch[0], tuple):  # graph and label
        def collate_fn(batch, id, type):
            return COLLATE_USING[type]([example[id] for example in batch])
        num_modalities = len(example_batch[0])
        return tuple([
            collate_fn(example_batch, mod_id, type(example_batch[0][mod_id]).__name__)
            for mod_id in range(num_modalities)
        ])
    else:  # graph only
        return tuple([COLLATE_USING[type(example_batch[0]).__name__](example_batch)])


def set_seeds(random_seed: int) -> None:
    """Set random seeds for all libraries."""
    seed(random_seed)
    np_seed(random_seed)
    manual_seed(random_seed)
    dgl_seed(random_seed)
    cuda_manual_seed(random_seed)
    manual_seed_all(random_seed)  # multi-GPU
    # use_deterministic_algorithms(True)
    # # multi_layer_gnn uses nondeterministic algorithm when on GPU
    # cudnn.deterministic = True
    cudnn.benchmark = False
