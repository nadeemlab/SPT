"""Run through the entire SPT CG-GNN pipeline using a local db config."""

from argparse import ArgumentParser

from pandas import DataFrame

from spatialprofilingtoolbox.cggnn.extract import extract_cggnn_data
from spatialprofilingtoolbox.db.importance_score_transcriber import transcribe_importance
from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from cggnn.run import run  # type: ignore
    from torch import save
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'cggnn')
from cggnn.run import run
from torch import save


def parse_arguments():
    """Process command line arguments."""
    parser = ArgumentParser(
        prog='spt cggnn run',
        description="""Create cell graphs from SPT tables saved locally, train a graph neural
network on them, and save resultant model, metrics, and visualizations (if requested) to file.

`spt cggnn run` allows you to run the `cg-gnn` pip package directly from SPT. It combines `spt cggnn
extract` with the entire `cggnn.run` process into a single command.
"""
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
        '--strata',
        nargs='+',
        type=int,
        help='Specimen strata to use as labels, identified according to the "stratum identifier" '
             'in `explore-classes`. This should be given as space separated integers.\n'
             'If not provided, all strata will be used.',
        required=False,
        default=None
    )
    parser.add_argument(
        '--validation_data_percent',
        type=int,
        help='Percentage of data to use as validation data. Set to 0 if you want to do k-fold '
        'cross-validation later. (Training percentage is implicit.) Default 15%%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--test_data_percent',
        type=int,
        help='Percentage of data to use as the test set. (Training percentage is implicit.) '
        'Default 15%%.',
        default=15,
        required=False
    )
    parser.add_argument(
        '--disable_channels',
        action='store_true',
        help='Disable the use of channel information in the graph.',
    )
    parser.add_argument(
        '--disable_phenotypes',
        action='store_true',
        help='Disable the use of phenotype information in the graph.',
    )
    parser.add_argument(
        '--roi_side_length',
        type=int,
        help='Side length in pixels of the ROI areas we wish to generate.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--cells_per_slide_target',
        type=int,
        help='Used with the median cell density across all slides to determine the ROI size.',
        default=5_000,
        required=False
    )
    parser.add_argument(
        '--target_name',
        type=str,
        help='If given, build ROIs based only on cells with true values in this DataFrame column.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--in_ram',
        help='If the data should be stored in RAM.',
        action='store_true',
    )
    parser.add_argument(
        '-b',
        '--batch_size',
        type=int,
        help='Batch size to use during training.',
        default=1,
        required=False
    )
    parser.add_argument(
        '--epochs',
        type=int,
        help='Number of training epochs to do.',
        default=5,
        required=False
    )
    parser.add_argument(
        '-l',
        '--learning_rate',
        type=float,
        help='Learning rate to use during training.',
        default=1e-3,
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
        '--explainer_model',
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
    parser.add_argument(
        '--output_prefix',
        type=str,
        help='Saves output files with this prefix, if provided.',
        default=None,
        required=False
    )
    parser.add_argument(
        '--upload_importances',
        help='Whether to upload importance scores to the database.',
        action='store_true'
    )
    return parser.parse_args()


def save_importance(df: DataFrame, spt_db_config_location: str, study: str) -> None:
    """Save cell importance scores as defined by cggnn to the database."""
    transcribe_importance(df, spt_db_config_location, study)


if __name__ == "__main__":
    args = parse_arguments()
    df_cell, df_label, label_to_result = extract_cggnn_data(
        args.spt_db_config_location,
        args.study,
        args.strata,
    )
    model, importances = run(
        df_cell,
        df_label,
        label_to_result,
        validation_data_percent=args.validation_data_percent,
        test_data_percent=args.test_data_percent,
        use_channels=not args.disable_channels,
        use_phenotypes=not args.disable_phenotypes,
        roi_side_length=args.roi_side_length,
        cells_per_slide_target=args.cells_per_slide_target,
        target_name=args.target_name,
        in_ram=args.in_ram,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        k_folds=args.k_folds,
        explainer_model=args.explainer_model,
        merge_rois=args.merge_rois,
        prune_misclassified=args.prune_misclassified,
    )
    if (args.output_prefix is not None) or args.upload_importances:
        df = DataFrame.from_dict(
            importances,
            orient='index',
            columns=['importance_score'],
        )
        if args.output_prefix is not None:
            df.to_csv(f'{args.output_prefix}_importances.csv')
            save(model.state_dict(), f'{args.output_prefix}_model.pt')
        if args.upload_importances:
            save_importance(df, args.spt_db_config_location, args.study)
