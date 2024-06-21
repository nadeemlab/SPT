"""Low-level calculations of proximity metric."""

from math import isnan

from sklearn.neighbors import BallTree  # type: ignore

from numpy import uint64 as np_int64
from numpy.typing import NDArray

from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.accessors.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def compute_proximity_metric_for_signature_pair(
    phenotype1: PhenotypeCriteria,
    phenotype2: PhenotypeCriteria,
    radius: float,
    phenotype_masks: NDArray[np_int64],
    locations: NDArray[np_int64],
    feature_names: BitMaskFeatureNames,
) -> float | None:
    def signature(markers: tuple[str, ...]):
        features = tuple(n.symbol for n in feature_names.names)
        return CountsProvider._compute_signature(markers, features)

    marker_set1 = (phenotype1.positive_markers, phenotype1.negative_markers)
    signatures1 = tuple(map(signature, marker_set1))

    marker_set2 = (phenotype2.positive_markers, phenotype2.negative_markers)
    signatures2 = tuple(map(signature, marker_set2))

    def membership1(_entry: np_int64) -> bool:
        entry = int(_entry)
        return (entry | signatures1[0] == entry) and (~entry | signatures1[1] == ~entry)

    def membership2(_entry: np_int64) -> bool:
        entry = int(_entry)
        return (entry | signatures2[0] == entry) and (~entry | signatures2[1] == ~entry)

    augmented_mask1 = tuple(map(
        lambda pair: (membership1(pair[0]), pair[1]),
        zip(phenotype_masks, locations.transpose()),
    ))
    mask1 = tuple(map(lambda pair: pair[0], augmented_mask1))
    locations1 = tuple(map(lambda pair: pair[1], filter(lambda pair: pair[0], augmented_mask1)))
    mask2 = tuple(map(membership2, phenotype_masks))
    mask12_size = len(tuple(filter(lambda pair: pair[0] and pair[1], zip(mask1, mask2))))
    source_count = len(locations1)
    if source_count == 0:
        logger.debug(f'No elements matching mask: {marker_set1} {signatures1} {tuple(bin(s) for s in signatures1)}')
        return None
    tree = BallTree(locations.transpose())
    within_radius_indices_list = tree.query_radius(locations1, radius, return_distance=False)
    counts = (
        sum(mask2[integer_index] for integer_index in list(integer_indices))
        for integer_indices in within_radius_indices_list
    )
    count = sum(counts) - mask12_size
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
