from math import floor
import random

import brotli  # type: ignore
from attrs import define
from cattrs.preconf.json import make_converter

from spatialprofilingtoolbox.db.accessors.feature_names import get_ordered_feature_names
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.db.accessors.study import CellsAccess
from spatialprofilingtoolbox.ondemand.compressed_matrix_writer import CompressedMatrixWriter
from spatialprofilingtoolbox.ondemand.defaults import FEATURE_MATRIX_WITH_INTENSITIES_SUBSAMPLE_WHOLE_STUDY
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
logger = colorized_logger(__name__)

@define
class SubsampleCount:
    specimen: str
    count: int

@define
class ChannelThreshold:
    name: str
    threshold: float

@define
class SubsampleMetadata:
    subsample_counts: tuple[SubsampleCount, ...]
    channel_order_and_thresholds: tuple[ChannelThreshold, ...]

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

        metadata, original_sample_sizes = self._form_subsample_metadata()
        blob.extend(make_converter().dumps(metadata).encode('utf-8'))

        file_separator = int.to_bytes(28)
        blob.extend(file_separator)

        for subsample_count, original in zip(
            metadata.subsample_counts,
            original_sample_sizes,
        ):
            sample_name, subsample_size = subsample_count.specimen, subsample_count.count
            blob.extend(self._get_subsample(sample_name, subsample_size, original, len(metadata.channel_order_and_thresholds)))

        if self.verbose:
            logger.info('Compressing blob.')
        compressed_blob = brotli.compress(blob, quality=11, lgwin=24)

        if self.verbose:
            logger.info('Writing blob to database.')
        blob_type = FEATURE_MATRIX_WITH_INTENSITIES_SUBSAMPLE_WHOLE_STUDY
        CompressedMatrixWriter(self.database_config_file)._insert_blob(
            self.study, compressed_blob, '', blob_type, drop_first=True,
        )

    def _form_subsample_metadata(self) -> tuple[SubsampleMetadata, tuple[int, ...]]:
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            s = StudyAccess(cursor).get_number_cells_by_sample(self.study, verbose=self.verbose)
        sample_names_alphabetical, sample_sizes = tuple(zip(*sorted(list(s), key=lambda pair: pair[0])))
        subsample_sizes_same_order = self._adjust_sample_sizes(sample_sizes)
        channel_names = self._get_channel_names()
        subsample_counts = tuple(map(
            lambda pair: SubsampleCount(*pair),
            zip(sample_names_alphabetical, subsample_sizes_same_order),
        ))
        channel_order_and_thresholds = tuple(map(
            lambda name: ChannelThreshold(name, 0.5),
            channel_names,
        ))
        return SubsampleMetadata(subsample_counts, channel_order_and_thresholds), sample_sizes

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
            index = (index + 1) % len(approximates)
        if not sum(approximates) == self.maximum_number_cells:
            logger.error('Something was wrong with subsampling logic, too many cells selected.')
        return tuple(approximates)

    def _get_channel_names(self) -> tuple[str, ...]:
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            n = get_ordered_feature_names(cursor)
        return tuple(map(lambda channel: channel.symbol, n.names))

    def _get_subsample(self, sample: str, size: int, original: int, number_channels: int) -> bytes:
        if self.verbose:
            logger.info(f'Subsampling: {sample} ({size}/{original} cells)')
        with DBCursor(study=self.study, database_config_file=self.database_config_file) as cursor:
            access = CellsAccess(cursor)
            compressed = access.get_cells_data_intensity(sample, accept_encoding=('br',))
        raw = brotli.decompress(compressed)
        random.seed(10001)
        indices = random.sample(list(range(original)), size)
        blob = bytearray()
        N = number_channels
        for i in indices:
            position = (N + 4)*i
            blob.extend(raw[position: position + N])
        return blob
