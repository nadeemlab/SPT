"""Ingest importance scores and upload them to the local database."""
from typing import cast

from pandas import DataFrame
from pandas import read_sql
from psycopg2.extensions import connection as Connection

from spatialprofilingtoolbox.db.create_data_analysis_study import DataAnalysisStudyFactory
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox import get_feature_description
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def transcribe_importance(
    df: DataFrame,
    connection: Connection,
    per_specimen_selection_number: int = 1000,
    cohort_stratifier: str='default sample stratification',
) -> None:
    r"""Upload importance score output from a cg-gnn instance to the local db.

    Parameters:
        df: DataFrame
            One column, `importance_score`, indexed by `histological_structure`.
        cohort_stratifier: str
            Name of the classification cohort variable the GNN was trained on to produce
                the importance score.
        connection: psycopg2.extensions.connection
        per_specimen_selection_number: int
            Grab this many of the most important cells from each specimen (or fewer if there
            aren't enough cells in the specimen).
    """
    study = _get_referenced_study(connection, df)
    indicator: str = 'cell importance'
    data_analysis_study = DataAnalysisStudyFactory(connection, study, indicator).create()
    _add_slide_column(connection, df)
    df_most_important = _group_and_filter(df, per_specimen_selection_number)
    _upload(df_most_important, connection, data_analysis_study, cohort_stratifier)


def _get_referenced_study(connection, df: DataFrame) -> str:
    first_index = str(df.index[0])
    return _recover_study_from_histological_structure(connection, first_index)


def _recover_study_from_histological_structure(
    connection: Connection,
    histological_structure,
) -> str:
    value = read_sql(f"""
        SELECT
            hsi.histological_structure,
            sdmp.study
        FROM histological_structure_identification hsi
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        WHERE hsi.histological_structure='{histological_structure}'
        LIMIT 1
        ;
    """, connection)['study'][0]
    return cast(str, value)


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
    reindexed = lookup.set_index('histological_structure')
    df['specimen'] = reindexed.loc[df.index, 'specimen']


def _group_and_filter(df: DataFrame, filter_number) -> DataFrame:
    ordered = df.sort_values(by='importance_score')
    df_most_important = ordered.groupby('specimen').head(filter_number)
    df_most_important = df_most_important.reset_index(drop=False)
    df_most_important['importance_order'] = df_most_important.index
    return df_most_important


def _upload(
    df: DataFrame,
    connection: Connection,
    data_analysis_study: str,
    cohort_stratifier: str,
) -> None:
    with ADIFeaturesUploader(
        None,
        data_analysis_study=data_analysis_study,
        derivation_and_number_specifiers=(get_feature_description("gnn importance score"), 1),
        impute_zeros=True,
        connection=connection,
    ) as feature_uploader:
        for _, row in df.iterrows():
            feature_uploader.stage_feature_value(
                (cohort_stratifier,),
                row['histological_structure'],
                row['importance_order'],
            )
