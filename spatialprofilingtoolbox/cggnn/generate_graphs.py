"""Generates graphs from SPT extracts."""

from os import makedirs
from os.path import join, exists
from random import shuffle, randint
from warnings import warn
from typing import DefaultDict

from torch import FloatTensor, IntTensor  # pylint: disable=no-name-in-module
from numpy import (
    rint,
    median,
    prod,  # type: ignore
    percentile,  # type: ignore
    argmin,
    nonzero,
    savetxt,
    int_,
)
from numpy.typing import NDArray
from dgl import DGLGraph, graph  # type: ignore
from sklearn.neighbors import kneighbors_graph  # type: ignore
from pandas import DataFrame
from scipy.spatial.distance import pdist, squareform
from tqdm import tqdm

from spatialprofilingtoolbox.cggnn.util import (
    GraphData,
    save_cell_graphs,
    load_cell_graphs,
    set_seeds,
)
from spatialprofilingtoolbox.cggnn.util.constants import (
    CENTROIDS,
    FEATURES,
    INDICES,
    SETS,
    SETS_type,
)


def generate_graphs(
    df_cell: DataFrame,
    df_label: DataFrame,
    validation_data_percent: int,
    test_data_percent: int,
    use_channels: bool = True,
    use_phenotypes: bool = True,
    roi_side_length: int | None = None,
    cells_per_slide_target: int | None = 10_000,
    max_cells_to_consider: int = 100_000,
    target_name: str | None = None,
    output_directory: str | None = None,
    random_seed: int | None = None,
    include_unlabeled: bool = False,
) -> tuple[list[GraphData], list[str]]:
    """Generate cell graphs from SPT server extracts and save to disk if requested.

    Parameters
    ----------
    df_cell: DataFrame
        Rows are individual cells, indexed by an integer ID.
        Column or column groups are, named and in order:
            1. The 'specimen' the cell is from
            2. Cell centroid positions 'pixel x' and 'pixel y'
            3. Channel expressions starting with 'C ' and followed by a human-readable symbol
            4. Phenotype expressions starting with 'P ' followed by a symbol
    df_label: DataFrame
        Rows are specimens, the sole column 'label' is its class label as an integer.
    validation_data_percent: int
    test_data_percent: int
        Percent of regions of interest (ROIs) to reserve for the validation and test sets. Actual
        percentage of ROIs may not match because different specimens may yield different ROI counts,
        and the splitting process ensures that ROIs from the same specimen are not split among
        different train/validation/test sets.
        Set validation_data_percent to 0 if you want to do k-fold cross-validation later.
        (Training data percent is calculated from these two percentages.)
    use_channels: bool = True
    use_phenotypes: bool = True
        Whether to include channel or phenotype features (columns in df_cell beginning with 'C ' and
        'P ', respectively) in the graph.
    roi_side_length: int | None = None
    cells_per_slide_target: int | None = 10_000
        One of these must be provided in order to determine the ROI size. roi_side_length specifies
        how long to make the side length of each square ROI, in pixels. If this isn't provided, the
        median cell density across all slides is used with cells_per_slide_target to determine the
        square ROI sizing.
    max_cells_to_consider: int = 100_000
        The maximum number of cells to consider when placing ROI bounds. All cells within each
        boundary region will be included in the graph, but the ROI's center will be based on the
        cell with the most and closest cells within the specified ROI size.
        Empirically 350,000 works but 400,000 gives a 1.75 TB square and an out of memory error.
    target_name: str | None = None
        If provided, decide ROI placement based on only cells with this channel or phenotype. (All
        cells will be included in the ROI, but the density of cells with this channel or phenotype
        will decide where each cell is placed.) Should be a column name in df_feat_all_specimens.
        If not provided, simply orient ROIs where all cells are densest.
    output_directory: str | None = None
        If provided, save the graphs to disk in the specified directory.
    random_seed: int | None = None
        If provided, set the random seed to make the train/test/validation split deterministic.

    Returns
    -------
    graphs_data: list[GraphData]
    feature_names: list[str]
        The names of the features in graph.ndata['features'] in the order they appear in the array.
    """
    if not 0 <= validation_data_percent < 100:
        raise ValueError(
            f"Validation set percentage must be between 0 and 100, not {validation_data_percent}%."
        )
    if not 0 <= test_data_percent < 100:
        raise ValueError(
            f"Test set percentage must be between 0 and 100, not {test_data_percent}%."
        )
    train_data_percent = validation_data_percent + test_data_percent
    if not 0 <= train_data_percent < 100:
        raise ValueError(
            "Remaining data set percentage for training use must be between 0 and 100, not "
            f"{train_data_percent}%."
        )
    p_validation: float = validation_data_percent/100
    p_test: float = test_data_percent/100
    roi_size = None if roi_side_length is None else (roi_side_length, roi_side_length)

    if random_seed is not None:
        set_seeds(random_seed)

    # Ensure output directory is created and check if graphs have already been generated
    if output_directory is not None:
        makedirs(output_directory, exist_ok=True)
        feature_names_path = join(output_directory, 'feature_names.txt')
        if exists(join(output_directory, 'graphs.bin')) and \
            exists(join(output_directory, 'graph_info.pkl')) and \
                exists(feature_names_path):
            warn('Graphs already exist in output directory. Loading from file.')
            return load_cell_graphs(output_directory)

    graphs_by_label_and_specimen, graph_names, feature_names = _create_graphs_from_spt(
        df_cell,
        df_label,
        use_channels=use_channels,
        use_phenotypes=use_phenotypes,
        roi_size=roi_size,
        cells_per_slide_target=cells_per_slide_target,
        max_cells_to_consider=max_cells_to_consider,
        target_name=target_name,
        include_unlabeled=include_unlabeled,
    )
    specimen_to_set = _split_rois(graphs_by_label_and_specimen, p_validation, p_test)
    graphs_data: list[GraphData] = _assemble_graph_data(
        graphs_by_label_and_specimen,
        graph_names,
        specimen_to_set,
    )
    print(_report_dataset_statistics(graphs_data))
    if output_directory is not None:
        save_cell_graphs(graphs_data, output_directory)
        savetxt(join(output_directory, 'feature_names.txt'), feature_names, fmt='%s', delimiter=',')
    return graphs_data, feature_names


def _create_graphs_from_spt(
    df_cell: DataFrame,
    df_label: DataFrame,
    use_channels: bool = True,
    use_phenotypes: bool = True,
    roi_size: tuple[int, int] | None = None,
    cells_per_slide_target: int | None = 5_000,
    max_cells_to_consider: int = 100_000,
    target_name: str | None = None,
    n_neighbors: int = 5,
    threshold: int | None = None,
    include_unlabeled: bool = False,
) -> tuple[dict[int | None, dict[str, list[DGLGraph]]], dict[DGLGraph, str], list[str]]:
    """Create graphs from cell and label files created from SPT."""
    if df_label['label'].nunique() < 2:
        raise ValueError('Less than two unique labels. No point to training.')
    if (not use_channels) and (not use_phenotypes):
        raise ValueError('Must use at least one of channels or phenotypes.')

    features_to_use: list[str] = []
    channels = df_cell.columns[df_cell.columns.str.startswith('C ')]
    phenotypes = df_cell.columns[df_cell.columns.str.startswith('P ')]
    if use_channels:
        features_to_use.extend(channels)
    else:
        df_cell.drop(columns=channels, inplace=True)
    if use_phenotypes:
        features_to_use.extend(phenotypes)
    else:
        df_cell.drop(columns=phenotypes, inplace=True)
    if len(features_to_use) == 0:
        raise ValueError('No features to use.')

    # Split the data by specimen (slide) and derive the roi_size from the average cell density if
    # not provided
    graphs_by_specimen: dict[str, list[DGLGraph]] = DefaultDict(list)
    roi_names: dict[DGLGraph, str] = {}
    grouped = df_cell.groupby('specimen')
    if roi_size is not None:
        roi_area = prod(roi_size)
    elif cells_per_slide_target is not None:
        roi_area: float = cells_per_slide_target / median([
            (df_specimen.shape[0] / prod(
                df_specimen[['pixel x', 'pixel y']].max() -
                df_specimen[['pixel x', 'pixel y']].min()
            )) for _, df_specimen in grouped
        ])
        roi_size = (rint(roi_area**0.5), rint(roi_area**0.5))
    else:
        raise ValueError('Must specify either roi_size or cells_per_slide_target.')
    print('Creating graphs for identified regions in each specimen...')
    for specimen, df_specimen in tqdm(grouped):

        # Skip specimens without labels
        if (not include_unlabeled) and (specimen not in df_label.index):
            continue

        # Normalize slide coordinates
        df_specimen[['pixel x', 'pixel y']] -= df_specimen[['pixel x', 'pixel y']].min()

        # Initialize data structures
        bounding_boxes: list[tuple[int, int, int, int, int, int]] = []
        slide_size = df_specimen[['pixel x', 'pixel y']].max() + 100
        if target_name is not None:
            proportion_of_target = df_specimen[target_name].sum()/df_specimen.shape[0]
            df_target = df_specimen.loc[df_specimen[target_name], :]
        else:
            proportion_of_target = 1.
            df_target = df_specimen
        if df_target.shape[0] > max_cells_to_consider:
            df_target = df_target.sample(max_cells_to_consider)
        distance_square = squareform(pdist(df_target[['pixel x', 'pixel y']]))
        slide_area = prod(slide_size)

        # Create as many ROIs such that the total area of the ROIs will equal the area of the source
        # image times the proportion of cells on that image that have the target phenotype
        n_rois = rint(proportion_of_target * slide_area / roi_area)
        while (len(bounding_boxes) < n_rois) and (df_target.shape[0] > 0):
            p_dist = percentile(distance_square, proportion_of_target, axis=0)
            x, y = df_target.iloc[argmin(p_dist), :][['pixel x', 'pixel y']].tolist()
            x_min = x - roi_size[0]//2
            x_max = x + roi_size[0]//2
            y_min = y - roi_size[1]//2
            y_max = y + roi_size[1]//2

            # Check that this bounding box contains enough cells to do nearest neighbors on
            if (
                df_specimen['pixel x'].between(x_min, x_max) &
                df_specimen['pixel y'].between(y_min, y_max)
            ).sum() < n_neighbors + 1:
                # If not, terminate the ROI creation process early
                break

            # Log the new bounding box and track which and how many cells haven't been captured yet
            bounding_boxes.append((x_min, x_max, y_min, y_max, x, y))
            proportion_of_target -= roi_area / slide_area
            cells_not_yet_captured = ~(
                df_target['pixel x'].between(x_min, x_max) &
                df_target['pixel y'].between(y_min, y_max)
            )
            df_target = df_target.loc[cells_not_yet_captured, :]
            distance_square = distance_square[cells_not_yet_captured, :][:, cells_not_yet_captured]

        # Create features, centroid, and label arrays and then the graph
        for i, (x_min, x_max, y_min, y_max, x, y) in enumerate(bounding_boxes):
            df_roi: DataFrame = df_specimen.loc[
                df_specimen['pixel x'].between(x_min, x_max) &
                df_specimen['pixel y'].between(y_min, y_max),
            ]
            centroids = df_roi[['pixel x', 'pixel y']].values
            features = df_roi[features_to_use].astype(int).values
            graph_instance = _create_graph(
                df_roi.index.to_numpy(), centroids, features, n_neighbors=n_neighbors,
                threshold=threshold)
            graphs_by_specimen[specimen].append(graph_instance)
            roi_names[graph_instance] = \
                f'melanoma_{specimen}_{i}_{roi_size[0]}x{roi_size[1]}_x{x}_y{y}'

        print(f'Created {len(bounding_boxes)} ROI(s) from specimen {specimen}.')

    # Split the graphs by specimen and label
    graphs_by_label_and_specimen: dict[int | None, dict[str, list[DGLGraph]]] = DefaultDict(dict)
    for specimen, graphs in graphs_by_specimen.items():
        label: int | None
        if include_unlabeled:
            label = df_label.loc[specimen, 'label'] if (specimen in df_label.index) else None
        else:
            label = df_label.loc[specimen, 'label']
        graphs_by_label_and_specimen[label][specimen] = graphs
    return graphs_by_label_and_specimen, roi_names, features_to_use


def _create_graph(
    node_indices: NDArray[int_],
    centroids: NDArray[int_],
    features: NDArray[int_],
    n_neighbors: int = 5,
    threshold: int | None = None,
) -> DGLGraph:
    """Generate the graph topology from the provided instance_map using (thresholded) kNN.

    Parameters
    ----------
    node_indices: NDArray[int_]
        Indices for each node.
    centroids: NDArray[int_]
        Node centroids
    features: NDArray[int_]
        Features of each node based on chemical channels.
    n_neighbors: int
        Number of neighbors. Defaults to 5.
    threshold: int | None
        Maximum allowed distance between 2 nodes. Defaults to None (no thresholding).
    Returns:
        DGLGraph: The constructed graph
    """
    # add nodes
    num_nodes = features.shape[0]
    graph_instance = graph([])
    graph_instance.add_nodes(num_nodes)
    graph_instance.ndata[INDICES] = IntTensor(node_indices)
    graph_instance.ndata[CENTROIDS] = FloatTensor(centroids)
    graph_instance.ndata[FEATURES] = FloatTensor(features)
    # Note: channels and phenotypes are binary variables, but DGL only supports FloatTensors

    # build kNN adjacency
    adj = kneighbors_graph(
        centroids,
        n_neighbors,
        mode="distance",
        include_self=False,
        metric="euclidean",
    ).toarray()

    # filter edges that are too far (i.e., larger than the threshold)
    if threshold is not None:
        adj[adj > threshold] = 0

    edge_list = nonzero(adj)
    graph_instance.add_edges(list(edge_list[0]), list(edge_list[1]))

    return graph_instance


def _split_rois(
    graphs_by_label_and_specimen: dict[int | None, dict[str, list[DGLGraph]]],
    p_validation: float,
    p_test: float,
) -> dict[str, SETS_type | None]:
    """Randomly allocate graphs to train, validation, and test sets."""
    p_train = 1 - p_validation - p_test
    specimen_to_set: dict[str, SETS_type | None] = {}

    # Shuffle the order of the specimens in each class and divvy them up.
    for label, graphs_by_specimen in graphs_by_label_and_specimen.items():

        # Separate out unlabeled specimens
        if label is None:
            for specimen in graphs_by_specimen:
                specimen_to_set[specimen] = None
            continue

        # Stuff
        n_graphs = sum(len(l) for l in graphs_by_specimen.values())
        if n_graphs == 0:
            warn(f'Class {label} doesn\'t have any examples.')
            continue
        specimens = list(graphs_by_specimen.keys())
        shuffle(specimens)

        # If there's at least one specimen of this class, add it to the training set.
        specimen = specimens[0]
        specimen_to_set[specimen] = SETS[0]
        n_specimens = len(specimens)
        if n_specimens == 1:
            warn(f'Class {label} only has one specimen. Allocating to training set.')
        elif n_specimens == 2:
            specimen = specimens[1]
            if (p_validation == 0) and (p_test == 0):
                specimen_to_set[specimen] = SETS[0]
            elif p_test == 0:
                specimen_to_set[specimen] = SETS[1]
            elif p_validation == 0:
                specimen_to_set[specimen] = SETS[2]
            else:
                warn(f'Class {label} only has two specimens. '
                     'Allocating one for training and the other randomly to validation or test.')
                if randint(0, 1) == 0:
                    specimen_to_set[specimen] = SETS[1]
                else:
                    specimen_to_set[specimen] = SETS[2]
        else:
            # Prepare to iterate through the remaining specimens.
            i_specimen: int = 1
            specimen = specimens[i_specimen]

            # Allocate at least one specimen to each of the validation and test sets if necessary.
            n_allocated_val = 0
            n_allocated_test = 0
            if p_validation > 0:
                specimen_to_set[specimen] = SETS[1]
                n_allocated_val = len(graphs_by_specimen[specimen])
                i_specimen += 1
                specimen = specimens[i_specimen]
            if p_test > 0:
                specimen_to_set[specimen] = SETS[2]
                n_allocated_test = len(graphs_by_specimen[specimen])
                i_specimen += 1

            # Calculate the number of ROIs we want in the train/test/validation sets, correcting
            # for how there's already one specimen allocated to each.
            n_train_target = n_graphs*p_train - len(graphs_by_specimen[specimens[0]])
            n_validation_target = n_graphs*p_validation - n_allocated_val
            n_test_target = n_graphs*p_test - n_allocated_test
            if (n_train_target < 0) or (n_validation_target < 0) or (n_test_target < 0):
                which_sets: list[str] = []
                if n_train_target < 0:
                    which_sets.append('train')
                if n_validation_target < 0:
                    which_sets.append('validation')
                if n_test_target < 0:
                    which_sets.append('test')
                warn(
                    f'Class {label} doesn\'t have enough specimens to maintain the specified '
                    f'{"/".join(which_sets)} proportion. Consider adding more specimens of this '
                    'class and/or increasing their allocation percentage.'
                )

            # Finish the allocation.
            # This method prioritizes bolstering the training and validation sets in that order.
            n_used_of_remainder = 0
            for specimen in specimens[i_specimen:]:
                specimen_files = graphs_by_specimen[specimen]
                if n_used_of_remainder < n_train_target:
                    specimen_to_set[specimen] = SETS[0]
                elif n_used_of_remainder < n_train_target + n_validation_target:
                    specimen_to_set[specimen] = SETS[1]
                else:
                    specimen_to_set[specimen] = SETS[2]
                n_used_of_remainder += len(specimen_files)

    return specimen_to_set


def _assemble_graph_data(
    graphs_by_label_and_specimen: dict[int | None, dict[str, list[DGLGraph]]],
    graph_names: dict[DGLGraph, str],
    specimen_to_set: dict[str, SETS_type | None],
) -> list[GraphData]:
    graph_data: list[GraphData] = []
    for label, graphs_by_specimen in graphs_by_label_and_specimen.items():
        for specimen, graph_list in graphs_by_specimen.items():
            set_name = specimen_to_set[specimen]
            for graph_instance in graph_list:
                graph_data.append(GraphData(
                    graph_instance,
                    label,
                    graph_names[graph_instance],
                    specimen,
                    set_name,
                ))
    return graph_data


def _report_dataset_statistics(graphs_data: list[GraphData]) -> DataFrame:
    df = DataFrame(columns=['label', 'set', 'count'])
    for graph_instance in graphs_data:
        if graph_instance.specimen in df.index:
            df.loc[graph_instance.specimen, 'count'] += 1
        else:
            df.loc[graph_instance, :] = [graph_instance.label, graph_instance.set, 1]
    return df.groupby(['set', 'label']).sum()
