
import re
from math import log
from math import sqrt
from itertools import chain
from itertools import zip_longest
from urllib.parse import urlencode

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from pandas import read_sql
from pandas import concat
from pandas import DataFrame
from pandas import Series

import seaborn as sns
import matplotlib.pyplot as plt

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor

from accessors import DataAccessor

aspect = 1.5


def shorten_study(study: str) -> str:
    return study.split(' collection: ')[0]


def generate_box_representation_one_study(number_boxes_strata: Series, width_count: int, height_count: int, area_per_box: float, strata: DataFrame) -> None:
    def _expand_list(stratum_identifier, size) -> list:
        return [int(stratum_identifier)] * size
    cellvalues = list(chain(*map(lambda args: _expand_list(*args), number_boxes_strata.items())))
    rows = zip_longest(*(iter(cellvalues),) * width_count, fillvalue=0)  # type: ignore
    df = DataFrame(rows)
    multiplier = 1.0
    box_width = sqrt(area_per_box)
    width = width_count * box_width * multiplier
    print('width ', width_count, ' * ' , area_per_box, ' * ' , multiplier, ' = ', width)
    plt.figure(figsize=(width, width * aspect))
    ax = sns.heatmap(df, linewidth=0.1, square=True, cbar=False, xticklabels=False, yticklabels=False)
    study = list(strata['study'])[0]
    ax.set_title(study)
    filename = re.sub(' ', '_', study).lower()
    plt.savefig(f'{filename}.svg')
    plt.show()


def generate_box_representations(summary: DataFrame, strata: DataFrame) -> None:
    summary = summary.set_index('study')
    df = strata.join(summary, on='study')
    print(df.to_string())
    for s, group in df.groupby('study'):
        target_area = pow(list(group['total_cells_study'])[0] / pow(10, 4), 1/3)
        groupstrata = group.copy().set_index('stratum_identifier')
        number_boxes_strata = groupstrata['count']
        number_boxes = int(group['count'].sum())
        area_per_box = target_area / number_boxes
        width_count = int(sqrt(number_boxes / aspect))
        remainder = number_boxes % width_count
        height_count = (number_boxes // width_count) + 1 if remainder > 0 else int(number_boxes / width_count)
        print('')
        print('cells ', list(group['total_cells_study'])[0])
        print('target area ', target_area)
        print('number boxes ', number_boxes)
        print('area per box ', area_per_box)
        generate_box_representation_one_study(number_boxes_strata, width_count, height_count, area_per_box, group)


def create_components():
    database_config_file = '.spt_db.config'
    with DBCursor(database_config_file=database_config_file) as cursor:
        cursor.execute('SELECT study from study_lookup;')
        studies = tuple(map(lambda r: r[0], cursor.fetchall()))
    print('\n'.join(studies))
    strata = None
    for s in studies:
        with DBConnection(database_config_file=database_config_file, study=s) as connection:
            df = read_sql(
                '''
                SELECT COUNT(*), stratum_identifier, local_temporal_position_indicator, subject_diagnosed_condition, subject_diagnosed_result
                FROM sample_strata
                GROUP BY stratum_identifier, local_temporal_position_indicator, subject_diagnosed_condition, subject_diagnosed_result;
                ''',
                connection,
            )
        df['study'] = shorten_study(s)
        if strata is None:
            strata = df
        else:
            strata = concat([strata, df], axis=0)
    print(strata.to_string())

    access = DataAccessor(studies[0])
    rows = []
    for s in studies:
        summary, _ = access._retrieve('study-summary', urlencode([('study', s)]))
        samples = summary['counts']['specimens']
        cells = summary['counts']['cells']
        rows.append((s, samples, cells, cells/samples))
    summary = DataFrame(rows, columns=['study', 'samples', 'total_cells_study', 'average'])
    summary['study'] = summary['study'].apply(shorten_study)
    print(summary.to_string())

    generate_box_representations(summary, strata)


if __name__=='__main__':
    create_components()
