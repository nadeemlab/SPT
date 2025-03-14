
import re
from math import sqrt
from math import log10
from itertools import chain
from itertools import zip_longest
from urllib.parse import urlencode
from warnings import filterwarnings
from warnings import catch_warnings

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from pandas import read_csv
from pandas import read_sql
from pandas import concat
from pandas import DataFrame
from pandas import Series

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib import colormaps
from matplotlib.patches import Rectangle

from spatialprofilingtoolbox.db.database_connection import DBConnection
from spatialprofilingtoolbox.db.database_connection import DBCursor

from accessors import DataAccessor

aspect = 1.5
database_config_file = '.spt_db.config'


def shorten_study(study: str) -> str:
    return study.split(' collection: ')[0]


def retrieve_all_counts() -> DataFrame:
    with DBCursor(database_config_file=database_config_file) as cursor:
        cursor.execute('SELECT study from study_lookup;')
        studies = tuple(map(lambda r: r[0], cursor.fetchall()))
    query = 'phenotype-counts'
    access = DataAccessor(studies[0])
    df = None
    for study in studies:
        parameters = urlencode([('study', study), ('negative_marker', ''), ('positive_marker', '')])
        counts, _ = access._retrieve(query, parameters)
        _df = DataFrame(counts['counts'])
        _df['study'] = shorten_study(study)
        if df is None:
            df = _df
        else:
            df = concat([df, _df], axis=0)
    return df


ColorLookup = dict[tuple[str, str], tuple[str, int]]

def get_color_lookup() -> ColorLookup:
    df = read_csv('outcome_stratum_labels_annotations.tsv', sep='\t')
    lookup = {
        (row['study'], str(row['stratum_identifier'])): parse_matplotlib_color_spec(row['color'])
        for _, row in df.iterrows()
    }
    return lookup


def get_site_lookup() -> dict[tuple[str, str], str]:
    df = read_csv('anatomical_labels_annotations.tsv', sep='\t', keep_default_na=False)
    lookup = {
        (row['study'], str(row['source_site'])): row['label']
        for _, row in df.iterrows()
    }
    return lookup

def get_color(cmap_name: str, value: int):
    return colormaps[cmap_name](value)


def parse_matplotlib_color_spec(c: str) -> tuple[str, int]:
    parts = c.split(';')
    return (parts[0], int(parts[1]))


def simplify_int(i: int | float) -> str:
    i = int(i)
    scale = log10(i)
    if scale >= 6:
        return str(round((i / pow(10, 6)))) + 'm'
    if scale >= 3:
        return str(round((i / pow(10, 3)))) + 'k'
    return str(i)


def generate_box_representation_one_study(number_boxes_strata: Series, width_count: int, height_count: int, area_per_box: float, strata: DataFrame, color_lookup: ColorLookup, site_lookup: dict[tuple[str, str], str], total_cells: int) -> None:
    study = list(strata['study'])[0]
    color_list = [(1,1,1)] + [None] * 10
    for _stratum_identifier in number_boxes_strata.index:
        stratum_identifier = str(_stratum_identifier)
        color_list[int(stratum_identifier)] = get_color(*color_lookup[(study, stratum_identifier)])
    cmap = ListedColormap([v for v in color_list if not v is None])
    def _expand_list(stratum_identifier, size) -> list:
        return [int(stratum_identifier)] * size
    cellvalues = list(chain(*map(lambda args: _expand_list(*args), number_boxes_strata.items())))
    rows = zip_longest(*(iter(cellvalues),) * width_count, fillvalue=0)  # type: ignore
    df = DataFrame(rows)
    multiplier = 1.0
    box_width = sqrt(area_per_box)
    width = width_count * box_width * multiplier
    plt.figure(figsize=(width, width * aspect))

    ax = sns.heatmap(df, linewidth=0.5, square=True, cbar=False, xticklabels=False, yticklabels=False, cmap=cmap, vmin=0, vmax=df.values.max())
    source = list(strata['source_site'])[0]
    site_name = site_lookup[(study, source)]
    ax.set_title(site_name + '\n' + simplify_int(total_cells), fontsize=6)
    filename = re.sub(' ', '_', f'{source} {study}').lower()
    filename = re.sub('[^a-zA-Z0-9]', '', filename)
    plt.savefig(f'{filename}.svg')
    print(f'Wrote {filename}.svg')


def generate_legend(df: DataFrame) -> None:
    category = list(df['category label'])[0]
    legend_fig, legend_ax = plt.subplots(1, 1, figsize=(3, 1.5))
    items = [
        (
            Rectangle((0, 0), 0.25, 0.5, facecolor=get_color(*parse_matplotlib_color_spec(row['color']))),
            str(row['value label']),
        )
        for _, row in df.iterrows()
    ]
    handles, labels = tuple(zip(*items))

    legend_ax.legend(handles, labels, loc='center')
    legend_ax.axis('off')
    legend_fig.suptitle(category)
    legend_fig.tight_layout()
    sanitized = re.sub(r'[ \.\-\,]', '_', category).lower()
    legend_fig.savefig(f'legend_{sanitized}.svg')
    print(f'Wrote legend_{sanitized}.svg')


def generate_legends() -> None:
    labels = read_csv('outcome_stratum_labels_annotations.tsv', sep='\t')[['study', 'stratum_identifier', 'category label', 'value label', 'color']]
    for study, group in labels.groupby('study'):
        generate_legend(group)


def generate_box_representations(strata: DataFrame) -> None:
    color_lookup = get_color_lookup()
    site_lookup = get_site_lookup()
    df = strata
    for _, group in df.groupby(['source_site', 'study']):
        total = group['cell_count'].sum()
        target_area = pow(total / pow(10, 4), 1/3)
        groupstrata = group.copy().set_index('stratum_identifier')
        number_boxes_strata = groupstrata['sample_count']
        number_boxes = int(group['sample_count'].sum())
        area_per_box = target_area / number_boxes
        width_count = max(1, int(sqrt(number_boxes / aspect)))
        remainder = number_boxes % width_count
        height_count = (number_boxes // width_count) + 1 if remainder > 0 else int(number_boxes / width_count)
        generate_box_representation_one_study(number_boxes_strata, width_count, height_count, area_per_box, group, color_lookup, site_lookup, total)


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

    counts = retrieve_all_counts()
    counts = counts.rename(columns={'specimen': 'sample', 'count': 'cell_count'})
    counts = counts.set_index(['sample', 'study'])

    strata = strata.join(counts, on=['sample', 'study'])

    strata['ones'] = int(1)
    columns = ['source_site', 'study', 'stratum_identifier', 'local_temporal_position_indicator', 'subject_diagnosed_condition', 'subject_diagnosed_result']
    del strata['sample']
    counts = strata.groupby(columns).agg('sum')
    strata = counts.reset_index()
    strata = strata.rename(columns={'ones': 'sample_count'})
    strata.to_csv('strata.tsv', sep='\t', index=False)
    generate_box_representations(strata)


if __name__=='__main__':
    create_components()
    generate_legends()
