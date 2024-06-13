"""Count cells for a specific signature, over the specially-created binary-format index."""

from typing import cast
from ast import literal_eval

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.providers.provider import CellDataArrays
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.ondemand.job_reference import ComputationJobReference
from spatialprofilingtoolbox.ondemand.phenotype_str import (\
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CountsProvider(PendingProvider):
    """Scan binary-format expression matrices for specific signatures."""

    def __init__(self, job: ComputationJobReference):
        super().__init__(job)

    def compute(self) -> None:
        args, arrays = self._prepare_parameters()
        count = self._perform_count(args, arrays)
        self.insert_value(count)

    def _prepare_parameters(self) -> tuple[tuple[int, int, tuple[int, ...]], CellDataArrays]:
        study = self.job.study
        specification = str(self.job.feature_specification)
        sample = self.job.sample
        _, specifiers = self.retrieve_specifiers(study, specification)
        phenotype = phenotype_str_to_phenotype(specifiers[0])
        cells_selected = self._selections_from_str(specifiers[1])
        marker_set = (phenotype.positive_markers, phenotype.negative_markers)
        arrays = self.get_cell_data_arrays()
        features = tuple(n.symbol for n in arrays.feature_names.names)
        signatures = tuple(map(lambda m: cast(int, self._compute_signature(m, features)), marker_set))
        return ((signatures[0], signatures[1], cells_selected), arrays)

    @staticmethod
    def _perform_count(args: tuple[int, int, tuple[int, ...]], arrays: CellDataArrays) -> int:
        return CountsProvider._count_structures_of_partial_signed_signature(*args, arrays)

    @staticmethod
    def _count_structures_of_partial_signed_signature(
        positives_signature: int,
        negatives_signature: int,
        cells_selected: tuple[int, ...],
        arrays: CellDataArrays,
    ) -> int:
        """Count the number of cells in the given sample that match this signature."""
        if cells_selected != ():
            candidates = tuple(map(
                lambda pair: pair[1],
                filter(
                    lambda pair: pair[0] in cells_selected,
                    zip(arrays.identifiers, arrays.phenotype,
                ))
            ))
        else:
            candidates = tuple(arrays.phenotype)
        count = CountsProvider._get_count(candidates, positives_signature, negatives_signature)
        return count

    @staticmethod
    def _get_count(integers: tuple[int, ...], positives_mask: int, negatives_mask: int) -> int:
        """
        Counts the number of elements of the list of integer-represented binary numbers which equal
        to 1 along the bits indicated by the positives mask, and equal to 0 along the bits indicated
        by the negatives mask.
        """
        count = 0
        for entry in integers:
            if (entry | positives_mask == entry) and (~entry | negatives_mask == ~entry):
                count = count + 1
        return count

    @staticmethod
    def _compute_signature(
        channel_names: tuple[str, ...],
        all_features: tuple[str, ...],
    ) -> int | None:
        """Compute int signature of this channel name combination."""
        if len(set(channel_names).difference(all_features)) > 0:
            return None
        signature = 0
        indices = map(lambda name: all_features.index(name), channel_names)
        for index in indices:
            signature = signature + (1 << index)
        return signature

    @classmethod
    def _selections_str(cls, cells_selected: tuple[int, ...]) -> str:
        return str(cells_selected)

    @classmethod
    def _selections_from_str(cls, cells_selected_str: str) -> tuple[int, ...]:
        return literal_eval(cells_selected_str)

    @classmethod
    def get_or_create_feature_specification(
        cls,
        study: str,
        data_analysis_study: str,
        phenotype: PhenotypeCriteria | None = None,
        cells_selected: tuple[int, ...] = (),
        **kwargs,
    ) -> str:
        if phenotype is None:
            phenotype = PhenotypeCriteria(positive_markers=(), negative_markers=())
        else:
            phenotype = cast(PhenotypeCriteria, phenotype)
        specifiers_arguments = (
            data_analysis_study,
            phenotype,
            cells_selected,
        )
        specification = cls._get_feature_specification(study, *specifiers_arguments)
        if specification is not None:
            return specification
        message = 'Creating feature with specifiers: (%s) %s, %s'
        logger.debug(message, *specifiers_arguments)
        specifiers_arguments_str = (
            data_analysis_study,
            phenotype_to_phenotype_str(phenotype),
            cls._selections_str(cells_selected),
        )
        return cls._create_feature_specification(study, *specifiers_arguments_str)

    @classmethod
    def _get_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype: PhenotypeCriteria,
        cells_selected: tuple[int, ...],
    ) -> str | None:
        args = (
            data_analysis_study,
            phenotype_to_phenotype_str(phenotype),
            cls._selections_str(cells_selected),
            get_feature_description('population fractions'),
        )
        with DBCursor(study=study) as cursor:
            cursor.execute('''
            SELECT
                fsn.identifier,
                fs.specifier
            FROM feature_specification fsn
            JOIN feature_specifier fs ON fs.feature_specification=fsn.identifier
            JOIN study_component sc ON sc.component_study=fsn.study
            JOIN study_component sc2 ON sc2.primary_study=sc.primary_study
            WHERE sc2.component_study=%s AND
                  ( fs.specifier=%s AND fs.ordinality='1'
                    fs.specifier=%s AND fs.ordinality='2' ) AND
                  fsn.derivation_method=%s
            ;
            ''', args)
            rows = cursor.fetchall()
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == 2:
                return key
        return None

    @classmethod
    def _create_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype: str,
        cells_selected: str,
    ) -> str:
        specifiers = (phenotype, cells_selected)
        method = get_feature_description('population fractions')
        return cls.create_feature_specification(study, specifiers, data_analysis_study, method)
