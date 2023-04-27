"""
Low-level calculations of proximity metric.
"""
from math import isnan
import re

import numpy as np

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def get_value_and_multiindex(signature):
    value = (1,) * len(signature['positive']) + (0,) * len(signature['negative'])
    if len(value) == 1:
        value = value[0]
    multiindex = [*signature['positive'], *signature['negative']]
    return value, multiindex

def get_mask(cells, signature):
    value, multiindex = get_value_and_multiindex(signature)
    try:
        loc = cells.set_index(multiindex).index.get_loc(value)
    except KeyError:
        return np.asarray([False,] * cells.shape[0])
    if isinstance(loc, np.ndarray):
        return loc
    if isinstance(loc, slice):
        range1 = [False,]*(loc.start - 0)
        range2 = [True,]*(loc.stop - loc.start)
        range3 = [False,]*(cells.shape[0] - loc.stop)
        return np.asarray(range1 + range2 + range3)
    if isinstance(loc, int):
        return np.asarray([i == loc for i in range(cells.shape[0])])
    raise ValueError(f'Could not select by index: {multiindex}. Got: {loc}')

def compute_proximity_metric_for_signature_pair(signature1, signature2, radius, cells, tree):
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
    count = sum(counts) - sum(mask1 & mask2)
    return count / source_count

def validate_value(value):
    if (not isinstance(value, float)) and (not isinstance(value, int)):
        return False
    if isnan(value):
        return False
    return True

def phenotype_identifier_lookup(handle, channel_symbols_by_column_name):
    if re.match(r'^\d+$', handle):
        return f'cell_phenotype {handle}'
    if re.match(r'^F\d+$', handle):
        channel_symbol = channel_symbols_by_column_name[handle]
        return channel_symbol
    raise ValueError(f'Did not understand meaning of specifier: {handle}')

def stage_proximity_feature_values(feature_uploader, feature_values, channel_symbols_by_column_name,
                                   sample_identifier):
    for _, row in feature_values.iterrows():
        specifiers=(phenotype_identifier_lookup(row['Phenotype 1'], channel_symbols_by_column_name),
                    phenotype_identifier_lookup(row['Phenotype 2'], channel_symbols_by_column_name),
                    row['Pixel radius'])
        value = row['Proximity']
        if validate_value(value):
            feature_uploader.stage_feature_value(specifiers, sample_identifier, value)

def describe_proximity_feature_derivation_method():
    return '''
    For a given cell phenotype (first specifier), the average number of cells of a second phenotype (second specifier) within a specified radius (third specifier).
    '''.lstrip().rstrip()
