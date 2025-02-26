
from abc import ABC
from abc import abstractmethod
from typing import Literal

from numpy import asarray
from numpy import uint64 as np_int64
from numpy.typing import NDArray
from attrs import define

from psycopg.errors import UniqueViolation

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.ondemand.relevant_specimens import relevant_specimens_query
from spatialprofilingtoolbox.ondemand.computers.cell_data_arrays import CellDataArrays
from spatialprofilingtoolbox.db.accessors.cells import CellsAccess
from spatialprofilingtoolbox.db.accessors.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.ondemand.add_feature_value import add_feature_value
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class GenericJobComputer(ABC):
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
            raw, _ = access.get_cells_data(sample, cell_identifiers=cell_identifiers)
            feature_names = access.get_ordered_feature_names()
        number_cells = int.from_bytes(raw[0:4])
        if number_cells == 0:
            return CellDataArrays(None, None, feature_names, None)  # type: ignore
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

    def handle_insert_value(self, value: float | None, allow_null: bool=True) -> None:
        if value is not None:
            self._insert_value(value)
        else:
            self._warn_no_value()
            if allow_null:
                self._insert_null()

    def _warn_no_value(self) -> None:
        specification = str(self.job.feature_specification)
        study = self.job.study
        sample = self.job.sample
        logger.warning(f'Feature {specification} ({sample}, {study}) could not be computed, worker generated None. May insert None.')

    def _insert_value(self, value: float | int) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            try:
                add_feature_value(specification, sample, str(value), cursor)
            except UniqueViolation:
                logger.warning(f'Worker took too long to compute ({value}, case: ({specification}, {sample})).')
        with DBCursor(study=study) as cursor:
            query = 'DELETE FROM quantitative_feature_value_queue WHERE feature=%s and subject=%s;'
            cursor.execute(query, (int(specification), sample))

    def _insert_null(self) -> None:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        with DBCursor(study=study) as cursor:
            try:
                add_feature_value(specification, sample, None, cursor)
            except UniqueViolation:
                logger.warning(f'Worker took too long to compute ({None}, case: ({specification}, {sample})).')

    @staticmethod
    def retrieve_specifiers(study: str, feature_specification: str) -> tuple[str, list[str]]:
        """Get specifiers for this feature specification."""
        with DBCursor(study=study) as cursor:
            cursor.execute('''
                SELECT fs.specifier, fs.ordinality
                FROM feature_specifier fs
                WHERE fs.feature_specification=%s ;
                ''',
                (feature_specification,),
            )
            rows = cursor.fetchall()
            specifiers = [row[0] for row in sorted(rows, key=lambda row: int(row[1]))]
            cursor.execute('''
                SELECT sc2.component_study FROM feature_specification fs
                JOIN study_component sc ON sc.component_study=fs.study
                JOIN study_component sc2 ON sc.primary_study=sc2.primary_study
                WHERE fs.identifier=%s AND
                    sc2.component_study IN ( SELECT name FROM specimen_measurement_study )
                    ;
                ''',
                (feature_specification,),
            )
            study = cursor.fetchall()[0][0]
        return study, specifiers
