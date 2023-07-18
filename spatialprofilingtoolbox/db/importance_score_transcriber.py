"""Ingest important scores and upload them to the local db."""

from pandas import DataFrame, read_sql

from spatialprofilingtoolbox.db.database_connection import DatabaseConnectionMaker
from spatialprofilingtoolbox.db.create_data_analysis_study import (insert_new_data_analysis_study,
                                                                   data_analysis_study_exists)
from spatialprofilingtoolbox.workflow.common.export_features import ADIFeaturesUploader
from spatialprofilingtoolbox.workflow.common.two_cohort_feature_association_testing import \
    perform_tests
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


def transcribe_importance(df: DataFrame,
                          target_var: str,
                          database_connection_maker: DatabaseConnectionMaker,
                          n_most_important: int = 1000) -> None:
    """Upload importance score output from a cg-gnn instance to the local db.

    Parameters:
        df: DataFrame
            One column, `importance_score`, indexed by `histological_structure`.
        target_var: str
            What variable the GNN was trained on to produce importance_score.
        database_connection_maker: DatabaseConnectionMaker
        n_most_important: int
            Grab this many of the most important cells from each slide.
    """
    # Recover the study from the histological_structure
    connection = database_connection_maker.get_connection()
    study: str = read_sql(f"""
        SELECT
            hsi.histological_structure,
            sdmp.study
        FROM histological_structure_identification hsi
            JOIN data_file df
                ON hsi.data_source=df.sha256_hash
            JOIN specimen_data_measurement_process sdmp
                ON df.source_generation_process=sdmp.identifier
        WHERE hsi.histological_structure={df.iloc[0,0]}
        LIMIT 1
        ;
    """, connection)['study'][0]

    study_indicator: str = f'cell importance ({target_var})'
    if data_analysis_study_exists(database_connection_maker, study, study_indicator):
        logger.debug('Fractions study already exists for %s.', study)
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
    df_n = df.groupby('specimen').head(
        n_most_important).reset_index(drop=False)
    df_n.rename({'index': 'importance_order'}, axis=1, inplace=True)

    # Upload to db
    das = insert_new_data_analysis_study(
        database_connection_maker, study, study_indicator)
    with ADIFeaturesUploader(
        database_connection_maker,
        data_analysis_study=das,
        derivation_and_number_specifiers=(
            'For a given target variable, a trained GNN identifies how important each cell is to '
            'the specimen\'s predicted classification.',
            1),
        impute_zeros=True,
    ) as feature_uploader:
        for histological_structure, row in df_n.iterrows():
            feature_uploader.stage_feature_value(
                (histological_structure,), das, row['importance_order'])

        perform_tests(das, connection)
