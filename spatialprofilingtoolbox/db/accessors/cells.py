"""Convenience accessor of all cell data for a given sample."""
from pickle import loads as pickle_loads
from json import loads as json_loads
from typing import Any
from typing import Iterable
from itertools import islice
from itertools import product

from psycopg import Cursor as PsycopgCursor

from spatialprofilingtoolbox.db.exchange_data_formats.cells import CellsData
from spatialprofilingtoolbox.db.exchange_data_formats.cells import BitMaskFeatureNames
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import Channel
from spatialprofilingtoolbox.db.database_connection import SimpleReadOnlyProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CellsAccess(SimpleReadOnlyProvider):
    """Retrieve cell-level data for a sample."""

    def get_cells_data(self, sample: str, cell_identifiers: tuple[int, ...] = ()) -> CellsData:
        return CellsAccess._zip_location_and_phenotype_data(
            self._get_location_data(sample, cell_identifiers),
            self._get_phenotype_data(sample, cell_identifiers),
        )

    def get_ordered_feature_names(self) -> BitMaskFeatureNames:
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
        names = tuple(map(
            lambda i: symbol_from_target[target_from_index[i]],
            indices,
        ))
        return BitMaskFeatureNames(
            names=tuple(Channel(symbol=n) for n in names)
        )

    def _get_location_data(
        self,
        sample: str,
        cell_identifiers: tuple[int, ...],
    ) -> dict[int, tuple[float, float]]:
        locations: dict[int, tuple[float, float]] = pickle_loads(
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
        )[sample]
        if cell_identifiers == ():
            return locations
        return {key: locations[key] for key in set(cell_identifiers).intersection(locations.keys())}

    def _get_phenotype_data(
        self,
        sample: str,
        cell_identifiers: tuple[int, ...],
    ) -> dict[int, bytes]:
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
            message = f'Expected 16 bytes per cell in binary representation of phenotype data, got {byte_count}.'  # pylint: disable=line-too-long
            logger.error(message)
            raise ValueError(message)
        bytes_iterator = index_and_expressions.__iter__()
        masks = dict(
            (int.from_bytes(batch[0:8], byteorder='little'), bytes(batch[8:16]))
            for batch in self._batched(bytes_iterator, 16)
        )
        if cell_identifiers == ():
            return masks
        return {key: masks[key] for key in set(cell_identifiers).intersection(masks.keys())}

    @staticmethod
    def _batched(iterable: Iterable, batch_size: int):
        iterator = iter(iterable)
        while batch := tuple(islice(iterator, batch_size)):
            yield batch

    @classmethod
    def _zip_location_and_phenotype_data(
        cls,
        location_data: dict[int, tuple[float, float]],
        phenotype_data: dict[int, bytes],
    ) -> CellsData:
        identifiers = sorted(list(location_data.keys()))
        _identifiers = sorted(list(phenotype_data.keys()))
        if _identifiers != identifiers:
            message = 'Mismatch of cell sets for location and phenotype data.'
            raise ValueError(message)

        if len(identifiers) == 0:
            header = b''.join(map(
                lambda i: int(i).to_bytes(4),
                (0, 0, 0, 0, 0)
            ))
            return b''.join((header, b''))

        cls._check_consecutive(identifiers)
        extrema = {
            (operation[1], index): operation[0](map(lambda p: p[index-1], location_data.values()))
            for operation, index in product(((min, 'min'), (max, 'max')), (1, 2))
        }
        min_x = extrema[('min', 1)]
        min_y = extrema[('min', 2)]
        if min_x <= 1 or min_y <= 1:
            keys = set(location_data.keys())
            for key in keys:
                location = location_data[key]
                location_data[key] = (location[0] - min_x + 1, location[1] - min_y + 1)
        combined = tuple(
            (i, location_data[i], phenotype_data[i])
            for i in identifiers
        )
        serial = b''.join(map(cls._format_cell_bytes, combined))
        if len(serial) % 20 != 0:
            message = f'Expected exactly 20 bytes per cell to be created. Got total {len(serial)}.'
            logger.error(message)
            raise ValueError(message)
        cell_count = int(len(serial) / 20)
        extrema = {
            (operation[1], index): operation[0](map(lambda p: p[index-1], location_data.values()))
            for operation, index in product(((min, 'min'), (max, 'max')), (1, 2))
        }
        header = b''.join(map(
            lambda i: int(i).to_bytes(4),
            (cell_count,extrema[('min',1)],extrema[('max',1)],extrema[('min',2)],extrema[('max',2)])
        ))
        return b''.join((header, serial))

    @classmethod
    def _check_consecutive(cls, identifiers: list[int]):
        offset = identifiers[0]
        for id1, id2 in zip(identifiers, range(len(identifiers))):
            if id1 != id2 + offset:
                message = f'Identifiers {identifiers[0]}..{identifiers[-1]} not consecutive: {id1} should be {id2 + offset}.'  # pylint: disable=line-too-long
                logger.warning(message)
                break

    @classmethod
    def _format_cell_bytes(cls, args: tuple[int, tuple[float, float], bytes]) -> bytes:
        identifier, location, phenotype = args
        return b''.join((
            identifier.to_bytes(4),
            int(location[0]).to_bytes(4),
            int(location[1]).to_bytes(4),
            phenotype,
        ))

    @staticmethod
    def fetch_one_or_else(
        query: str,
        args: tuple,
        cursor: PsycopgCursor,
        error_message: str,
    ) -> Any:
        cursor.execute(query, args)
        fetched = cursor.fetchone()
        if fetched is None:
            logger.error(error_message)
            raise ValueError(error_message)
        return fetched[0]
