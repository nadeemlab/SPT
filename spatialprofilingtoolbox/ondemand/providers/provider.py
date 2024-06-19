"""Base class for on-demand calculation providers."""

from abc import ABC
from abc import abstractmethod
from typing import Literal

from numpy import asarray
from numpy import uint64 as np_int64
from numpy.typing import NDArray
from attrs import define

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.relevant_specimens import relevant_specimens_query
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.db.accessors.cells import CellsAccess
from spatialprofilingtoolbox.db.accessors.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
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
    """Base class for OnDemandProvider instances, since they share some data ingestion methods."""
    job: ComputationJobReference

    def __init__(self, job: ComputationJobReference):
        self.job = job

    @abstractmethod
    def compute(self) -> None:
        raise NotImplementedError

    def get_cell_data_arrays(self) -> CellDataArrays:
        study = self.job.study
        sample = self.job.sample
        cell_identifiers = self._get_cells_selected()
        with DBCursor(study=study) as cursor:
            access = CellsAccess(cursor)
            raw = access.get_cells_data(sample, cell_identifiers=cell_identifiers)
            feature_names = access.get_ordered_feature_names()
        number_cells = int.from_bytes(raw[0:4])
        if number_cells == 0:
            return CellDataArrays(None, None, feature_names, None)
        location = asarray((self._get_parts(4, 8, raw), self._get_parts(8, 12, raw)))
        self._expect_number(location.shape[1], number_cells)
        phenotype = asarray(self._get_parts(12, 20, raw, byteorder='little'))
        self._expect_number(phenotype.shape[0], number_cells)
        identifiers = asarray(self._get_parts(0, 4, raw))
        self._expect_number(identifiers.shape[0], number_cells)
        return CellDataArrays(location, phenotype, feature_names, identifiers)

    def _get_cells_selected(self) -> tuple[int, ...]:
        with DBCursor(study=self.job.study) as cursor:
            query = 'SELECT histological_structure FROM cell_set_cache WHERE feature=%s ;'
            cursor.execute(query, (str(self.job.feature_specification),))
            return tuple(map(lambda row: int(row[0]), cursor.fetchall()))

    @staticmethod
    def _get_parts(
        start: int, end: int, raw: bytes, byteorder: Literal['big', 'little']='big',
    ) -> tuple[np_int64, ...]:
        offset = 20
        period = 20
        return tuple(map(
            lambda batch: np_int64(int.from_bytes(batch[start:end], byteorder=byteorder)),
            CellsAccess._batched(raw[offset:], period),
        ))

    @staticmethod
    def _expect_number(got: int, expected: int) -> None:
        if got != expected:
            raise ValueError(f'Unexpected number of cells, got {got}, expected {expected}.')

    def _get_measurement_study(self, study: str) -> str:
        with DBCursor(study=study) as cursor:
            return StudyAccess(cursor).get_study_components(study).measurement

    @staticmethod
    def relevant_specimens_query() -> str:
        return relevant_specimens_query()

    @staticmethod
    def extract_binary(mask: int, length: int) -> tuple[int, ...]:
        return tuple(reversed(list(map(int, bin(mask)[2:].rjust(length, '0')))))
