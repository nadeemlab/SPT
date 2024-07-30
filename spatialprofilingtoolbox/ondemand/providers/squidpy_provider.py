"""Selected metrics from the squidpy library, adapted for use with SPT."""

from typing import cast
from itertools import chain

from pandas import DataFrame

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import (
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.providers.pending_provider import PendingProvider
from spatialprofilingtoolbox.ondemand.providers.provider import CellDataArrays
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.workflow.common.squidpy import (
    lookup_squidpy_feature_class,
    compute_squidpy_metric_for_one_sample,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SquidpyProvider(PendingProvider):
    """Calculate selected squidpy metrics."""

    def compute(self) -> None:
        args, arrays = self._prepare_parameters()
        if arrays.identifiers is None:
            self.handle_insert_value(None, allow_null=True)
        else:
            value = self._perform_computation(args, arrays)
            self.handle_insert_value(value, allow_null=True)

    def _prepare_parameters(
        self,
    ) -> tuple[tuple[str, tuple[PhenotypeCriteria, ...], float | None], CellDataArrays]:
        study = self.job.study
        feature_specification = str(self.job.feature_specification)
        method = self.retrieve_feature_derivation_method(study, feature_specification)
        feature_class = cast(str, lookup_squidpy_feature_class(method))
        _, specifiers = SquidpyProvider.retrieve_specifiers(study, feature_specification)
        phenotypes: tuple[PhenotypeCriteria, ...]
        if feature_class == 'co-occurrence':
            phenotypes = tuple(map(phenotype_str_to_phenotype, specifiers[0:2]))
            radius = float(specifiers[2])
        else:
            phenotypes = tuple(map(phenotype_str_to_phenotype, specifiers))
            radius = None
        arrays = self.get_cell_data_arrays()
        return ((feature_class, phenotypes, radius), arrays)

    def _perform_computation(
        self,
        args: tuple[str, tuple[PhenotypeCriteria, ...], float | None],
        arrays: CellDataArrays,
    ) -> float | None:
        feature_class, phenotypes, radius = args
        df = self._form_cells_dataframe(arrays)
        return compute_squidpy_metric_for_one_sample(df, phenotypes, feature_class, radius=radius)

    @staticmethod
    def _form_cells_dataframe(arrays: CellDataArrays) -> DataFrame:
        features = tuple(f.symbol for f in arrays.feature_names.names)
        rows = []
        zipped = zip(arrays.identifiers, arrays.phenotype, arrays.location.transpose())
        for identifier, phenotype, location in zipped:
            location_list = [location[0], location[1]]
            vector = list(OnDemandProvider.extract_binary(phenotype, len(features)))
            row = tuple(vector + [identifier] + location_list)
            rows.append(row)
        columns = list(features) + ['histological_structure_id'] + ['pixel x', 'pixel y']
        df = DataFrame(rows, columns=columns)
        df.set_index('histological_structure_id', inplace=True)
        return df

    @classmethod
    def get_or_create_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        feature_class: str | None = None,
        phenotypes: list[PhenotypeCriteria] | None = None,
        radius: float | None = None,
        **kwargs,
    ) -> tuple[str, bool]:
        """Create and return the identifier of a feature specification defined by the specifiers,
        if it does not exist. If it already exists, return the already-existing specification's
        identifier.
        """
        feature_class = cast(str, feature_class)
        phenotypes = cast(list[PhenotypeCriteria], phenotypes)
        phenotypes_strs: list[str] = [
            phenotype_to_phenotype_str(phenotype) for phenotype in phenotypes
        ]
        specification = cls._get_feature_specification(
            study,
            data_analysis_study,
            feature_class,
            phenotypes_strs,
            radius=radius,
        )
        if specification is not None:
            return (specification, False)
        if radius is not None:
            message = 'Creating feature with specifiers: (%s) %s, %s'
            logger.debug(message, data_analysis_study, str(phenotypes_strs), radius)
        else:
            message = 'Creating feature with specifiers: (%s) %s'
            logger.debug(message, data_analysis_study, str(phenotypes_strs))
        return (cls._create_feature_specification(
            study,
            data_analysis_study,
            feature_class,
            phenotypes_strs,
            radius=radius,
        ), True)

    @classmethod
    def _get_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        feature_class:str,
        phenotypes_strs: list[str],
        radius: float | None = None,
    ) -> str | None:
        specifiers = phenotypes_strs
        if feature_class == 'co-occurrence':
            specifiers = specifiers + [str(radius)]
        query = cls._form_query_for_feature_specifiers(len(specifiers))
        method = cast(str, get_feature_description(feature_class))
        variable_portion_args = list(chain(*[
            [specifier, str(i+1)] for i, specifier in enumerate(specifiers)
        ]))
        with DBCursor(study=study) as cursor:
            cursor.execute(query, tuple([data_analysis_study] + variable_portion_args + [method]))
            rows = cursor.fetchall()
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, _specifiers in feature_specifications.items():
            if len(_specifiers) == len(specifiers):
                return key
        return None

    @classmethod
    def _form_query_for_feature_specifiers(cls, number_specifiers: int) -> str:
        query_header = '''
        SELECT
            fsn.identifier,
            fs.specifier
        FROM feature_specification fsn
            JOIN feature_specifier fs
                ON fs.feature_specification=fsn.identifier
            JOIN study_component sc
                ON sc.component_study=fsn.study
            JOIN study_component sc2
                ON sc2.primary_study=sc.primary_study
        WHERE sc2.component_study=%s AND
            ( '''
        variable_portion_template = ' (fs.specifier=%s AND fs.ordinality=%s) '
        variable_portion = ' OR '.join([
            variable_portion_template
            for i in range(number_specifiers)
        ])
        query_footer = ''') AND
            fsn.derivation_method=%s
        ;
        '''
        return query_header + variable_portion + query_footer

    @classmethod
    def _create_feature_specification(cls,
        study: str,
        data_analysis_study: str,
        feature_class: str,
        phenotypes: list[str],
        radius: float | None = None,
    ) -> str:
        if feature_class == 'co-occurrence':
            specifiers = tuple(phenotypes[0:2] + [str(radius)])
        else:
            specifiers = tuple(phenotypes)
        method = cast(str, get_feature_description(feature_class))
        return cls.create_feature_specification(study, specifiers, data_analysis_study, method)
