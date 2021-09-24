
from .dichotomization import Dichotomizer
from .log_formats import colorized_logger

logger = colorized_logger(__name__)


class ComputationalDesign:
    """
    Subclass this object to collect together any metadata that is specific to a
    particular pipeline/workflow's computation stage.
    """
    def __init__(self, dichotomize: bool=False, **kwargs):
        self.dichotomize = dichotomize

    def preprocess(self, table, dataset_design):
        if self.dichotomize:
            for phenotype in dataset_design.get_elementary_phenotype_names():
                intensity = dataset_design.get_intensity_column_name(phenotype_name)
                if not intensity in table.columns:
                    dataset_design.add_combined_intensity_column(table, phenotype)
                Dichotomizer.dichotomize(
                    phenotype,
                    table,
                    dataset_design=dataset_design,
                )
                feature = dataset_design.get_feature_name(phenotype)
                number_positives = sum(cells[feature])
                logger.info(
                    'Dichotomization column "%s" written. %s positives.',
                    feature,
                    number_positives,
                )

    def get_database_uri(self):
        """
        Each computational workflow may request persistent storage of intermediate data.
        The implementation class should provide the URI of the database in which to
        store this data.

        Currently, only local sqlite databases are supported. Future version may
        support remote SQL database connections.

        :return: The Uniform Resource Identifier (URI) identifying the database.
        :rtype: str
        """
        pass
