"""GNN importance fractions figure generation."""

from os.path import exists
from pickle import load as pickle_load
from pickle import dump as pickle_dump
from typing import Literal
from typing import Iterable
from typing import cast
from typing import Any
from typing import TYPE_CHECKING
from json import loads as json_loads
from glob import glob
import re
from enum import Enum

import numpy as np
from numpy.typing import NDArray
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

from accessors import DataAccessor  # type: ignore

if TYPE_CHECKING:
    from matplotlib.figure import Figure

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
            print('Retrieving count data to support plot.')
            f = self.get_progress_bar_format()
            self.df_phenotypes_original = tuple(
                (str(phenotype), self.get_access().counts(phenotype).astype(int))
                for phenotype in tqdm(levels, total=N, bar_format=f)
            )
            with open(pickle_file, 'wb') as file:
                pickle_dump(self.df_phenotypes_original, file)

    def retrieve(self, cohorts: set[int], phenotypes: list[str], plugin: GNNModel) -> DataFrame:
        multiindex = MultiIndex.from_product([phenotypes, ['p_value', 'important_fraction']])
        df = DataFrame(columns=multiindex)
        self.reset_phenotype_counts(df)
        print(f'Retrieving important cell fractions ({plugin}).')
        N = len(self.get_df_phenotypes())
        pickle_file = self.get_pickle_file('importance', plugin=plugin)
        f = self.get_progress_bar_format()
        if exists(pickle_file):
            with open(pickle_file, 'rb') as file:
                important_proportions = pickle_load(file)
                print(f'Loaded from cache: {pickle_file}')
        else:
            important_proportions = {
                phenotype: self.get_access().important(phenotype, plugin=plugin)
                for phenotype, _ in tqdm(self.get_df_phenotypes(), total=N, bar_format=f)
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

    def _test_one_case(
        self,
        phenotype: str,
        _sample: str,
        count_phenotype: int,
        count_both,
        total: int,
        df: DataFrame,
    ) -> None:
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

    def _get_omittable_samples(
        self,
        important_proportions: dict[str, dict[str, float]],
    ) -> set[str]:
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


@define
class SubplotGenerator:
    title_location: str
    norm: Normalize
    disc_scale_factor: float = 200

    def plot(
        self,
        df: DataFrame,
        ax: Axes,
        title: str,
        label_vertically: bool,
        label_horizontally: bool,
    ) -> None:
        """Plot the important fractions and p-values for the given dataframe."""
        s_cohort = df['cohort']
        cohorts = s_cohort.unique()

        df = self._prepare_dataframe(df, cohorts)
        df_p_value_normalized, df_p_important = self._get_p_values(df)
        X, Y = self._create_meshgrid(df_p_important)

        c, s = self._flatten_data(df_p_important, df_p_value_normalized)

        self._plot_scatter(ax, X, Y, c, s)
        self._set_axes(ax, df_p_important)
        self._add_labels(ax,
                         s_cohort,
                         cohorts,
                         df_p_important,
                         label_vertically,
                         label_horizontally,
                         )
        self._set_title(ax, title)

    def _prepare_dataframe(self, df: DataFrame, cohorts: NDArray[Any]) -> DataFrame:
        """Prepare the dataframe for plotting by adding NaN rows between cohorts."""
        dfs = []
        for i, cohort in enumerate(cohorts):
            df_cohort = df[df['cohort'] == cohort]
            if i != 0:
                df_cohort = concat([DataFrame([np.repeat(np.nan, df_cohort.shape[1])],
                                              columns=df_cohort.columns,
                                              index=[''],
                                              ), df_cohort])
            dfs.append(df_cohort)
        df = concat(dfs)
        df.index.name = 'Specimen by cohort'
        df.drop('cohort', axis=1, level=0, inplace=True)

        return df.transpose().astype(float)

    def _get_p_values(self, df: DataFrame) -> DataFrame:
        """Get, clip, and normalize the p-values and important fractions from the dataframe."""
        df_p_value = df.xs('p_value', axis=0, level=1)
        df_p_important = df.xs('important_fraction', axis=0, level=1)

        df_p_value_clipped = df_p_value.clip(upper=0.05)
        df_p_value_normalized = 1 - df_p_value_clipped / 0.05

        return df_p_value_normalized, df_p_important

    def _create_meshgrid(self, df_p_important: DataFrame) -> tuple[NDArray[Any], NDArray[Any]]:
        """Create a meshgrid for the cell centers."""
        x = np.arange(df_p_important.shape[1]) + 0.5
        y = np.arange(df_p_important.shape[0]) + 0.5
        X, Y = np.meshgrid(x, y)
        return X, Y

    def _flatten_data(self,
                      df_p_important: DataFrame,
                      df_p_value_normalized: DataFrame,
                      ) -> tuple[NDArray[Any], NDArray[Any]]:
        """Flatten the data and the sizes and scale up the latter for visibility."""
        c = df_p_important.values.flatten()
        s = df_p_value_normalized.values.flatten() * self.disc_scale_factor
        return c, s

    def _plot_scatter(self,
                      ax: Axes,
                      X: NDArray[Any],
                      Y: NDArray[Any],
                      c: NDArray[Any],
                      s: NDArray[Any],
                      ) -> None:
        ax.scatter(X.flatten(),
                   Y.flatten(),
                   c=c,
                   s=s,
                   cmap=self._get_main_heatmap_colormap(),
                   norm=self.norm,
                   edgecolor='black',
                   )
        ax.set_aspect('equal')
        # ax.set_aspect((df_p_important.shape[0] + len(cohorts) - 1) / df_p_important.shape[1]*1.5)

    def _set_axes(self, ax: Axes, df_p_important: DataFrame) -> None:
        """Invert the y-axis and turn off x-tick labels."""
        ax.set_xlim(0, df_p_important.shape[1])
        ax.set_ylim(0, df_p_important.shape[0])
        ax.invert_yaxis()

        ax.tick_params(axis='x', length=0)

    def _add_labels(self,
                    ax: Axes,
                    s_cohort: Series,
                    cohorts: NDArray[Any],
                    df_p_important: DataFrame,
                    label_vertically: bool,
                    label_horizontally: bool,
                    ) -> None:
        """Add text annotations to the plot to label the cohort and phenotype."""
        if label_horizontally:
            start = 0
            for cohort in cohorts:
                ax.text(start, -0.25, cohort if isinstance(cohort, str) else f'Cohort {cohort}',
                        ha='left', va='center')
                start += s_cohort[s_cohort == cohort].shape[0] + 1  # plus the NaN row
        ax.set_xticks([])

        if label_vertically:
            ax.set_yticks(np.arange(df_p_important.shape[0]) + 0.5)
            ax.set_yticklabels(df_p_important.index, rotation=0)
        else:
            ax.set_yticks([])
        ax.yaxis.set_ticks_position('none')

    def _set_title(self, ax: Axes, title: str) -> None:
        if self.title_location == 'bottom':
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


class PlotGenerator:
    """Generate a importance fractions plot."""

    def __init__(
        self,
        db_config_file_path: str,
        study_name: str,
        phenotypes: list[str],
        plugins: list[str],
        figure_size: tuple[int, int],
        orientation: str | None,
    ) -> None:
        """Instantiate the importance fractions plot generator."""
        self.db_config_file_path = db_config_file_path
        self.specification = PlotSpecification(
            study_name,
            phenotypes,
            phenotypes,
            None,  # TODO: Get cohorts from database
            plugins,
            figure_size,
            'horizontal' if (orientation is None) else orientation,
        )

    def generate_plot(self) -> 'Figure':
        self._check_viability()
        dfs = self._retrieve_data()
        self._gather_subplot_cases(dfs)
        return self._generate_subplots(dfs)

    def _check_viability(self) -> None:
        if len(self.specification.plugins) != 2:
            raise ValueError('Currently plot generation requires 2 plugins worth of run data.')

    def _retrieve_data(self) -> tuple[DataFrame, ...]:
        dfs = PlotDataRetriever(self.host).retrieve_data(self.specification)
        dfs = self._transfer_cohort_labels(dfs, self.specification)
        return dfs

    def _transfer_cohort_labels(
        self,
        dfs: tuple[DataFrame, ...],
        specification: PlotSpecification,
    ) -> tuple[DataFrame, ...]:
        if specification.cohorts is not None:
            cohort_map = {c.index_int: c.label for c in specification.cohorts}
            dfs = tuple(df.copy() for df in dfs)
            for _, df in enumerate(dfs):
                df['cohort'] = df['cohort'].map(cohort_map)
        dfs = tuple(df.sort_values('cohort').sort_index() for df in dfs)
        return dfs

    def _gather_subplot_cases(
        self,
        dfs: tuple[DataFrame, ...],
    ) -> tuple[SubplotSpecification, Indicators, Iterable[tuple[DataFrame, GNNModel]]]:
        subplot_specification = derive_subplot_specification(self.specification)
        indicators = label_indicators(self.specification).get_label_subplot_indicators()
        return subplot_specification, indicators, zip(dfs, self.specification.plugins)

    def _generate_subplots(self, dfs: tuple[DataFrame, ...]) -> 'Figure':
        plt.rcParams['font.size'] = 14
        norm = self._generate_normalization(dfs)
        subplot_specification, indicators, cases = self._gather_subplot_cases(dfs)
        fig, axs = plt.subplots(
            *subplot_specification.grid_dimensions,
            figsize=self.specification.figure_size,
        )
        title_location = subplot_specification.title_location
        subplot_generator = SubplotGenerator(title_location, norm)
        for i, ((df, plugin), ax) in enumerate(zip(cases, axs)):
            subplot_generator.plot(df, ax, plugin, indicators[0][i], indicators[1][i])
        fig.suptitle(self.specification.study)
        plt.tight_layout()
        return fig

    @staticmethod
    def _generate_normalization(dfs: tuple[DataFrame, ...]) -> Normalize:
        dfs_values_only = tuple(df.drop('cohort', axis=1, level=0) for df in dfs)
        vmin = min(df.min().min() for df in dfs_values_only)
        vmax = max(df.max().max() for df in dfs_values_only)
        return Normalize(vmin=vmin, vmax=vmax)
