
import re
from math import log
from math import sqrt
from itertools import chain
from itertools import zip_longest
from urllib.parse import urlencode
from warnings import filterwarnings
from warnings import catch_warnings

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
database_config_file = '.spt_db.config'


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
    ax = sns.heatmap(df, linewidth=0.5, square=True, cbar=False, xticklabels=False, yticklabels=False)
    study = list(strata['study'])[0]
    source = list(strata['source_site'])[0]
    ax.set_title(f'{source} {study}')
    filename = re.sub(' ', '_', f'{source} {study}').lower()
    filename = re.sub('[^a-zA-Z0-9]', '', filename)
    plt.savefig(f'{filename}.svg')
    plt.show()


def generate_box_representations(summary: DataFrame, strata: DataFrame) -> None:
    summary = summary.set_index('study')
    df = strata.join(summary, on='study')
    print(df.to_string())
    for ss, group in df.groupby(['source_site', 'study']):
        target_area = pow(list(group['total_cells_study'])[0] / pow(10, 4), 1/3)
        groupstrata = group.copy().set_index('stratum_identifier')
        number_boxes_strata = groupstrata['count']
        number_boxes = int(group['count'].sum())
        area_per_box = target_area / number_boxes
        width_count = max(1, int(sqrt(number_boxes / aspect)))
        remainder = number_boxes % width_count
        height_count = (number_boxes // width_count) + 1 if remainder > 0 else int(number_boxes / width_count)
        print('')
        print('cells ', list(group['total_cells_study'])[0])
        print('target area ', target_area)
        print('number boxes ', number_boxes)
        print('area per box ', area_per_box)
        generate_box_representation_one_study(number_boxes_strata, width_count, height_count, area_per_box, group)


def combined_dataframe(query: str, studies: tuple[str, ...]) -> DataFrame:
    df = None
    for s in studies:
        with DBConnection(database_config_file=database_config_file, study=s) as connection:
            with catch_warnings():
                filterwarnings('ignore', message='pandas only supports SQLAlchemy', category=UserWarning)
                df_study = read_sql(query, connection)
        df_study['study'] = shorten_study(s)
        if df is None:
            df = df_study
        else:
            df = concat([df, df_study], axis=0)
    return df


def create_components():
    with DBCursor(database_config_file=database_config_file) as cursor:
        cursor.execute('SELECT study from study_lookup;')
        studies = tuple(map(lambda r: r[0], cursor.fetchall()))
    print('\n'.join(studies))

    query = '''
    SELECT sample, stratum_identifier, local_temporal_position_indicator, subject_diagnosed_condition, subject_diagnosed_result
    FROM sample_strata;
    '''
    strata = combined_dataframe(query, studies)

    query = '''
    SELECT specimen, source_site
    FROM specimen_collection_process
    ORDER BY source_site, specimen;
    '''
    anatomy = combined_dataframe(query, studies)
    print(anatomy.to_string())
    anatomy = anatomy.rename(columns={'specimen': 'sample'})
    anatomy = anatomy.set_index('sample')
    del anatomy['study']
    strata = strata.join(anatomy, on='sample')
    columns = ['source_site', 'study', 'stratum_identifier', 'local_temporal_position_indicator', 'subject_diagnosed_condition', 'subject_diagnosed_result']
    counts = strata.value_counts(columns).to_frame().reset_index()
    print(counts.to_string())
    strata = counts

    access = DataAccessor(studies[0])
    rows = []
    for s in studies:
        summary, _ = access._retrieve('study-summary', urlencode([('study', s)]))
        samples = summary['counts']['specimens']
        cells = summary['counts']['cells']
        rows.append((shorten_study(s), samples, cells, cells/samples))
    summary = DataFrame(rows, columns=['study', 'samples', 'total_cells_study', 'average'])
    print(summary.to_string())

    generate_box_representations(summary, strata)


if __name__=='__main__':
    create_components()
