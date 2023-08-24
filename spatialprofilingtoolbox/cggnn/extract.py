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
    strata_to_use: list[int] | None,
) -> tuple[DataFrame, dict[int, str]]:
    """Get slide-level results."""
    df_assignments = df_assignments.set_index('specimen')
    df_strata = df_strata.set_index('stratum identifier')

    # Filter for strata to use
    if strata_to_use is not None:
        df_strata = df_strata.loc[sorted(strata_to_use)]
    if df_strata.shape[0] < 2:
        raise ValueError(f'Need at least 2 strata to classify, there are {df_strata.shape[0]}.')

    # Drop columns that're the same for all kept strata
    for col in df_strata.columns.tolist():
        if df_strata[col].unique().size == 1:
            df_strata = df_strata.drop(col, axis=1)

    # Compress remaining columns into a single string
    df_strata['label'] = '(' + df_strata.iloc[:, 0].astype(str)
    for i in range(1, df_strata.shape[1]):
        df_strata['label'] += df_strata.iloc[:, i].astype(str)
    df_strata['label'] += ')'
    df_strata = df_strata[['label']]

    # Merge with specimen assignments, keeping only selected strata
    df = merge(df_assignments, df_strata, on='stratum identifier', how='inner')[['label']]
    label_to_result = dict(enumerate(sort(df['label'].unique())))
    return df.replace({res: i for i, res in label_to_result.items()}), label_to_result


def extract_cggnn_data(
    spt_db_config_location: str,
    study: str,
    strata_to_use: list[int] | None,
) -> tuple[DataFrame, DataFrame, dict[int, str]]:
    """Extract information cg-gnn needs from SPT."""
    extractor = FeatureMatrixExtractor(database_config_file=spt_db_config_location)
    df_cell = _create_cell_df({
        slide: data.dataframe for slide, data in extractor.extract(study=study).items()
    })
    cohorts = extractor.extract_cohorts(study)
    df_label, label_to_result_text = _create_label_df(
        cohorts['assignments'],
        cohorts['strata'],
        strata_to_use,
    )
    return df_cell, df_label, label_to_result_text
