from math import floor

import brotli  # type: ignore
from attrs import define
from cattrs.preconf.json import make_converter

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.ondemand.compressed_matrix_writer import CompressedMatrixWriter
from spatialprofilingtoolbox.ondemand.defaults import FEATURE_MATRIX_WITH_INTENSITIES_SUBSAMPLE_WHOLE_STUDY
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

@define
class SubsampleMetadata:
    sample_names_alphabetical: tuple[str, ...]
    subsample_sizes_same_order: tuple[int, ...]
    channel_names: tuple[str, ...]

DEFAULT_MAX = 1000000

class Subsampler:
    study: str
    database_config_file: str | None
    maximum_number_cells: int
    verbose: bool

    def __init__(self, study: str, database_config_file: str | None, maximum_number_cells: int = DEFAULT_MAX, verbose: bool=False):
        self.study = study
        self.database_config_file = database_config_file
        self.maximum_number_cells = maximum_number_cells
        self.verbose = verbose
        self._compute_and_store()

    def _compute_and_store(self) -> None:
        blob = bytearray()

        metadata = self._form_subsample_metadata()
        blob.extend(make_converter().dumps(metadata).encode('utf-8'))

        file_separator = int.to_bytes(28)
        blob.extend(file_separator)

        for sample_name, subsample_size in zip(
            metadata.sample_names_alphabetical,
            metadata.subsample_sizes_same_order,
        ):
            blob.extend(self._get_subsample(sample_name, subsample_size, metadata.channel_names))

        compressed_blob = brotli.compress(blob, quality=11, lgwin=24)
        # CompressedMatrixWriter(None)._insert_blob(
        #     self.study, compressed_blob, '', FEATURE_MATRIX_WITH_INTENSITIES_SUBSAMPLE_WHOLE_STUDY,
        # )

    def _form_subsample_metadata(self) -> SubsampleMetadata:
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            s = StudyAccess(cursor).get_number_cells_by_sample(self.study, verbose=self.verbose)
        sample_names_alphabetical, sample_sizes = tuple(zip(*sorted(list(s), key=lambda pair: pair[0])))
        subsample_sizes_same_order = self._adjust_sample_sizes(sample_sizes)
        channel_names = self._get_channel_names()
        return SubsampleMetadata(sample_names_alphabetical, subsample_sizes_same_order, channel_names)

    def _adjust_sample_sizes(self, sample_sizes: tuple[int, ...]) -> tuple[int, ...]:
        total = sum(list(sample_sizes))
        if total <= self.maximum_number_cells:
            return sample_sizes
        deflator = float(self.maximum_number_cells / total)
        approximates = list(map(lambda s: floor(s*deflator), sample_sizes))
        index = 0
        while sum(approximates) < self.maximum_number_cells:
            value = approximates[index]
            original = sample_sizes[index]
            if value < original:
                approximates[index] = value + 1
        if not sum(approximates) == self.maximum_number_cells:
            logger.error('Something was wrong with subsampling logic, too many cells selected.')
        return tuple(approximates)

    def _get_channel_names(self) -> tuple[str, ...]:
        return ()

    def _get_subsample(self, sample: str, size: int, channel_names: tuple[str, ...]) -> bytes:

        #     blob.extend(int(histological_structure_id).to_bytes(4))
        #     for value in data_array[histological_structure_id]:
        #         encoded = encode_float8_with_clipping(value)
        #         blob.extend(encoded)

        return bytes()
