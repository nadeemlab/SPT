"""Helper functions to translate SPT HSGraphs and prepare them for CG-GNN training."""

from typing import Callable, Sequence, NamedTuple

from numpy import nonzero  # type: ignore
from scipy.sparse import csr_matrix  # type: ignore
from networkx import to_scipy_sparse_array  # type: ignore
from torch import (
    Tensor,  # type: ignore
    FloatTensor,
    LongTensor,  # type: ignore
    IntTensor,  # type: ignore
    manual_seed,  # type: ignore
    use_deterministic_algorithms,
)
from torch.backends import cudnn  # type: ignore
from torch.cuda import is_available, manual_seed_all
from torch.cuda import manual_seed as cuda_manual_seed  # type: ignore
from torch.utils.data import ConcatDataset, DataLoader, SubsetRandomSampler
from torch.utils.data import Dataset
from dgl import DGLGraph, graph, batch  # type: ignore
from dgl import seed as dgl_seed  # type: ignore
from sklearn.model_selection import KFold

from spatialprofilingtoolbox.graphs.util import GraphData as SPTGraphData
from spatialprofilingtoolbox.graphs.util import HSGraph, split_graph_sets, SETS_type


INDICES = 'histological_structure'
FEATURES = 'features'
CENTROIDS = 'centroid'
IMPORTANCES = 'importance'

# cuda support
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


class DGLGraphData(NamedTuple):
    """Data relevant to a cell graph instance."""
    graph: DGLGraph
    label: int | None
    name: str
    specimen: str
    set: SETS_type | None


def convert_spt_graph(g_spt: HSGraph) -> DGLGraph:
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


def convert_spt_graph_data(g_spt: SPTGraphData) -> DGLGraphData:
    """Convert a SPT GraphData object to a CG-GNN/DGL GraphData object."""
    return DGLGraphData(
        graph=convert_spt_graph(g_spt.graph),
        label=g_spt.label,
        name=g_spt.name,
        specimen=g_spt.specimen,
        set=g_spt.set,
    )


def convert_spt_graphs_data(graphs_data: list[SPTGraphData]) -> list[DGLGraphData]:
    """Convert a list of SPT HSGraphs to CG-GNN cell graphs."""
    return [convert_spt_graph_data(g_spt) for g_spt in graphs_data]


def convert_dgl_graph(g_dgl: DGLGraph) -> HSGraph:
    """Convert a DGLGraph to a CG-GNN cell graph."""
    return HSGraph(
        adj=to_scipy_sparse_array(g_dgl.to_networkx()),
        node_features=g_dgl.ndata[FEATURES],
        centroids=g_dgl.ndata[CENTROIDS],
        histological_structure_ids=g_dgl.ndata[INDICES],
        importances=g_dgl.ndata[IMPORTANCES] if (IMPORTANCES in g_dgl.ndata) else None,
    )


def convert_dgl_graph_data(g_dgl: DGLGraphData) -> SPTGraphData:
    return SPTGraphData(
        graph=convert_dgl_graph(g_dgl.graph),
        label=g_dgl.label,
        name=g_dgl.name,
        specimen=g_dgl.specimen,
        set=g_dgl.set,
    )


def convert_dgl_graphs_data(graphs_data: list[DGLGraphData]) -> list[SPTGraphData]:
    """Convert a list of DGLGraphs to CG-GNN cell graphs."""
    return [convert_dgl_graph_data(g_dgl) for g_dgl in graphs_data]


class CGDataset(Dataset):
    """Cell graph dataset."""

    def __init__(
        self,
        cell_graphs: list[DGLGraph],
        cell_graph_labels: list[int] | None = None,
        load_in_ram: bool = False,
    ):
        """Cell graph dataset constructor.

        Args:
            cell_graphs: list[DGLGraph]
                Cell graphs for a given split (e.g., test).
            cell_graph_labels: list[int] | None
                Labels for the cell graphs. Optional.
            load_in_ram: bool = False
                Whether to load the graphs in RAM. Defaults to False.
        """
        super(CGDataset, self).__init__()

        self.cell_graphs = cell_graphs
        self.cell_graph_labels = cell_graph_labels
        self.n_cell_graphs = len(self.cell_graphs)
        self.load_in_ram = load_in_ram

    def __getitem__(self, index: int) -> DGLGraph | tuple[DGLGraph, float]:
        """Get an example.

        Args:
            index (int): index of the example.
        """
        cell_graph = self.cell_graphs[index]
        if IS_CUDA:
            cell_graph = cell_graph.to('cuda:0')
        return cell_graph if (self.cell_graph_labels is None) \
            else (cell_graph, float(self.cell_graph_labels[index]))

    def __len__(self):
        """Return the number of samples in the dataset."""
        return self.n_cell_graphs


def create_datasets(
    graphs_data: list[DGLGraphData],
    in_ram: bool = True,
    k_folds: int = 3,
) -> tuple[CGDataset, CGDataset | None, CGDataset | None, KFold | None]:
    """Make the cell and/or tissue graph datasets and the k-fold if necessary."""
    cell_graph_sets = split_graph_sets(graphs_data)
    train_dataset: CGDataset | None = \
        create_dataset(cell_graph_sets[0][0], cell_graph_sets[0][1], in_ram)
    assert train_dataset is not None
    validation_dataset = create_dataset(cell_graph_sets[1][0], cell_graph_sets[1][1], in_ram)
    test_dataset = create_dataset(cell_graph_sets[2][0], cell_graph_sets[2][1], in_ram)

    if (k_folds > 0) and (validation_dataset is not None):
        # stack train and validation datasets if both exist and k-fold cross validation is on
        train_dataset = ConcatDataset((train_dataset, validation_dataset))
        validation_dataset = None
    elif (k_folds == 0) and (validation_dataset is None):
        # set k_folds to 3 if not provided and no validation data is provided
        k_folds = 3
    kfold = KFold(n_splits=k_folds, shuffle=True) if k_folds > 0 else None

    return train_dataset, validation_dataset, test_dataset, kfold


def create_dataset(
    cell_graphs: list[DGLGraph],
    cell_graph_labels: list[int] | None = None,
    in_ram: bool = True,
) -> CGDataset | None:
    """Make a cell graph dataset."""
    return CGDataset(cell_graphs, cell_graph_labels, load_in_ram=in_ram) \
        if (len(cell_graphs) > 0) else None


def create_training_dataloaders(
    train_ids: Sequence[int] | None,
    test_ids: Sequence[int] | None,
    train_dataset: CGDataset,
    validation_dataset: CGDataset | None,
    batch_size: int,
) -> tuple[DataLoader, DataLoader]:
    """Determine whether to k-fold and then create dataloaders."""
    if (train_ids is None) or (test_ids is None):
        if validation_dataset is None:
            raise ValueError("validation_dataset must exist.")
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate,
        )
        validation_dataloader = DataLoader(
            validation_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate,
        )
    else:
        if validation_dataset is not None:
            raise ValueError(
                "validation_dataset provided but k-folding of training dataset requested."
            )
        train_subsampler = SubsetRandomSampler(train_ids)
        test_subsampler = SubsetRandomSampler(test_ids)
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=train_subsampler,
            collate_fn=collate,
        )
        validation_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=test_subsampler,
            collate_fn=collate,
        )

    return train_dataloader, validation_dataloader


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
    manual_seed(random_seed)
    dgl_seed(random_seed)
    cuda_manual_seed(random_seed)
    manual_seed_all(random_seed)  # multi-GPU
    # use_deterministic_algorithms(True)
    # # multi_layer_gnn uses nondeterministic algorithm when on GPU
    # cudnn.deterministic = True
    cudnn.benchmark = False
