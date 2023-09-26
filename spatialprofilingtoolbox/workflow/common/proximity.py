"""Low-level calculations of proximity metric."""

from math import isnan

from pandas import DataFrame
from sklearn.neighbors import BallTree  # type: ignore
from numpy import logical_and

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def compute_proximity_metric_for_signature_pair(
    signature1: PhenotypeCriteria,
    signature2: PhenotypeCriteria,
    radius: float,
    cells: DataFrame,
    tree: BallTree,
) -> float | None:
    cells = cells.rename({
        column: (column[2:] if (column.startswith('C ') or column.startswith('P ')) else column)
        for column in cells.columns
    }, axis=1)
    mask1 = cells.astype(bool)[signature1.positive_markers].all(axis=1) & \
        (~(cells.astype(bool))[signature1.negative_markers]).all(axis=1)
    mask2 = cells.astype(bool)[signature2.positive_markers].all(axis=1) & \
        (~(cells.astype(bool))[signature2.negative_markers]).all(axis=1)
    source_count = sum(mask1)

    if source_count == 0:
        return None
    source_cell_locations = cells.loc[mask1, ['pixel x', 'pixel y']]
    within_radius_indices_list = tree.query_radius(
        source_cell_locations,
        radius,
        return_distance=False,
    )
    counts = [
        sum(mask2.iloc[integer_index] for integer_index in list(integer_indices))
        for integer_indices in within_radius_indices_list
    ]
    count = sum(counts) - sum(logical_and(mask1, mask2))
    return count / source_count


def _validate_value(value) -> bool:
    if (not isinstance(value, float)) and (not isinstance(value, int)):
        return False
    if value is None:
        return False
    if isnan(value):
        return False
    return True


def stage_proximity_feature_values(
    feature_uploader,
    feature_values,
    sample_identifier,
) -> None:
    for _, row in feature_values.iterrows():
        specifiers = (
            row['Phenotype 1'],
            row['Phenotype 2'],
            row['Pixel radius'],
        )
        value = row['Proximity']
        if _validate_value(value):
            feature_uploader.stage_feature_value(specifiers, sample_identifier, value)
