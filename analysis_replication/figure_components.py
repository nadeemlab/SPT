
from collections import OrderedDict
from os import mkdir
from os.path import join
from os.path import exists
import re
from math import sqrt
from math import log10
from itertools import chain
from itertools import zip_longest
from urllib.parse import urlencode
from warnings import filterwarnings
from warnings import catch_warnings

from attrs import define

import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from pandas import Index
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


class GatherSampleSummaryData:
    database_config_file: str

    def __init__(self, database_config_file = '.spt_db.config'):
        self.database_config_file = database_config_file
        self.studies = self.get_studies()

    def get(self) -> DataFrame:
        filename = 'sources_and_strata.tsv'
        if not exists(filename):
            sources_and_strata = self._gather_source_sites_and_strata()
            sources_and_strata.to_csv(filename, sep='\t', index=False)
        else:
            sources_and_strata = read_csv(filename, sep='\t', keep_default_na=False)
        return sources_and_strata

    def _gather_source_sites_and_strata(self) -> DataFrame:
        strata = self.get_sample_strata()
        source_sites = self.get_source_site_assignments()
        source_sites_and_strata_by_sample = strata.join(source_sites, on='sample')
        cell_counts = self.get_cell_counts()
        source_sites_strata_counts_by_sample = source_sites_and_strata_by_sample.join(cell_counts, on=['sample', 'study'])
        source_sites_strata_counts_by_sample['ones'] = int(1)
        columns = ['source_site', 'study', 'stratum_identifier', 'local_temporal_position_indicator', 'subject_diagnosed_condition', 'subject_diagnosed_result']
        del source_sites_strata_counts_by_sample['sample']
        aggregated = source_sites_strata_counts_by_sample.groupby(columns).agg('sum')
        aggregated = aggregated.reset_index()
        aggregated = aggregated.rename(columns={'ones': 'sample_count'})
        return aggregated

    def get_sample_strata(self) -> DataFrame:
        query = '''
        SELECT sample, stratum_identifier, local_temporal_position_indicator, subject_diagnosed_condition, subject_diagnosed_result
        FROM sample_strata;
        '''
        return self.dataframe_combined_over_studies(query)

    def get_source_site_assignments(self) -> DataFrame:
        query = '''
        SELECT specimen, source_site
        FROM specimen_collection_process
        ORDER BY source_site, specimen;
        '''
        df = self.dataframe_combined_over_studies(query)
        df = df.rename(columns={'specimen': 'sample'})
        df = df.set_index('sample')
        del df['study']
        return df

    def dataframe_combined_over_studies(self, query: str) -> DataFrame:
        df = None
        for study in self.studies:
            with DBConnection(database_config_file=self.database_config_file, study=study) as connection:
                with catch_warnings():
                    filterwarnings('ignore', message='pandas only supports SQLAlchemy', category=UserWarning)
                    df_study = read_sql(query, connection)
            df_study['study'] = self.abbreviate_study_name(study)
            if df is None:
                df = df_study
            else:
                df = concat([df, df_study], axis=0)
        return df

    def get_cell_counts(self) -> DataFrame:
        counts = self.retrieve_cell_counts()
        counts = counts.rename(columns={'specimen': 'sample', 'count': 'cell_count'})
        counts = counts.set_index(['sample', 'study'])
        return counts

    def retrieve_cell_counts(self) -> DataFrame:
        query = 'phenotype-counts'
        access = DataAccessor(self.studies[0])
        df = None
        for study in self.studies:
            parameters = urlencode([('study', study), ('negative_marker', ''), ('positive_marker', '')])
            counts, _ = access._retrieve(query, parameters)
            _df = DataFrame(counts['counts'])
            _df['study'] = self.abbreviate_study_name(study)
            if df is None:
                df = _df
            else:
                df = concat([df, _df], axis=0)
        return df

    def get_studies(self) -> tuple[str, ...]:
        with DBCursor(database_config_file=self.database_config_file) as cursor:
            cursor.execute('SELECT study from study_lookup;')
            studies = tuple(map(lambda r: r[0], cursor.fetchall()))
        return studies

    @staticmethod
    def abbreviate_study_name(study: str) -> str:
        return study.split(' collection: ')[0]


ColorCodeLookup = dict[tuple[str, str], tuple[str, int]]

class ColorLookup:
    _lookup: ColorCodeLookup

    def __init__(self):
        df = read_csv('outcome_stratum_labels_annotations.tsv', sep='\t')
        lookup = {
            (row['study'], str(row['stratum_identifier'])): self._parse_matplotlib_color_spec(row['color'])
            for _, row in df.iterrows()
        }
        self._lookup = lookup

    def lookup(self, study: str, stratum_identifier: str) -> tuple[float, float, float, float]:
        return self._get_mpl_color(*self._lookup[(study, stratum_identifier)])

    @staticmethod
    def _parse_matplotlib_color_spec(c: str) -> tuple[str, int]:
        parts = c.split(';')
        return (parts[0], int(parts[1]))

    @staticmethod
    def _get_mpl_color(cmap_name: str, value: int):
        return colormaps[cmap_name](value)


class SiteLabels:
    labels: dict[tuple[str, str], str]

    def __init__(self):
        self.labels = self._get_site_labels()

    def lookup(self, study: str, source_site: str) -> str:
        return self.labels[(study, source_site)]

    def _get_site_labels(self) -> dict[tuple[str, str], str]:
        df = read_csv('anatomical_labels_annotations.tsv', sep='\t', keep_default_na=False)
        lookup = {
            (row['study'], str(row['source_site'])): row['label']
            for _, row in df.iterrows()
        }
        return lookup


class OutcomeLabels:
    stratum_labels: dict[tuple[str, str], str]
    category_labels: dict[str, str]

    def __init__(self):
        df = read_csv('outcome_stratum_labels_annotations.tsv', sep='\t')
        df = df[~df['value label'].isna()]
        lookup = {
            row['study']: str(row['category label'])
            for _, row in df[['study', 'category label']].drop_duplicates().iterrows()
        }
        self.category_labels = lookup
        lookup = {
            (row['study'], str(row['stratum_identifier'])): str(row['value label'])
            for _, row in df.iterrows()
        }
        self.stratum_labels = lookup

    def get_category_label(self, study: str) -> str:
        return self.category_labels[study]

    def get_stratum_label(self, study: str, stratum_identifier: str) -> str:
        return self.stratum_labels[(study, stratum_identifier)]

    def get_studies(self) -> tuple[str, ...]:
        return tuple(self.category_labels.keys())

    def get_strata(self, study: str) -> tuple[tuple[str, str], ...]:
        return tuple(filter(lambda k: k[0] == study, self.stratum_labels.keys()))


class GenerateLegends:
    verbose: bool
    outcome_labels: OutcomeLabels
    subpath: str

    def __init__(self, subpath: str, verbose: bool=False):
        self.subpath = subpath
        self.verbose = verbose

    def generate(self) -> None:
        self.outcome_labels = OutcomeLabels()
        self.color_lookup = ColorLookup()
        for study in self.outcome_labels.get_studies():
            self._generate_legend(study)

    def _generate_legend(self, study: str) -> None:
        category = self.outcome_labels.get_category_label(study)
        legend_fig, legend_ax = plt.subplots(1, 1, figsize=(2, 1))
        items = [
            (
                Rectangle((0, 0), 0.25, 0.5, facecolor=self.color_lookup.lookup(study, stratum_identifier)),
                self.outcome_labels.get_stratum_label(study, stratum_identifier),
            )
            for _, stratum_identifier in self.outcome_labels.get_strata(study)
        ]
        handles, labels = tuple(zip(*items))
        legend_ax.legend(handles, labels, loc='center')
        legend_ax.axis('off')
        # legend_fig.suptitle(category)
        # legend_fig.tight_layout()
        filename = self._form_filename(category)
        legend_fig.savefig(filename, pad_inches=0, bbox_inches='tight')
        plt.close()
        if self.verbose:
            print(f'Wrote {filename}')

    def _form_filename(self, category: str) -> str:
        sanitized = re.sub(r'[ \.\-\,]', '_', category).lower()
        return join(self.subpath, f'legend_{sanitized}.svg')


@define
class BoxDiagramSpecification:
    number_boxes_by_stratum: OrderedDict[str, int]
    width_count: int
    height_count: int
    aspect: float
    area_per_box: float
    total_cells: int
    study: str
    source_site: str


class SampleBoxesOverview:
    verbose: bool
    subpath: str
    sources_and_strata: DataFrame
    color_lookup: ColorLookup
    site_labels: SiteLabels

    def __init__(self, subpath='diagram_components'):
        self.subpath = subpath
        self._create_subdirectory()

    def _create_subdirectory(self) -> None:
        try:
            mkdir(self.subpath)
        except FileExistsError:
            pass

    def create(self, verbose: bool=False) -> None:
        self.verbose = verbose
        self._retrieve_input_data()
        self._generate_box_diagrams()
        GenerateLegends(self.subpath, verbose=verbose).generate()

    def _retrieve_input_data(self) -> None:
        self.sources_and_strata = GatherSampleSummaryData().get()
        self.color_lookup = ColorLookup()
        self.site_labels = SiteLabels()

    def _generate_box_diagrams(self) -> None:
        if self.verbose:
            print(self.sources_and_strata.to_string())
        for (source_site, study), group in self.sources_and_strata.groupby(['source_site', 'study']):
            spec = self._specify_box_diagram(study, source_site, group)
            self.generate_box_representation_one_study(spec)

    def _specify_box_diagram(self, study: str, source_site: str, counts: DataFrame) -> BoxDiagramSpecification:
        total_cells = float(counts['cell_count'].sum())
        target_area = pow(total_cells / pow(10, 5), 1/2)
        groupstrata = counts.copy().set_index('stratum_identifier')
        number_boxes_strata = groupstrata['sample_count']
        number_boxes_by_stratum = OrderedDict()
        for key, value in number_boxes_strata.items():
            number_boxes_by_stratum[key] = int(value)
        number_boxes = int(counts['sample_count'].sum())
        area_per_box = target_area / number_boxes
        aspect_attempted = 1.6
        width_count = max(1, round(sqrt(number_boxes / aspect_attempted)))
        remainder = number_boxes % width_count
        height_count = (number_boxes // width_count) + 1 if remainder > 0 else int(number_boxes / width_count)
        aspect = height_count / width_count
        return BoxDiagramSpecification(
            number_boxes_by_stratum,
            width_count,
            height_count,
            aspect,
            area_per_box,
            total_cells,
            study,
            source_site,
        )

    def generate_box_representation_one_study(self, spec: BoxDiagramSpecification) -> None:
        cmap = self._form_cmap(spec)
        rows = self._form_uniform_rows(spec)
        df = DataFrame(rows)
        box_width = sqrt(spec.area_per_box)
        width = spec.width_count * box_width
        plt.figure(figsize=(width, width * spec.aspect))

        ax = sns.heatmap(df, linewidth=1.5, square=True, cbar=False, xticklabels=False, yticklabels=False, cmap=cmap, vmin=0, vmax=df.values.max())
        # ax.set_title(self._form_title(spec), fontsize=6)
        filename = self._form_filename(spec.source_site, spec.study)
        plt.savefig(join(self.subpath, f'{filename}.svg'), pad_inches=0, bbox_inches='tight')
        plt.close()
        if self.verbose:
            print(f'Wrote {filename}.svg')

    def _form_cmap(self, spec: BoxDiagramSpecification) -> ListedColormap:
        color_list = [(1,1,1)] + [None] * 20
        for i in spec.number_boxes_by_stratum.keys():
            stratum_identifier = str(i)
            color_list[int(stratum_identifier)] = self.color_lookup.lookup(spec.study, stratum_identifier)
        return ListedColormap(list(filter(lambda v: v is not None, color_list)))

    def _form_uniform_rows(self, spec: BoxDiagramSpecification) -> list[tuple[int, ...]]:
        def _expand_list(stratum_identifier, size) -> list:
            return [int(stratum_identifier)] * size
        number_boxes_by_stratum = self._apply_study_patches(spec.study, spec.number_boxes_by_stratum)
        cellvalues = list(chain(*map(lambda args: _expand_list(*args), number_boxes_by_stratum.items())))
        return list(zip_longest(*(iter(cellvalues),) * spec.width_count, fillvalue=0))  # type: ignore

    def _form_title(self, spec: BoxDiagramSpecification) -> str:
        site_name = self.site_labels.lookup(spec.study, spec.source_site)
        return site_name + '\n' + self.abbreviate_int(spec.total_cells)

    def _form_filename(self, source: str, study: str) -> str:
        filename = re.sub(' ', '_', f'{source} {study}').lower()
        filename = re.sub('[^a-zA-Z0-9]', '', filename)
        return filename

    def _apply_study_patches(self, study: str, number_boxes_by_stratum: OrderedDict[str, int]) -> OrderedDict[str, int]:
        if study == 'Brain met IMC':
            def key(i):
                k = int(i)
                if k in [2, 3]:
                    return 2 + 3 - k
                return k
            keys = sorted(number_boxes_by_stratum, key=key)
            new = OrderedDict()
            for k in keys:
                new[k] = number_boxes_by_stratum[k]
            number_boxes_by_stratum = new
        return number_boxes_by_stratum

    @staticmethod
    def abbreviate_int(i: int | float) -> str:
        i = int(i)
        scale = log10(i)
        if scale >= 6:
            return str(round((i / pow(10, 6)))) + 'm'
        if scale >= 3:
            return str(round((i / pow(10, 3)))) + 'k'
        return str(i)


if __name__=='__main__':
    import sys
    verbose=False
    if len(sys.argv) > 1:
        if sys.argv[1] == '--verbose':
            verbose = True
    figure = SampleBoxesOverview()
    figure.create(verbose=verbose)
