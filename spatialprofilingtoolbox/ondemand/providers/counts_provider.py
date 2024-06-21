"""Count cells for a specific signature, over the specially-created binary-format index."""

from typing import cast

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.providers.provider import CellDataArrays
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.ondemand.phenotype_str import (\
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
ItemList = tuple[str, list[int]]
Item = tuple[str, tuple[int, ...]]

logger = colorized_logger(__name__)


class CountsProvider(PendingProvider):
    """Scan binary-format expression matrices for specific signatures."""

    def compute(self) -> None:
        args, arrays = self._prepare_parameters()
        if arrays.identifiers is None:
            self.handle_insert_value(None, allow_null=True)
        else:
            count = self._perform_count(args, arrays)
            self.handle_insert_value(count)

    def _prepare_parameters(self) -> tuple[tuple[int, int, tuple[int, ...]], CellDataArrays]:
        study = self.job.study
        specification = str(self.job.feature_specification)
        _, specifiers = self.retrieve_specifiers(study, specification)
        phenotype = phenotype_str_to_phenotype(specifiers[0])
        cells_selected = self._retrieve_cells_selected(study, specification)  # to deprecate
        marker_set = (phenotype.positive_markers, phenotype.negative_markers)
        arrays = self.get_cell_data_arrays()
        features = tuple(n.symbol for n in arrays.feature_names.names)
        signatures = tuple(map(lambda m: cast(int, self._compute_signature(m, features)), marker_set))
        return ((signatures[0], signatures[1], cells_selected), arrays)

    @staticmethod
    def _retrieve_cells_selected(study: str, specification: str) -> tuple[int, ...]:
        with DBCursor(study=study) as cursor:
            query = 'SELECT histological_structure FROM cell_set_cache WHERE feature=%s ;'
            cursor.execute(query, (specification,))
            rows = tuple(cursor.fetchall())
        if len(rows) == 0:
            return ()
        return tuple(map(lambda row: int(row[0]), rows))

    @staticmethod
    def _perform_count(args: tuple[int, int, tuple[int, ...]], arrays: CellDataArrays) -> int:
        if arrays.identifiers.shape[0] == 0:
            return 0
        return CountsProvider._count_structures_of_partial_signed_signature(*args, arrays)

    @staticmethod
    def _count_structures_of_partial_signed_signature(
        positives_signature: int,
        negatives_signature: int,
        cells_selected: tuple[int, ...],
        arrays: CellDataArrays,
    ) -> int:
        """Count the number of cells in the given sample that match this signature."""
        if positives_signature == 0 and negatives_signature == 0:
            return arrays.identifiers.shape[0]
        count = CountsProvider._get_count(tuple(arrays.phenotype), positives_signature, negatives_signature)
        return count

    @staticmethod
    def _get_count(integers: tuple[int, ...], positives_mask: int, negatives_mask: int) -> int:
        """
        Counts the number of elements of the list of integer-represented binary numbers which equal
        to 1 along the bits indicated by the positives mask, and equal to 0 along the bits indicated
        by the negatives mask.
        """
        count = 0
        for _entry in integers:
            entry = int(_entry)
            if (entry | positives_mask == entry) and (~entry | negatives_mask == ~entry):
                count = count + 1
        return count

    @staticmethod
    def _compute_signature(
        channel_names: tuple[str, ...],
        all_features: tuple[str, ...],
    ) -> int:
        """Compute int signature of this channel name combination."""
        missing = set(channel_names).difference(all_features)
        if len(missing) > 0:
            message = f'Cannot compute signature when these columns are requested: {missing}'
            raise ValueError(message)
        signature = 0
        indices = map(lambda name: all_features.index(name), channel_names)
        for index in indices:
            signature = signature + (1 << index)
        return signature

    @classmethod
    def get_or_create_feature_specification(
        cls,
        study: str,
        data_analysis_study: str,
        phenotype: PhenotypeCriteria | None = None,
        cells_selected: tuple[int, ...] = (),
        **kwargs,
    ) -> tuple[str, bool]:
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
            _cells_selected = cls._retrieve_cells_selected(study, specification)
            if set(cells_selected) == set(_cells_selected):
                return (specification, False)
        short = str(cells_selected[0:min(len(cells_selected), 5)]) + ' ...'
        addend = f' (and cell set {short}, {len(cells_selected)} cells)' if cells_selected != () else ''
        message = 'Creating feature with specifiers: %s' + addend
        logger.debug(message, phenotype)
        specifiers_arguments_str = (
            data_analysis_study,
            phenotype_to_phenotype_str(phenotype),
        )
        specification = cls._create_feature_specification(study, *specifiers_arguments_str)
        cls._append_cell_set(study, specification, cells_selected)
        return (specification, True)

    @classmethod
    def _append_cell_set(
        cls, study: str, specification: str, cells_selected: tuple[int, ...],
    ) -> None:
        with DBCursor(study=study) as cursor:
            copy_command = 'COPY cell_set_cache (feature, histological_structure) FROM STDIN'
            with cursor.copy(copy_command) as copy:
                for cell in cells_selected:
                    copy.write_row((specification, str(cell)))

    @classmethod
    def _check_cell_set(
        cls, study: str, feature: str, _cells_selected: tuple[int, ...],
    ) -> bool:
        with DBCursor(study=study) as cursor:
            query = '''
            SELECT histological_structure
            FROM cell_set_cache
            WHERE feature=%s ;
            '''
            cursor.execute(query, (feature,))
            rows = tuple(cursor.fetchall())
        cells = tuple(sorted(list(map(lambda row: int(row[0]), rows))))
        cells_selected = tuple(sorted(list(_cells_selected)))
        if len(cells) == 0 or len(cells_selected) == 0:
            return len(cells) == len(cells_selected)
        condition = cells == cells_selected
        return condition

    @classmethod
    def _get_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype: PhenotypeCriteria,
        cells_selected: tuple[int, ...],
    ) -> str | None:
        cells = f'{cells_selected[0:min(5, len(cells_selected))]} ... ({len(cells_selected)})'
        feature_description = get_feature_description('population fractions')
        args = (
            data_analysis_study,
            phenotype_to_phenotype_str(phenotype),
            feature_description,
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
                  ( fs.specifier=%s AND fs.ordinality='1') AND
                  fsn.derivation_method=%s
            ;
            ''', args)
            rows = tuple(cursor.fetchall())
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        matches_list: list[str] = []
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == 1:
                matches_list.append(key)
        matches = tuple(filter(
            lambda feature: cls._check_cell_set(study, feature, cells_selected),
            matches_list,
        ))
        if len(matches) == 0:
            return None
        if len(matches) > 1:
            text = 'Multiple features match the selected specification'
            message = f'{text}: {matches} {phenotype} {cells}'
            logger.warning(message)
        return matches[0]

    @classmethod
    def _create_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        phenotype: str,
    ) -> str:
        specifiers = (phenotype,)
        method = get_feature_description('population fractions')
        return cls.create_feature_specification(study, specifiers, data_analysis_study, method)
