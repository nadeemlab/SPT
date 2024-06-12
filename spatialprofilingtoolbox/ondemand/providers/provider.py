"""Base class for on-demand calculation providers."""

from typing import cast
from typing import Type
from abc import ABC

from numpy import asarray
from numpy import uint64 as np_int64
from numpy.typing import NDArray
from attrs import define

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.cells import CellsAccess
from spatialprofilingtoolbox.db.accessors.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)

@define
class CellDataArrays:
    """Represents the location and phenotypes for the cells in one sample."""
    location: NDArray[np_int64]
    phenotype: NDArray[np_int64]
    feature_names: BitMaskFeatureNames
    identifiers: NDArray[np_int64]


class OnDemandProvider(ABC):
    """Base class for OnDemandProvider instances, since they share data ingestion methods."""
    database_config_file: str
    timeout: int

    @classmethod
    def service_specifier(cls) -> str:
        raise NotImplementedError

    def __init__(self, timeout: int, database_config_file: str | None) -> None:
        self.database_config_file = cast(str, database_config_file)
        self.timeout = timeout

    def get_cell_data_arrays(self, study: str, sample: str) -> CellDataArrays:
        with DBCursor(database_config_file=self.database_config_file, study=study) as cursor:
            access = CellsAccess(cursor)
            raw = access.get_cells_data(sample)
            feature_names = access.get_ordered_feature_names()
        number_cells = int.from_bytes(raw[0:4])
        location = asarray((self._get_parts(4, 8, raw), self._get_parts(8, 12, raw)))
        self._expect_number(location.shape[1], number_cells)
        phenotype = asarray(self._get_parts(12, 20, raw))
        self._expect_number(phenotype.shape[0], number_cells)
        identifiers = asarray(self._get_parts(0, 4, raw))
        self._expect_number(identifiers.shape[0], number_cells)
        return CellDataArrays(location, phenotype, feature_names, identifiers)

    @staticmethod
    def _get_parts(start: int, end: int, raw: bytes) -> tuple:
        offset = 20
        period = 20
        return tuple(map(
            lambda batch: np_int64(int.from_bytes(batch[start:end])),
            CellsAccess._batched(raw[offset:], period),
        ))

    @staticmethod
    def _expect_number(got: int, expected: int) -> None:
        if got != expected:
            raise ValueError(f'Unexpected number of cells, got {got}, expected {expected}.')
