"""Selected metrics from the squidpy library, adapted for use with SPT."""

from typing import cast
from itertools import chain

from spatialprofilingtoolbox import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import (
    phenotype_str_to_phenotype,
    phenotype_to_phenotype_str,
)
from spatialprofilingtoolbox.ondemand.providers import PendingProvider
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.workflow.common.squidpy import (
    describe_squidpy_feature_derivation_method,
    lookup_squidpy_feature_class,
    compute_squidpy_metric_for_one_sample,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class SquidpyProvider(PendingProvider):
    """Calculate selected squidpy metrics."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from binary expression files and JSON-formatted index in the data directory.

        Note: SquidpyProvider always loads centroids because it needs them.
        """
        super().__init__(data_directory, load_centroids=True)

    @classmethod
    def get_or_create_feature_specification(cls,
        study_name: str,
        feature_class: str | None = None,
        phenotypes: list[PhenotypeCriteria] | None = None,
        **kwargs,
    ) -> str:
        """Create and return the identifier of a feature specification defined by the specifiers,
        if it does not exist. If it already exists, return the already-existing specification's
        identifier.
        """
        feature_class = cast(str, feature_class)
        phenotypes = cast(list[PhenotypeCriteria], phenotypes)
        phenotypes_strs: list[str] = [
            phenotype_to_phenotype_str(phenotype) for phenotype in phenotypes
        ]
        specification = cls._get_feature_specification(study_name, feature_class, phenotypes_strs)
        if specification is not None:
            return specification
        logger.debug('Creating feature with specifiers: (%s) %s', study_name, str(phenotypes_strs))
        return cls._create_feature_specification(study_name, feature_class, phenotypes_strs)

    @classmethod
    def _get_feature_specification(cls,
        study_name: str,
        feature_class:str,
        phenotypes_strs: list[str],
    ) -> str | None:
        query = cls._form_query_for_feature_specifiers(len(phenotypes_strs))
        method = cast(str, describe_squidpy_feature_derivation_method(feature_class))
        variable_portion_args = list(chain(*[
            [phenotype, str(i+1)] for i, phenotype in enumerate(phenotypes_strs)
        ]))
        arguments_list = [study_name] + variable_portion_args + [method]
        arguments = tuple(arguments_list)
        with DBCursor() as cursor:
            cursor.execute(query, arguments)
            rows = cursor.fetchall()
        feature_specifications: dict[str, list[str]] = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == len(phenotypes_strs):
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
        study_name: str,
        feature_class: str,
        phenotypes: list[str],
    ) -> str:
        specifiers = tuple(phenotypes)
        method = cast(str, describe_squidpy_feature_derivation_method(feature_class))
        return cls.create_feature_specification(specifiers, study_name, method)

    def have_feature_computed(self, feature_specification: str) -> None:
        study_name, specifiers = SquidpyProvider.retrieve_specifiers(feature_specification)
        phenotypes: list[PhenotypeCriteria] = [phenotype_str_to_phenotype(s) for s in specifiers]
        method = self.retrieve_feature_derivation_method(feature_specification)
        feature_class = cast(str, lookup_squidpy_feature_class(method))
        sample_identifiers = SquidpyProvider.get_sample_identifiers(feature_specification)
        for sample_identifier in sample_identifiers:
            value = compute_squidpy_metric_for_one_sample(
                self.get_cells(sample_identifier, study_name),
                phenotypes,
                feature_class,
            )
            message = 'Computed feature value of %s: %s, %s'
            logger.debug(message, feature_specification, sample_identifier, value)
            with DBCursor() as cursor:
                add_feature_value(feature_specification, sample_identifier, value, cursor)
        SquidpyProvider.drop_pending_computation(feature_specification)
        logger.debug('Wrapped up squidpy metric calculation, feature "%s".', feature_specification)
        logger.debug(
            'The samples considered were: %s',
            [sample_identifiers[0:5], f'(... {len(sample_identifiers)} entries)'],
        )
