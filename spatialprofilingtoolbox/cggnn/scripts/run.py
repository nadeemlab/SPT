"Run through the entire SPT CG-GNN pipeline."

from argparse import ArgumentParser

from spatialprofilingtoolbox.standalone_utilities.module_load_error import SuggestExtrasException
try:
    from cggnn.run_all import run_pipeline
except ModuleNotFoundError as e:
    SuggestExtrasException(e, 'cggnn')


def parse_arguments():
    "Process command line arguments."
    parser = ArgumentParser(
        prog='spt cggnn run',
        description='Create cell graphs from SPT tables, train a graph neural network on them, '
        'and save resultant model, metrics, and visualizations (if requested) to file.'
    )
    parser.add_argument(
        '--study',
        type=str,
        help='Name of the study to query data for in SPT.',
        required=True
    )
    parser.add_argument(
        '--host',
        type=str,
        help='Host SQL server IP.',
        required=True
    )
    parser.add_argument(
        '--dbname',
        type=str,
        help='Database in SQL server to query.',
        required=True
    )
    parser.add_argument(
        '--user',
        type=str,
        help='Server login username.',
        required=True
    )
    parser.add_argument(
        '--password',
        type=str,
        help='Server login password.',
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
        '--epochs', type=int, help='epochs.', default=10, required=False
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


if __name__ == "__main__":
    args = parse_arguments()
    run_pipeline(args.study,
                 args.host,
                 args.dbname,
                 args.user,
                 args.password,
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
