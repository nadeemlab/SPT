"""Convenience functions for working with cell DataFrames."""

from numpy import asarray, ndarray
from numpy.typing import NDArray
from pandas import DataFrame

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria

def _get_value_and_multiindex(signature: PhenotypeCriteria) -> tuple[int | tuple[int, ...], list[str]]:
    value = (1,) * len(signature.positive_markers) + (0,) * len(signature.negative_markers)
    if len(value) == 1:
        value = value[0]
    multiindex = [*signature.positive_markers, *signature.negative_markers]
    return value, multiindex


def get_mask(cells: DataFrame, signature: PhenotypeCriteria) -> NDArray[bool,]:
    """Transform phenotype signature into a boolean mask for a DataFrame."""
    value, multiindex = _get_value_and_multiindex(signature)
    try:
        loc = cells.set_index(multiindex).index.get_loc(value)
    except KeyError:
        return asarray([False,] * cells.shape[0])
    if isinstance(loc, ndarray):
        return loc
    if isinstance(loc, slice):
        range1 = [False,]*(loc.start - 0)
        range2 = [True,]*(loc.stop - loc.start)
        range3 = [False,]*(cells.shape[0] - loc.stop)
        return asarray(range1 + range2 + range3)
    if isinstance(loc, int):
        return asarray([i == loc for i in range(cells.shape[0])])
    raise ValueError(f'Could not select by index: {multiindex}. Got: {loc}')
