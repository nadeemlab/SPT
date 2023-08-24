"""Extract information cg-gnn needs from SPT."""

from pandas import DataFrame, concat, merge  # type: ignore
from numpy import sort  # type: ignore

from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor


def _create_cell_df(dfs_by_specimen: dict[str, DataFrame]) -> DataFrame:
    """Find simple and complex phenotypes, and locations and merge into a DataFrame."""
    for specimen, df_specimen in dfs_by_specimen.items():
        df_specimen['specimen'] = specimen

    df = concat(dfs_by_specimen.values(), axis=0)
    df.index.name = 'histological_structure'
    # Reorder columns so it's specimen, xy, channels, and phenotypes
    column_order = ['specimen', 'pixel x', 'pixel y']
    column_order.extend(df.columns[df.columns.str.startswith('C ')])
    column_order.extend(df.columns[df.columns.str.startswith('P ')])
    return df[column_order]


def _create_label_df(
    df_assignments: DataFrame,
    df_strata: DataFrame,
) -> tuple[DataFrame, dict[int, str]]:
    """Get slide-level results."""
    df = merge(df_assignments, df_strata, on='stratum identifier', how='left')[
        ['specimen', 'subject diagnosed result']
    ].rename(
        {'specimen': 'slide', 'subject diagnosed result': 'result'},
        axis=1,
    )
    label_to_result = dict(enumerate(sort(df['result'].unique())))
    return df.replace({res: i for i, res in label_to_result.items()}), label_to_result


def extract_cggnn_data(
    spt_db_config_location: str,
    study: str,
) -> tuple[DataFrame, DataFrame, dict[int, str]]:
    """Extract information cg-gnn needs from SPT."""
    extractor = FeatureMatrixExtractor(database_config_file=spt_db_config_location)
    df_cell = _create_cell_df({
        slide: data.dataframe for slide, data in extractor.extract(study=study).items()
    })
    cohorts = extractor.extract_cohorts(study)
    df_label, label_to_result_text = _create_label_df(cohorts['assignments'], cohorts['strata'])
    return df_cell, df_label, label_to_result_text
