"""Merge TIFF channel file data and aggregate over cell segments."""

import sys
import warnings

from pandas import DataFrame
from pandas import Series
from pandas import merge
from numpy import nanmean
from numpy import isnan

from _extraction_formats import create_sparse_dataframe  # pylint: disable=E0611

sys.path.append('../../convenience_scripts')
from bimodality_assessor import BimodalityAssessor

def aggregate_cell(group: DataFrame, channel_name: str) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        value = float(nanmean(group[channel_name]))
    if isnan(value):
        value = 0
    return value

def aggregate_cell_position(group: DataFrame, which: int) -> float:
    columns = ['Column', 'Row']
    column = columns[which]
    return float(nanmean(group[column]))

class Aggregator:
    """Aggregate channel and position information over cell segments."""
    def __init__(self, channel_names: list[str]):
        self.channel_names = channel_names

    def aggregate(self, group: DataFrame) -> Series:
        if group.shape[0] == 0:
            raise ValueError('Some cell has no pixels.')
        aggregation = Series({
            **{
                'XMax': aggregate_cell_position(group, 0),
                'XMin': aggregate_cell_position(group, 0),
                'YMax': aggregate_cell_position(group, 1),
                'YMin': aggregate_cell_position(group, 1),
            },
            **{
                f'{channel_name} Intensity': aggregate_cell(group, channel_name)
                for channel_name in self.channel_names
            }
        })
        return aggregation

def add_binary_vector(channel_name, df) -> bool:
    feature_values = df[f'{channel_name} Intensity']
    assessor = BimodalityAssessor(feature_values)
    quality = assessor.get_average_mahalanobis_distance()
    if quality >= 0.5:
        binary = assessor.get_dichotomized_feature(use_threshold=True)
        df[f'{channel_name} Positive'] = binary
        return True
    threshold = nanmean(feature_values)
    def thresholding(value):
        if isnan(value):
            return 0
        return 1 if value >= threshold else 0
    df[f'{channel_name} Positive'] = df[f'{channel_name} Intensity'].apply(thresholding)
    return False

def create_cell_measurement_table(channel_files: dict[str, str], mask_file: str) -> DataFrame:
    df = create_sparse_dataframe(
        mask_file,
        value_column='Cell segment',
        index_by_position=True,
        keep_position_columns=True,
    )

    for channel_name, channel_file in channel_files.items():
        channel_df = create_sparse_dataframe(
            channel_file,
            value_column = str(channel_name),
            index_by_position = True,
        )
        df = merge(df, channel_df, how='left', left_index=True, right_index=True)
    aggregator = Aggregator(list(channel_files.keys()))
    measurements = df.groupby('Cell segment').apply(aggregator.aggregate)
    gmm_thresholding = []
    mean_thresholding = []
    for channel_name in channel_files.keys():
        used_gmm = add_binary_vector(channel_name, measurements)
        if used_gmm:
            gmm_thresholding.append(channel_name)
        else:
            mean_thresholding.append(channel_name)
    print(f'Used GMM thresholding for:  {sorted(gmm_thresholding)}')
    print(f'Used mean thresholding for: {sorted(mean_thresholding)}')
    return measurements
