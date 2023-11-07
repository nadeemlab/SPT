"""PyTorch Dataset and DataLoader objects for cell graphs."""

from typing import List, Optional, Sequence, Tuple, Callable

from torch.utils.data import ConcatDataset, DataLoader, SubsetRandomSampler
from dgl import DGLGraph
from sklearn.model_selection import KFold

from spatialprofilingtoolbox.cggnn.util import CGDataset, GraphData, split_graph_sets, collate


def create_datasets(
    graphs_data: List[GraphData],
    in_ram: bool = True,
    k_folds: int = 3
) -> Tuple[CGDataset, Optional[CGDataset], Optional[CGDataset], Optional[KFold]]:
    """Make the cell and/or tissue graph datasets and the k-fold if necessary."""
    cell_graph_sets = split_graph_sets(graphs_data)
    train_dataset: Optional[CGDataset] = \
        _create_dataset(cell_graph_sets[0][0], cell_graph_sets[0][1], in_ram)
    assert train_dataset is not None
    validation_dataset = _create_dataset(cell_graph_sets[1][0], cell_graph_sets[1][1], in_ram)
    test_dataset = _create_dataset(cell_graph_sets[2][0], cell_graph_sets[2][1], in_ram)

    if (k_folds > 0) and (validation_dataset is not None):
        # stack train and validation datasets if both exist and k-fold cross validation is on
        train_dataset = ConcatDataset((train_dataset, validation_dataset))
        validation_dataset = None
    elif (k_folds == 0) and (validation_dataset is None):
        # set k_folds to 3 if not provided and no validation data is provided
        k_folds = 3
    kfold = KFold(n_splits=k_folds, shuffle=True) if k_folds > 0 else None

    return train_dataset, validation_dataset, test_dataset, kfold


def _create_dataset(cell_graphs: List[DGLGraph],
                    cell_graph_labels: Optional[List[int]] = None,
                    in_ram: bool = True
                    ) -> Optional[CGDataset]:
    """Make a cell graph dataset."""
    return CGDataset(cell_graphs, cell_graph_labels, load_in_ram=in_ram) \
        if (len(cell_graphs) > 0) else None


def create_training_dataloaders(train_ids: Optional[Sequence[int]],
                                test_ids: Optional[Sequence[int]],
                                train_dataset: CGDataset,
                                validation_dataset: Optional[CGDataset],
                                batch_size: int
                                ) -> Tuple[DataLoader, DataLoader]:
    """Determine whether to k-fold and then create dataloaders."""
    if (train_ids is None) or (test_ids is None):
        if validation_dataset is None:
            raise ValueError("validation_dataset must exist.")
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate
        )
        validation_dataloader = DataLoader(
            validation_dataset,
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate
        )
    else:
        if validation_dataset is not None:
            raise ValueError(
                "validation_dataset provided but k-folding of training dataset requested.")
        train_subsampler = SubsetRandomSampler(train_ids)
        test_subsampler = SubsetRandomSampler(test_ids)
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=train_subsampler,
            collate_fn=collate
        )
        validation_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=test_subsampler,
            collate_fn=collate
        )

    return train_dataloader, validation_dataloader
