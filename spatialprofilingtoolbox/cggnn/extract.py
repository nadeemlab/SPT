"""Extract information cg-gnn needs from SPT."""

from typing import cast

from pandas import DataFrame, concat, merge  # type: ignore
from numpy import sort  # type: ignore

from spatialprofilingtoolbox.db.feature_matrix_extractor import (
    FeatureMatrixExtractor,
    Bundle,
)


def _create_cell_df(
    dfs_by_specimen: dict[str, DataFrame],
    feature_names: dict[str, str],
) -> DataFrame:
    """Find simple and complex phenotypes, and locations and merge into a DataFrame."""
    feature_ids_to_names = {ft_id: 'FT_' + ft_name for ft_id, ft_name in feature_names.items()}
    for specimen, df_specimen in dfs_by_specimen.items():
        df_specimen.rename(feature_ids_to_names, axis=1, inplace=True)
        # TODO: Create phenotype columns
        df_specimen.rename(
            {'pixel x': 'center_x', 'pixel y': 'center_y'},
            axis=1,
            inplace=True,
        )
        df_specimen['specimen'] = specimen

    # TODO: Reorder so that it's simple phenotype, specimen, complex phenotype, x, y
    df = concat(dfs_by_specimen.values(), axis=0)
    df.index.name = 'histological_structure'
    return df


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
    study_data = cast(Bundle, extractor.extract(study=study))
    df_cell = _create_cell_df(
        {
            slide: cast(DataFrame, data['dataframe'])
            for slide, data in study_data['feature matrices'].items()
        },
        cast(dict[str, str], study_data['channel symbols by column name']),
    )
    df_label, label_to_result_text = _create_label_df(
        cast(DataFrame, study_data['sample cohorts']['assignments']),
        cast(DataFrame, study_data['sample cohorts']['strata']),
    )
    return df_cell, df_label, label_to_result_text
