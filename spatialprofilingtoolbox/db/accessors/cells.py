"""Convenience accessor of all cell data for a given sample."""
from pickle import loads as pickle_loads
from json import loads as json_loads
from typing import Any
from typing import Iterable
from typing import Hashable
from typing import Callable
from typing import cast
from itertools import islice

from psycopg2 import cursor as Psycopg2Cursor
from pandas import DataFrame
from pandas import Series
from pandas import concat

from spatialprofilingtoolbox.db.exchange_data_formats.cells import CellsData
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellsAccess(SimpleReadOnlyProvider):
    def get_cell_data(self, study: str, sample: str) -> CellsData:
        return CellsAccess._zip_location_and_phenotype_data(
            self._get_location_data(sample),
            self._get_phenotype_data(sample),
        )

    def get_ordered_feature_names(self) -> tuple[str, ...]:
        expressions_index = json_loads(bytearray(self.fetch_one_or_else(
            '''
            SELECT blob_contents
            FROM ondemand_studies_index osi
            WHERE blob_type='expressions_index' ;
            ''',
            (),
            self.cursor,
            'No feature metadata for the given study.',
        )).decode('utf-8'))[''][0]
        lookup1: dict[str, int] = expressions_index['target index lookup']
        lookup2: dict[str, str] = expressions_index['target by symbol']
        target_from_index = {value: key for key, value in lookup1.items()}
        symbol_from_target = {value: key for key, value in lookup2.items()}
        indices = sorted(list(target_from_index.keys()))
        return tuple(map(
            lambda i: symbol_from_target[target_from_index[i]],
            indices,
        ))

    def _get_location_data(self, sample: str) -> DataFrame:
        by_sample = pickle_loads(
            self.fetch_one_or_else(
                '''
                SELECT blob_contents
                FROM ondemand_studies_index
                WHERE specimen=%s AND blob_type='centroids' ;
                ''',
                (sample,),
                self.cursor,
                f'Requested centroids data for "{sample}" not found in database.'
            )
        )
        return DataFrame.from_dict(by_sample[sample], orient='index', columns=['x', 'y'])

    def _get_phenotype_data(self, sample: str) -> DataFrame:
        index_and_expressions = bytearray(self.fetch_one_or_else(
            '''
            SELECT blob_contents
            FROM ondemand_studies_index
            WHERE specimen=%s AND blob_type='feature_matrix' ;
            ''',
            (sample,),
            self.cursor,
            f'Requested phenotype data for "{sample}" not found in database.',
        ))
        byte_count = len(index_and_expressions)
        if byte_count % 16 != 0:
            message = f'Expected 16 bytes per cell in binary representation of phenotype data, got {byte_count}.'
            raise ValueError(message)
        bytes_iterator = index_and_expressions.__iter__()
        integers_from_hsi = dict(
            (int.from_bytes(batch[0:8], 'little'), batch[8:16])
            for batch in self._batched(bytes_iterator, 16)
        )
        return DataFrame.from_dict(integers_from_hsi, orient='index', columns=['integer_representation'])

    @staticmethod
    def _batched(iterable: Iterable, batch_size: int):
        iterator = iter(iterable)
        while batch := tuple(islice(iterator, batch_size)):
            yield batch

    @classmethod
    def _zip_location_and_phenotype_data(
        cls,
        location_data: DataFrame,
        phenotype_data: DataFrame,
    ) -> CellsData:
        df = concat((location_data, phenotype_data))
        format = cast(Callable[[tuple[Hashable | None, Series]], bytes], cls._format_cell_bytes)
        serial = b''.join(map(format, df.iterrows()))
        if len(serial) % 20 != 0:
            message = f'Expected exactly 20 bytes per cell to be created. Got total {len(serial)}.'
            logger.error(message)
            raise ValueError(message)
        cell_count = len(serial) / 20
        header = cell_count.to_bytes(8, 'little')
        return b''.join((header, serial))

    @classmethod
    def _format_cell_bytes(cls, index_row: tuple[int, tuple[float, float, int]]) -> bytes:
        index, row = index_row
        return b''.join((
            index.to_bytes(4, 'little'),
            int(row[0]).to_bytes(4, 'little'),
            int(row[1]).to_bytes(4, 'little'),
            row[2].to_bytes(8, 'little'),
        ))

    @staticmethod
    def fetch_one_or_else(
        query: str,
        args: tuple,
        cursor: Psycopg2Cursor,
        error_message: str,
    ) -> Any:
        cursor.execute(query, args)
        fetched = cursor.fetchone()
        if fetched is None:
            logger.error(error_message)
            raise ValueError(error_message)
        return fetched[0]
