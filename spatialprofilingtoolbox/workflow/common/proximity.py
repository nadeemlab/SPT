"""Low-level calculations of proximity metric."""

from math import isnan
import re

from pandas import DataFrame
from sklearn.neighbors import BallTree  # type: ignore
from numpy import logical_and

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.workflow.common.cell_df_indexer import get_mask
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def compute_proximity_metric_for_signature_pair(
    signature1: PhenotypeCriteria,
    signature2: PhenotypeCriteria,
    radius: float,
    cells: DataFrame,
    tree: BallTree
) -> float | None:
    mask1 = get_mask(cells, signature1)
    mask2 = get_mask(cells, signature2)
    source_count = sum(mask1)
    if source_count == 0:
        return None
    source_cell_locations = cells.loc()[mask1][['pixel x', 'pixel y']]
    within_radius_indices_list = tree.query_radius(
        source_cell_locations,
        radius,
        return_distance=False,
    )
    counts = [
        sum(mask2[index] for index in list(indices))
        for indices in within_radius_indices_list
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


def _phenotype_identifier_lookup(handle, channel_symbols_by_column_name) -> str:
    if re.match(r'^\d+$', handle):
        return f'cell_phenotype {handle}'
    if re.match(r'^F\d+$', handle):
        channel_symbol = channel_symbols_by_column_name[handle]
        return channel_symbol
    raise ValueError(f'Did not understand meaning of specifier: {handle}')


def stage_proximity_feature_values(
    feature_uploader,
    feature_values,
    channel_symbols_by_column_name,
    sample_identifier,
) -> None:
    for _, row in feature_values.iterrows():
        specifiers = (
            _phenotype_identifier_lookup(row['Phenotype 1'], channel_symbols_by_column_name),
            _phenotype_identifier_lookup(row['Phenotype 2'], channel_symbols_by_column_name),
            row['Pixel radius'],
        )
        value = row['Proximity']
        if _validate_value(value):
            feature_uploader.stage_feature_value(specifiers, sample_identifier, value)
