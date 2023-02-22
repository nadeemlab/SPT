"Run through the entire SPT CG-GNN pipeline using a local db config."

from argparse import ArgumentParser
from typing import Dict, Tuple

from pandas import DataFrame, concat, merge
from numpy import sort

from spatialprofilingtoolbox.db.feature_matrix_extractor import FeatureMatrixExtractor
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from cggnn.run_all import run_with_dfs
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'cggnn')


def parse_arguments():
    "Process command line arguments."
    parser = ArgumentParser(
        prog='spt cggnn run',
        description='Create cell graphs from SPT tables saved locally, train a graph neural '
        'network on them, and save resultant model, metrics, and visualizations (if requested) '
        'to file.'
    )
    parser.add_argument(
        '--spt_db_config_location',
        type=str,
        help='File location for SPT DB config file.',
        required=True
    )
    parser.add_argument(
        '--study',
        type=str,
        help='Name of the study to query data for in SPT.',
        required=True
    )
    parser.add_argument(
        '--validation_data_percent',
        type=int,
        help='Percentage of data to use as validation data. Set to 0 if you want to do k-fold '
        'cross-validation later. (Training percentage is implicit.) Default 15%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--test_data_percent',
        type=int,
        help='Percentage of data to use as the test set. (Training percentage is implicit.) '
        'Default 15%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--roi_side_length',
        type=int,
        help='Side length in pixels of the ROI areas we wish to generate.',
        default=600,
        required=False
    )
    parser.add_argument(
        '--target_column',
        type=str,
        help='Phenotype column to use to build ROIs around.',
        default=None,
        required=False
    )
    parser.add_argument(
        '-b',
        '--batch_size',
        type=int,
        help='batch size.',
        default=1,
        required=False
    )
    parser.add_argument(
        '--epochs',
        type=int,
        help='epochs.',
        default=10,
        required=False
    )
    parser.add_argument(
        '-l',
        '--learning_rate',
        type=float,
        help='learning rate.',
        default=10e-3,
        required=False
    )
    parser.add_argument(
        '-k',
        '--k_folds',
        type=int,
        help='Folds to use in k-fold cross validation. 0 means don\'t use k-fold cross validation '
        'unless no validation dataset is provided, in which case k defaults to 3.',
        required=False,
        default=0
    )
    parser.add_argument(
        '--explainer',
        type=str,
        help='Which explainer type to use.',
        default='pp',
        required=False
    )
    parser.add_argument(
        '--merge_rois',
        help='Merge ROIs together by specimen.',
        action='store_true'
    )
    parser.add_argument(
        '--prune_misclassified',
        help='Remove entries for misclassified cell graphs when calculating separability scores.',
        action='store_true'
    )
    return parser.parse_args()


def _create_cell_df(cell_dfs: Dict[str, DataFrame], feature_names: Dict[str, str]) -> DataFrame:
    "Find chemical species, phenotypes, and locations and merge into a DataFrame."

    for specimen, df_specimen in cell_dfs.items():
        df_specimen.rename({ft_id: 'FT_' + ft_name for ft_id, ft_name in feature_names.items()},
                           axis=1, inplace=True)
        # TODO: Create phenotype columns
        df_specimen.rename({'pixel x': 'center_x', 'pixel y': 'center_y'},
                           axis=1, inplace=True)
        df_specimen['specimen'] = specimen

    # TODO: Reorder so that it's feature, specimen, phenotype, xy
    # TODO: Verify histological structure ID or recreate one
    df = concat(cell_dfs.values(), axis=0)
    df.index.name = 'histological_structure'
    return df


def _create_label_df(df_assignments: DataFrame,
                     df_strata: DataFrame) -> Tuple[DataFrame, Dict[int, str]]:
    """Get slide-level results."""
    df = merge(df_assignments, df_strata, on='stratum identifier', how='left')[
        ['specimen', 'subject diagnosed result']].rename(
        {'specimen': 'slide', 'subject diagnosed result': 'result'}, axis=1)
    label_to_result = dict(enumerate(sort(df['result'].unique())))
    return df.replace({res: i for i, res in label_to_result.items()}), label_to_result


if __name__ == "__main__":
    args = parse_arguments()
    study_data: Dict[str, Dict] = FeatureMatrixExtractor.extract(
        args.spt_db_config_location)[args.study]

    df_cell = _create_cell_df(
        {slide: data['dataframe']
            for slide, data in study_data['feature matrices'].items()},
        study_data['channel symbols by column name'])
    df_label, label_to_result_text = _create_label_df(
        study_data['sample cohorts']['assignments'],
        study_data['sample cohorts']['strata'])

    run_with_dfs(df_cell,
                 df_label,
                 label_to_result_text,
                 args.validation_data_percent,
                 args.test_data_percent,
                 args.roi_side_length,
                 args.target_column,
                 args.batch_size,
                 args.epochs,
                 args.learning_rate,
                 args.k_folds,
                 args.explainer,
                 args.merge_rois,
                 args.prune_misclassified)
