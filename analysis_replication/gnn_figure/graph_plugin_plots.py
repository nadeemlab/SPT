from os.path import join
from os.path import exists
from pickle import load as pickle_load
from pickle import dump as pickle_dump
from argparse import ArgumentParser
from typing import Literal
from typing import Iterable
from typing import cast
from json import loads as json_loads
import sys
from glob import glob
import re
from enum import Enum

import numpy as np
from pandas import DataFrame
from pandas import MultiIndex
from pandas import concat
from pandas import Series
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize
from scipy.stats import fisher_exact  # type: ignore
from attr import define
from cattrs import structure as cattrs_structure
from tqdm import tqdm

sys.path.append('../')
from accessors import DataAccessor  # type: ignore

GNNModel = Literal['cg-gnn', 'graph-transformer']

@define
class Cohort:
    index_int: int
    label: str


class Orientation(Enum):
    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'


@define
class PlotSpecification:
    study: str
    phenotypes: tuple[str, ...]
    attribute_order: tuple[str, ...]
    cohorts: tuple[Cohort, ...]
    plugins: tuple[GNNModel, ...]
    figure_size: tuple[float, float]
    orientation: Orientation


def get_plot_specifications() -> tuple[PlotSpecification, ...]:
    filenames = glob('*.json')
    specifications = []
    for filename in filenames:
        with open(filename, 'rt', encoding='utf-8') as file:
            contents = file.read()
        specifications.append(cattrs_structure(json_loads(contents), PlotSpecification))
    return tuple(specifications)

def sanitized_study(study: str) -> str:
    return re.sub(' ', '_', study).lower()

PhenotypeDataFrames = tuple[tuple[str, DataFrame], ...]


@define
class ImportanceFractionAndTestRetriever:
    host: str
    study: str
    access: DataAccessor | None = None
    count_important: int = 100
    df_phenotypes: PhenotypeDataFrames | None = None
    df_phenotypes_original: PhenotypeDataFrames | None = None

    def initialize(self) -> None:
        self.access = DataAccessor(self.study, host=self.host)

    def get_access(self) -> DataAccessor:
        return cast(DataAccessor, self.access)

    def get_df_phenotypes(self) -> PhenotypeDataFrames:
        return cast(PhenotypeDataFrames, self.df_phenotypes)

    def get_sanitized_study(self) -> str:
        return sanitized_study(self.study)

    def get_pickle_file(self, data: Literal['counts', 'importance'], plugin: GNNModel | None = None) -> str:
        if data == 'counts':
            return f'{self.get_sanitized_study()}.df_phenotypes.pickle'
        if data == 'importance':
            return f'{self.get_sanitized_study()}.{plugin}.pickle'

    @staticmethod
    def get_progress_bar_format():
        return '{l_bar}{bar:30}{r_bar}{bar:-30b}'

    def reset_phenotype_counts(self, df: DataFrame) -> None:
        if self.df_phenotypes_original is None:
            self._retrieve_phenotype_counts(df)
        self.df_phenotypes = tuple(
            (phenotype, _df.copy())
            for phenotype, _df in cast(PhenotypeDataFrames, self.df_phenotypes_original)
        )

    def _retrieve_phenotype_counts(self, df: DataFrame) -> None:
        pickle_file = self.get_pickle_file('counts')
        if exists(pickle_file):
            with open(pickle_file, 'rb') as file:
                self.df_phenotypes_original = pickle_load(file)
                print(f'Loaded from cache: {pickle_file}')
        else:
            levels = df.columns.get_level_values(0).unique()
            N = len(levels)
            print(f'Retrieving count data to support plot.')
            self.df_phenotypes_original = tuple(
                (str(phenotype), self.get_access().counts(phenotype).astype(int))
                for phenotype, _ in zip(levels, tqdm(range(N), bar_format=self.get_progress_bar_format()))
            )
            with open(pickle_file, 'wb') as file:
                pickle_dump(self.df_phenotypes_original, file)

    def retrieve(self, cohorts: set[int], phenotypes: list[str], plugin: GNNModel) -> DataFrame:
        df = DataFrame(columns=MultiIndex.from_product([phenotypes, ['p_value', 'important_fraction']]))
        self.reset_phenotype_counts(df)
        print(f'Retrieving important cell fractions ({plugin}).')
        N = len(self.get_df_phenotypes())
        pickle_file = self.get_pickle_file('importance', plugin=plugin)
        if exists(pickle_file):
            with open(pickle_file, 'rb') as file:
                important_proportions = pickle_load(file)
                print(f'Loaded from cache: {pickle_file}')
        else:
            important_proportions = {
                phenotype: self.get_access().important(phenotype, plugin=plugin)
                for (phenotype, _), _ in zip(self.get_df_phenotypes(), tqdm(range(N), bar_format=self.get_progress_bar_format()))
            }
            with open(pickle_file, 'wb') as file:
                pickle_dump(important_proportions, file)
        omittable = self._get_omittable_samples(important_proportions)
        self._restrict_rows(cohorts, omittable)
        cohort_column = self._get_cohort_column().astype(int)
        self._restrict_columns()
        for phenotype, df_phenotype in self.get_df_phenotypes():
            important_proportion = important_proportions[phenotype]
            for _sample, row in df_phenotype.iterrows():
                sample = str(_sample)
                count_both = important_proportion[sample] * self.count_important / 100
                test = self._test_one_case
                test(phenotype, sample, row[phenotype], count_both, row['all cells'], df)
        self._get_cell_count()
        df['cohort'] = cohort_column
        return df

    def _test_one_case(self, phenotype: str, _sample: str, count_phenotype: int, count_both, total: int, df: DataFrame) -> None:
        sample = str(_sample)
        a = count_both
        b = self.count_important - count_both
        c = count_phenotype - count_both
        d = total - a - b - c
        _, p_value = fisher_exact([[a, b], [c, d]])
        df.loc[sample, (phenotype, 'important_fraction')] = count_both / self.count_important
        df.loc[sample, (phenotype, 'p_value')] = p_value

    def _restrict_rows(self, cohorts: set[int], omittable: set[str]) -> None:
        self.df_phenotypes = tuple(
            (
                phenotype,
                df[df['cohort'].isin(cohorts) & ~df.index.isin(omittable)]
                    .reset_index()
                    .sort_values(['cohort', 'sample'])
                    .set_index('sample'),
            )
            for phenotype, df in self.get_df_phenotypes()
        )

    def _restrict_columns(self) -> None:
        self.df_phenotypes = tuple(
            (
                phenotype,
                df.iloc[:, [
                    df.columns.get_loc('all cells'),
                    df.columns.get_indexer_for([phenotype])[0],
                ]],
            )
            for phenotype, df in self.get_df_phenotypes()
        )

    def _get_cohort_column(self) -> Series:
        cohort_column: Series | None = None
        for _, df_phenotype in self.get_df_phenotypes():
            if cohort_column is None:
                cohort_column = df_phenotype['cohort']
            else:
                assert (cohort_column == df_phenotype['cohort']).all()
        assert not cohort_column is None
        return cohort_column

    def _get_omittable_samples(self, important_proportions: dict[str, dict[str, float]]) -> set[str]:
        occurring = set(
            str(sample)
            for _, df in self.get_df_phenotypes()
            for _, sample in Series(df.index).items()
        )
        with_none = set(
            str(sample)
            for _, important_proportion in important_proportions.items()
            for sample, value in important_proportion.items()
            if value is None
        )
        return occurring.intersection(with_none)

    def _get_cell_count(self) -> Series:
        cell_count = None
        for _, df in self.get_df_phenotypes():
            if cell_count is None:
                cell_count = df['all cells']
            else:
                assert (cell_count == df['all cells']).all()
        assert not cell_count is None
        return cell_count


@define
class PlotDataRetriever:
    host: str

    def retrieve_data(self, specification: PlotSpecification) -> tuple[DataFrame, ...]:
        cohorts = set(c.index_int for c in specification.cohorts)
        plugins = cast(tuple[GNNModel, GNNModel], specification.plugins)
        phenotypes = list(specification.phenotypes)
        attribute_order = self._get_attribute_order(specification)
        retriever = ImportanceFractionAndTestRetriever(self.host, specification.study)
        retriever.initialize()
        return tuple(
            retriever.retrieve(cohorts, phenotypes, plugin)[attribute_order] for plugin in plugins
        )

    @staticmethod
    def _get_attribute_order(specification: PlotSpecification) -> list[str]:
        attribute_order = list(specification.attribute_order)
        if attribute_order is None:
            attribute_order = specification.phenotypes.copy()
        if 'cohort' not in attribute_order:
            attribute_order.append('cohort')
        return attribute_order


class SubplotGenerator:
    @classmethod
    def plot(
        cls,
        df: DataFrame,
        ax: Axes,
        title: str,
        title_side: str,
        label_vertically: bool,
        label_horizontally: bool,
        norm: Normalize,
        s_factor: float = 200,
    ) -> None:
        # Extract the 'cohort' column
        s_cohort = df['cohort']

        # Add a row of NaN values between each cohort
        dfs = []
        cohorts = df['cohort'].unique()
        for i, cohort in enumerate(cohorts):
            df_cohort = df[df['cohort'] == cohort]
            # Skip adding a NaN row before the first cohort
            if i != 0:
                df_cohort = concat([DataFrame([np.repeat(np.nan, df_cohort.shape[1])],
                                columns=df_cohort.columns, index=['']), df_cohort])
            dfs.append(df_cohort)
        df = concat(dfs)
        df.index.name = 'Specimen by cohort'
        df.drop('cohort', axis=1, level=0, inplace=True)

        df = df.transpose().astype(float)

        df_p_value = df.xs('p_value', axis=0, level=1)
        df_p_important = df.xs('important_fraction', axis=0, level=1)

        # Clip the p_value to the range [0, 0.1] and normalize it to the range [0, 1]
        df_p_value_clipped = df_p_value.clip(upper=0.05)
        df_p_value_normalized = 1 - df_p_value_clipped / 0.05

        # Create a meshgrid for the cell centers
        x = np.arange(df_p_important.shape[1]) + 0.5
        y = np.arange(df_p_important.shape[0]) + 0.5
        X, Y = np.meshgrid(x, y)

        # Flatten the data and the sizes
        c = df_p_important.values.flatten()
        s = df_p_value_normalized.values.flatten() * s_factor  # Scale up the sizes for visibility

        ax.scatter(X.flatten(), Y.flatten(), c=c, s=s, cmap=cls._get_main_heatmap_colormap(), norm=norm, edgecolor='black')
        ax.set_aspect('equal')
        # ax.set_aspect((df_p_important.shape[0] + len(cohorts) - 1) / df_p_important.shape[1]*1.5)

        # Invert the y-axis to match the heatmap orientation
        ax.set_xlim(0, df_p_important.shape[1])
        ax.set_ylim(0, df_p_important.shape[0])
        ax.invert_yaxis()

        # Turn off x-tick labels
        ax.tick_params(axis='x', length=0)

        # Add text annotations to label the cohorts
        if label_horizontally:
            start = 0
            for cohort in cohorts:
                df_cohort = s_cohort[s_cohort == cohort]
                ax.text(start, -0.25, cohort if isinstance(cohort, str) else f'Cohort {cohort}',
                        ha='left', va='center')
                start += df_cohort.shape[0] + 1  # Add 1 to account for the NaN row
        ax.set_xticks([])

        # Add the phenotype labels
        if label_vertically:
            ax.set_yticks(np.arange(df_p_important.shape[0]) + 0.5)
            ax.set_yticklabels(df_p_important.index, rotation=0)
        else:
            ax.set_yticks([])
        ax.yaxis.set_ticks_position('none')

        if title_side == 'bottom':
            ax.set_xlabel(title)
        else:
            ax.text(1.021, .5, title, rotation=-90, ha='right', va='center', transform=ax.transAxes)

    @staticmethod
    def _get_main_heatmap_colormap():
        colors = ['white', 'red']
        cmap = mcolors.LinearSegmentedColormap.from_list('', colors)
        cmap.set_under(color='white')
        return cmap


@define
class SubplotSpecification:
    grid_dimensions: tuple[int, int]
    title_location: Literal['bottom', 'side']


def derive_subplot_specification(specification: PlotSpecification) -> SubplotSpecification:
    size = len(specification.plugins)
    specs = {
        Orientation.HORIZONTAL: SubplotSpecification((1, size), 'bottom'),
        Orientation.VERTICAL: SubplotSpecification((size, 1), 'side'),
    }
    return specs[specification.orientation]


Indicator = tuple[bool, ...]
Indicators = tuple[Indicator, Indicator]


@define
class LabelIndicators:
    size: int
    baseline_orientation: Orientation

    def label_indicator_first(self) -> Indicator:
        return tuple([True] + list(map(lambda _: False, range(1, self.size))))

    def label_indicator_all(self) -> Indicator:
        return tuple(map(lambda _: True, range(self.size)))

    def get_label_subplot_indicators(self) -> Indicators:
        indicators = (
            self.label_indicator_first(),
            self.label_indicator_all(),
        )
        if self.baseline_orientation == Orientation.HORIZONTAL:
            return indicators
        if self.baseline_orientation == Orientation.VERTICAL:
            return cast(Indicators, tuple(reversed(indicators)))


def label_indicators(spec: PlotSpecification) -> LabelIndicators:
    return LabelIndicators(len(spec.plugins), spec.orientation)


@define
class PlotGenerator:
    host: str
    output_directory: str 
    show_also: bool
    current_specification: PlotSpecification | None = None

    def get_specification(self) -> PlotSpecification:
        return cast(PlotSpecification, self.current_specification)

    def generate_plots(self) -> None:
        for specification in get_plot_specifications():
            self.current_specification = specification
            self._check_viability()
            dfs = self._retrieve_data()
            self._gather_subplot_cases(dfs)
            self._generate_plot(dfs)
            self._export()

    def _check_viability(self) -> None:
        if len(self.get_specification().plugins) != 2:
            raise ValueError('Currently plot generation requires 2 plugins worth of run data.')

    def _retrieve_data(self) -> tuple[DataFrame, ...]:
        dfs = PlotDataRetriever(self.host).retrieve_data(self.get_specification())
        dfs = self._update_cohorts(dfs, self.get_specification())
        return dfs

    def _update_cohorts(
        self,
        dfs: tuple[DataFrame, ...],
        specification: PlotSpecification,
    ) -> tuple[DataFrame, ...]:
        if specification.cohorts is not None:
            cohort_map={c.index_int: c.label for c in specification.cohorts}
            dfs = tuple(df.copy() for df in dfs)
            for _, df in enumerate(dfs):
                df['cohort'] = df['cohort'].map(cohort_map)
        dfs = tuple(df.sort_values('cohort').sort_index() for df in dfs)
        return dfs

    def _gather_subplot_cases(
        self,
        dfs: tuple[DataFrame, ...],
    ) -> tuple[SubplotSpecification, Indicators, Iterable[tuple[DataFrame, GNNModel]]]:
        subplot_specification = derive_subplot_specification(self.get_specification())
        indicators = label_indicators(self.get_specification()).get_label_subplot_indicators()
        return subplot_specification, indicators, zip(dfs, self.get_specification().plugins)

    def _generate_plot(self, dfs: tuple[DataFrame, ...]) -> None:
        plt.rcParams['font.size'] = 14
        norm = self._generate_normalization(dfs)
        subplot_specification, indicators, cases = self._gather_subplot_cases(dfs)
        fig, axs = plt.subplots(
            *subplot_specification.grid_dimensions,
            figsize=self.get_specification().figure_size,
        )
        title_location = subplot_specification.title_location
        for i, ((df, plugin), ax) in enumerate(zip(cases, axs)):
            SubplotGenerator.plot(
                df, ax, plugin, title_location, indicators[0][i], indicators[1][i], norm,
            )
        fig.suptitle(self.get_specification().study)
        plt.tight_layout()

    def _export(self) -> None:
        if self.output_directory is not None:
            plt.savefig(join(self.output_directory, f'{sanitized_study(self.get_specification().study)}.svg'))
        if self.show_also:
            plt.show()

    @staticmethod
    def _generate_normalization(dfs: tuple[DataFrame, ...]) -> Normalize:
        dfs_values_only = tuple(df.drop('cohort', axis=1, level=0) for df in dfs)
        vmin = min(df.min().min() for df in dfs_values_only)
        vmax = max(df.max().max() for df in dfs_values_only)
        return Normalize(vmin=vmin, vmax=vmax)


if __name__ == '__main__':
    parser = ArgumentParser()
    add = parser.add_argument
    add('host', nargs='?', type=str, default='http://oncopathtk.org/api', help='SPT API host.')
    add('output_directory', nargs='?', type=str, default='.', help='Directory in which to save SVGs.')
    add('--show', action='store_true', help='If set, will display figures in addition to saving.')
    args = parser.parse_args()
    generator = PlotGenerator(args.host, args.output_directory, args.show)
    generator.generate_plots()
