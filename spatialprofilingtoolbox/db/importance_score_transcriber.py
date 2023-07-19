"""Ingest important scores and upload them to the local db."""

from pandas import DataFrame, read_sql

from psycopg2.extensions import connection as Connection

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.create_data_analysis_study import (
    insert_new_data_analysis_study, data_analysis_study_exists)
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.workflow.common.two_cohort_feature_association_testing import \
    perform_tests
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def _recover_study_from_histological_structure(
        connection: Connection,
        histological_structure: int) -> str:
    """Recover the study name from the database given a histological_structure."""
    return read_sql(f"""
        SELECT
            hsi.histological_structure,
            sdmp.study
        FROM histological_structure_identification hsi
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        WHERE hsi.histological_structure={histological_structure}
        LIMIT 1
        ;
    """, connection)['study'][0]


def transcribe_importance(
    df: DataFrame,
        cohort_stratifier: str,
        database_connection_maker: DatabaseConnectionMaker,
        per_specimen_selection_number: int = 1000
) -> None:
    r"""Upload importance score output from a cg-gnn instance to the local db.

    Parameters:
        df: DataFrame
            One column, `importance_score`, indexed by `histological_structure`.
        cohort_stratifier: str
            Name of the classification cohort variable the GNN was trained on to produce
                the importance score.
        database_connection_maker: DatabaseConnectionMaker
        per_specimen_selection_number: int
            Grab this many of the most important cells from each specimen (or fewer if there
            aren\'t enough cells in the specimen).
    """
    # Recover the study from the histological_structure
    connection = database_connection_maker.get_connection()
    study: str = _recover_study_from_histological_structure(
        connection, df.iloc[0, 0])

    study_indicator: str = f'cell importance ({cohort_stratifier})'
    if data_analysis_study_exists(database_connection_maker, study, study_indicator):
        logger.warning('GNN study already exists for %s.', study)
        return
    connection = database_connection_maker.get_connection()

    # Get the slide for each histological_structure from the study
    df['specimen'] = read_sql("""
        SELECT
            hsi.histological_structure,
            sdmp.specimen
        FROM histological_structure_identification hsi
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        ;
    """, connection).set_index('histological_structure').loc[df.index, 'specimen']

    # Group by specimen and get the top n_most_important cells
    df_most_important = df.groupby('specimen').head(
        per_specimen_selection_number).reset_index(drop=False)
    df_most_important.rename(
        {'index': 'importance_order'}, axis=1, inplace=True)

    # Upload to db
    das = insert_new_data_analysis_study(
        database_connection_maker, study, study_indicator)
    with ADIFeaturesUploader(
        database_connection_maker,
        data_analysis_study=das,
        derivation_and_number_specifiers=(
            'For a given cohort stratification variable (the specifier), the integer rank of each '
            'cell (the subjects of the feature) with respect to the importance scores derived '
            'from a GNN trained on this variable.',
            1
        ),
        impute_zeros=True,
    ) as feature_uploader:
        for histological_structure, row in df_most_important.iterrows():
            feature_uploader.stage_feature_value(
                (histological_structure,), das, row['importance_order'])

        perform_tests(das, connection)
