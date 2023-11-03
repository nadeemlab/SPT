"""Ingest importance scores and upload them to the local database."""
from typing import cast

from pandas import DataFrame
from pandas import read_sql
from psycopg2.extensions import connection as Connection

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.db.describe_features import get_feature_description
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def transcribe_importance(
    df: DataFrame,
    database_config_file: str,
    study: str,
    per_specimen_selection_number: int = 1000,
    cohort_stratifier: str = '',
) -> None:
    r"""Upload importance score output from a cg-gnn instance to the local db.

    Parameters:
        df: DataFrame
            One column, `importance`, indexed by `histological_structure`.
        connection: psycopg2.extensions.connection
        per_specimen_selection_number: int
            Grab this many of the most important cells from each specimen (or fewer if there
            aren't enough cells in the specimen).
        cohort_stratifier: str = ''
            Name of the classification cohort variable the GNN was trained on to produce
                the importance score.
    """
    if study is None:
        message = 'Study specifier not supplied.'
        logger.error(message)
        raise ValueError(message)
    indicator: str = 'cell importance'
    with DBConnection(database_config_file=database_config_file, study=study) as connection:
        data_analysis_study = DataAnalysisStudyFactory(connection, study, indicator).create()
        _add_slide_column(connection, df)
        df_most_important = _group_and_filter(df, per_specimen_selection_number)
        _upload(df_most_important, connection, data_analysis_study, cohort_stratifier)


def _add_slide_column(connection: Connection, df: DataFrame) -> None:
    lookup = read_sql("""
        SELECT
            hsi.histological_structure,
            sdmp.specimen
        FROM histological_structure_identification hsi
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        ;
    """, connection)
    lookup['histological_structure'] = lookup['histological_structure'].astype(int)
    reindexed = lookup.set_index('histological_structure')
    df['specimen'] = reindexed.loc[df.index, 'specimen']


def _group_and_filter(df: DataFrame, filter_number: int) -> DataFrame:
    ordered = df.sort_values(by='importance', ascending=False)
    ordered['importance_order'] = 1
    grouped = ordered.groupby('specimen')
    ranks = grouped['importance_order'].cumsum()
    df_most_important = \
        grouped.head(filter_number).drop('importance_order', axis=1).join(ranks, how='left')
    return df_most_important


def _upload(
    df: DataFrame,
    connection: Connection,
    data_analysis_study: str,
    cohort_stratifier: str,
) -> None:
    with ADIFeaturesUploader(
        connection,
        data_analysis_study=data_analysis_study,
        derivation_and_number_specifiers=(get_feature_description("gnn importance score"), 1),
        impute_zeros=True,
    ) as feature_uploader:
        for histological_structure, row in df.iterrows():
            feature_uploader.stage_feature_value(
                (cohort_stratifier,),
                str(histological_structure),
                row['importance_order'],
            )
