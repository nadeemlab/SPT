"""Selected metrics from the squidpy library, adapted for use with SPT."""

from spatialprofilingtoolbox import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.phenotype_str import \
    phenotype_str_to_phenotype, phenotype_to_phenotype_str
from spatialprofilingtoolbox.ondemand.providers import PendingProvider
from spatialprofilingtoolbox.workflow.common.export_features import add_feature_value
from spatialprofilingtoolbox.workflow.common.squidpy import \
    describe_squidpy_feature_derivation_method, compute_squidpy_metrics_for_one_sample
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
    def _get_or_create_feature_specification(cls, study_name, specifiers) -> str:
        pass

    @classmethod
    def get_or_create_feature_specification(
        cls,
        study_name: str,
        feature_class: str | None = None,
        phenotypes: list[PhenotypeCriteria] | None = None,
        **kwargs,
    ) -> str:
        """Create and return the identifier of a feature specification defined by the specifiers,
        if it does not exist. If it already exists, return the already-existing specification's
        identifier.
        """
        phenotypes_strs: list[str] = [
            phenotype_to_phenotype_str(phenotype) for phenotype in phenotypes
        ]
        args: list[str] = [study_name]
        query = '''
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
                (
                    (fs.specifier=%s AND fs.ordinality='1')'''
        for i, phenotype in enumerate(phenotypes):
            if i > 0:
                query += f'''
                    OR (fs.specifier=%s AND fs.ordinality={i+1})'''
            args.append(phenotype)
        query += '''
                ) AND
                fsn.derivation_method=%s
        ;
        '''
        args.append(describe_squidpy_feature_derivation_method())
        with DBCursor() as cursor:
            cursor.execute(query, args)
            rows = cursor.fetchall()
        feature_specifications = {row[0]: [] for row in rows}
        for row in rows:
            feature_specifications[row[0]].append(row[1])
        for key, specifiers in feature_specifications.items():
            if len(specifiers) == len(phenotypes):
                return key
        message = 'Creating feature with specifiers: (%s) %s'
        for _ in range(len(phenotypes)-1):
            message += ', %s'
        logger.debug(message, study_name, *phenotypes)
        return cls._create_feature_specification(study_name, phenotypes)

    @classmethod
    def _create_feature_specification(cls,
        study_name: str,
        phenotypes: list[str],
    ) -> str:
        specifiers = tuple(phenotypes)
        method = describe_squidpy_feature_derivation_method()
        return cls.create_feature_specification(specifiers, study_name, method)

    def have_feature_computed(self, feature_specification: str) -> None:
        # Ditto for this one.
        study_name, specifiers = SquidpyProvider.retrieve_specifiers(
            feature_specification)
        phenotypes: list[PhenotypeCriteria] = [phenotype_str_to_phenotype(s) for s in specifiers]
        sample_identifiers = SquidpyProvider.get_sample_identifiers(feature_specification)
        for sample_identifier in sample_identifiers:
            values = compute_squidpy_metrics_for_one_sample(
                self.get_cells(sample_identifier, study_name), phenotypes)
            # TODO: Figure out how to upload vector and matrix squidpy metrics.
            message = 'Computed feature values of %s: %s, %s'
            logger.debug(message, feature_specification, sample_identifier, values)
            with DBCursor() as cursor:
                for value in values:
                    add_feature_value(feature_specification, sample_identifier, value, cursor)
        SquidpyProvider.drop_pending_computation(feature_specification)
        logger.debug('Wrapped up squidpy metric calculation, feature "%s".', feature_specification)
        logger.debug('The samples considered were: %s', sample_identifiers)
