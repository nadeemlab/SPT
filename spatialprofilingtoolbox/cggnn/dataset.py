"""PyTorch Dataset and DataLoader objects for cell graphs."""

from typing import Sequence

from torch.utils.data import ConcatDataset, DataLoader, SubsetRandomSampler
from torch.utils.data import Dataset
from torch.cuda import is_available
from dgl import DGLGraph  # type: ignore
from sklearn.model_selection import KFold

from spatialprofilingtoolbox.cggnn.util import GraphData, split_graph_sets, collate  # type: ignore

# cuda support
IS_CUDA = is_available()
DEVICE = 'cuda:0' if IS_CUDA else 'cpu'


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
    graphs_data: list[GraphData],
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
