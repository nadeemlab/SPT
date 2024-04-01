from os.path import join
from argparse import ArgumentParser
from argparse import Namespace
from itertools import chain
from typing import NamedTuple
from typing import Literal
from typing import cast

import numpy as np
from pandas import DataFrame
from pandas import MultiIndex
from pandas import concat
from pandas import Series
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import SymLogNorm
from scipy.stats import fisher_exact  # type: ignore
from attr import define

from accessors import DataAccessor

GNNModel = Literal['cg-gnn', 'graph-transformer']


class Cohort(NamedTuple):
    index_int: int
    label: str


class PlotSpecification(NamedTuple):
    study: str
    phenotypes: tuple[str, ...]
    attribute_order: tuple[str, ...]
    cohorts: tuple[Cohort, ...]
    plugins: tuple[GNNModel, ...]
    figure_size: tuple[float, float]
    orientation: Literal['horizontal', 'vertical']


def plot_specifications() -> tuple[PlotSpecification, ...]:
    miscellaneous = [
        'Tumor',
        'Adipocyte or Langerhans cell',
        'Nerve',
        'B cell',
        'Natural killer cell',
    ]
    t_cells = [
        'Natural killer T cell',
        'CD4+/CD8+ T cell',
        'CD4+ natural killer T cell',
        'CD4+ regulatory T cell',
        'CD4+ T cell',
        'CD8+ natural killer T cell',
        'CD8+ regulatory T cell',
        'CD8+ T cell',
        'Double negative regulatory T cell',
        'T cell/null phenotype',
    ]
    macrophages = [
        'CD163+MHCII- macrophage',
        'CD163+MHCII+ macrophage',
        'CD68+MHCII- macrophage',
        'CD68+MHCII+ macrophage',
        'Other macrophage/monocyte CD14+',
        'Other macrophage/monocyte CD4+',
    ]

    most_interesting = [
        'Tumor',
        'Adipocyte or Langerhans cell',
        'Natural killer cell',
        'CD4+ T cell',
    ]
    less_activity = [
        'Nerve',
        'B cell',
    ]
    t_cell_types_selected = [
        'CD4+/CD8+ T cell',
        'CD4+ regulatory T cell',
        'CD8+ natural killer T cell',
        'CD8+ regulatory T cell',
        'CD8+ T cell',
        'Double negative regulatory T cell',
        'T cell/null phenotype',
    ]
    no_activity = [
        'Natural killer T cell',
        'CD4+ natural killer T cell',
    ]
    phenotypes_urothelial = [
        'Tumor',
        'CD4- CD8- T cell',
        'T cytotoxic cell',
        'T helper cell',
        'Macrophage',
        'intratumoral CD3+ LAG3+',
        'Regulatory T cell',
    ]
    return (
        PlotSpecification(
            study = 'Melanoma intralesional IL2',
            phenotypes = tuple(miscellaneous + t_cells + macrophages),
            attribute_order = tuple(chain(*
                [most_interesting, less_activity, t_cell_types_selected, no_activity, ['cohort']]
            )),
            cohorts = (
                Cohort(index_int=1, label='Non-responder'),
                Cohort(index_int=3, label='Responder'),
            ),
            plugins = ('cg-gnn', 'graph-transformer'),
            figure_size = (11, 8),
            orientation = 'horizontal',
        ),
        PlotSpecification(
            study = 'Urothelial ICI',
            phenotypes = tuple(phenotypes_urothelial),
            attribute_order = tuple(phenotypes_urothelial + ['cohort']),
            cohorts = (
                Cohort(index_int=1, label='Responder'),
                Cohort(index_int=2, label='Non-responder'),
            ),
            plugins = ('cg-gnn', 'graph-transformer'),
            figure_size = (14, 5),
            orientation = 'vertical',
        )
    )


def plot_scatter_heatmap(df: DataFrame,
                         ax: plt.Axes,
                         label_phenotypes: bool,
                         label_cohorts: bool,
                         cmap: mcolors.ListedColormap,
                         norm: mcolors.Normalize | None = None,
                         title: str | None = None,
                         title_side: str = 'bottom',
                         s_factor: float = 200,
                         ):
    df = df.sort_values('cohort')
    df = df.sort_index()

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

    # Transpose the DataFrame
    df = df.transpose().astype(float)

    # Separate the p_value and p_important
    df_p_value = df.xs('p_value', axis=0, level=1)
    df_p_important = df.xs('important_fraction', axis=0, level=1)

    # Clip the p_value to the range [0, 0.1] and normalize it to the range [0, 1]
    df_p_value_clipped = df_p_value.clip(upper=0.05)
    df_p_value_normalized = 1 - df_p_value_clipped / 0.05

    # Use SymLogNorm for the colormap
    if norm is None:
        norm = mcolors.SymLogNorm(linthresh=0.001, linscale=0.001,
                                  vmin=df_p_important.min().min(),
                                  vmax=df_p_important.max().max(),
                                  )

    # Create a meshgrid for the cell centers
    x = np.arange(df_p_important.shape[1]) + 0.5
    y = np.arange(df_p_important.shape[0]) + 0.5
    X, Y = np.meshgrid(x, y)

    # Flatten the data and the sizes
    c = df_p_important.values.flatten()
    s = df_p_value_normalized.values.flatten() * s_factor  # Scale up the sizes for visibility

    # Plot the scatter plot
    ax.scatter(X.flatten(), Y.flatten(), c=c, s=s, cmap=cmap, norm=norm, edgecolor='black')
    ax.set_aspect('equal')
    # ax.set_aspect((df_p_important.shape[0] + len(cohorts) - 1) / df_p_important.shape[1]*1.5)

    # Invert the y-axis to match the heatmap orientation
    ax.set_xlim(0, df_p_important.shape[1])
    ax.set_ylim(0, df_p_important.shape[0])
    ax.invert_yaxis()

    # Turn off x-tick labels
    ax.tick_params(axis='x', length=0)

    # Add text annotations to label the cohorts
    if label_cohorts:
        start = 0
        for cohort in cohorts:
            df_cohort = s_cohort[s_cohort == cohort]
            ax.text(start, -0.25, cohort if isinstance(cohort, str) else f'Cohort {cohort}',
                    ha='left', va='center')
            start += df_cohort.shape[0] + 1  # Add 1 to account for the NaN row
    ax.set_xticks([])

    # Add the phenotype labels
    if label_phenotypes:
        ax.set_yticks(np.arange(df_p_important.shape[0]) + 0.5)
        ax.set_yticklabels(df_p_important.index, rotation=0)
    else:
        ax.set_yticks([])
    ax.yaxis.set_ticks_position('none')

    if title is not None:
        if title_side == 'bottom':
            ax.set_xlabel(title)
        else:
            ax.text(1.021, .5, title, rotation=-90, ha='right', va='center', transform=ax.transAxes)


# Create a colormap that varies in color
colors = ["white", "red"]
cmap = mcolors.LinearSegmentedColormap.from_list("", colors)
cmap.set_under(color='white')


def plot_2_heatmaps(dfs: tuple[DataFrame, DataFrame],
                    model_names: tuple[GNNModel, GNNModel],
                    study_name: str,
                    output_directory: str | None = None,
                    cohort_map: dict[int, str] | None = None,
                    concat_axis: str = 'horizontal',
                    figsize: tuple[float, float] = (16, 6),
                    ):

    dfs_values_only = tuple(df.drop('cohort', axis=1, level=0) for df in dfs)
    vmin = min(df.min().min() for df in dfs_values_only)
    vmax = max(df.max().max() for df in dfs_values_only)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    if concat_axis == 'horizontal':
        fig, axs = plt.subplots(1, 2, figsize=figsize)
        title_side = 'bottom'
        label_phenotypes_2nd = False
        label_cohorts_2nd = True
    else:  # concat_axis == 'vertical'
        fig, axs = plt.subplots(2, 1, figsize=figsize)
        title_side = 'side'
        label_phenotypes_2nd = True
        label_cohorts_2nd = False

    if cohort_map is not None:
        dfs = tuple(df.copy() for df in dfs)
        for i, df in enumerate(dfs):
            df['cohort'] = df['cohort'].map(cohort_map)

    plot_scatter_heatmap(dfs[0], axs[0], True, True, cmap, norm,
                         title=model_names[0], title_side=title_side)
    plot_scatter_heatmap(dfs[1], axs[1], label_phenotypes_2nd, label_cohorts_2nd, cmap, norm,
                         title=model_names[1], title_side=title_side)

    # Adjust the model/study labels
    fig.suptitle(study_name)

    # Create a ScalarMappable object with the same colormap and normalization as the scatter plots
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # Add the colorbar to the figure
    # fig.subplots_adjust(left=0.2)  # Increase left margin
    cbar_ax = fig.add_axes([0.3, 0, 0.4, 0.01])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal', fraction=0.05)

    plt.tight_layout()
    if output_directory is not None:
        plt.savefig(join(output_directory, f'{study_name}.svg'))
    plt.show()


def plot_2x2_heatmaps(df_model1: tuple[DataFrame, DataFrame], df_model2: tuple[DataFrame, DataFrame], model_names: tuple[str, str], study_names: tuple[str, str], figsize: tuple[float, float] = (16, 6)):
    fig, axs = plt.subplots(2, 2, figsize=figsize)

    # dfs = df_model1 + df_model2
    # vmin = min(df.drop('cohort', axis=1, level=0).xs(
    #     'p_important', axis=1, level=1).min().min() for df in dfs)
    # vmax = max(df.drop('cohort', axis=1, level=0).xs(
    #     'p_important', axis=1, level=1).max().max() for df in dfs)
    vmin = 0
    vmax = 1
    # norm = SymLogNorm(linthresh=0.001, linscale=0.001, vmin=vmin, vmax=vmax)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    plot_scatter_heatmap(df_model1[0], axs[0, 0], True, True, cmap, norm)
    plot_scatter_heatmap(df_model2[0], axs[0, 1], False, True, cmap, norm)
    plot_scatter_heatmap(df_model1[1], axs[1, 0], True, True, cmap, norm)
    plot_scatter_heatmap(df_model2[1], axs[1, 1], False, True, cmap, norm)

    # Adjust the model/study labels
    fig.text(0.5, 1.15, model_names[0], ha='center', va='center', transform=axs[0, 0].transAxes)
    fig.text(0.5, 1.15, model_names[1], ha='center', va='center', transform=axs[0, 1].transAxes)
    fig.text(-0.2, 0.5, study_names[0], ha='center', va='center',
             rotation='vertical', transform=axs[0, 0].transAxes)
    fig.text(-0.2, 0.5, study_names[1], ha='center', va='center',
             rotation='vertical', transform=axs[1, 0].transAxes)

    # Create a ScalarMappable object with the same colormap and normalization as the scatter plots
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # # Adjust the position of the subplots to make room for the colorbar
    # fig.subplots_adjust(bottom=0.1)

    # Create a ScalarMappable object with the same colormap and normalization as the scatter plots
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # Add the colorbar to the figure
    cbar_ax = fig.add_axes([0.15, 0.2, 0.7, 0.01])  # [left, bottom, width, height]
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal', fraction=0.05)

    plt.tight_layout()
    plt.show()


def plot_heatmap(df: DataFrame, model_name: str, study_name: str, figsize: tuple[float, float] = (16, 6)):
    fig, axs = plt.subplots(1, 1, figsize=figsize)
    df_values_only = df.drop('cohort', axis=1, level=0).xs('important_fraction', axis=1, level=1)
    norm = SymLogNorm(linthresh=0.001, linscale=0.001,
                      vmin=df_values_only.min().min(), vmax=df_values_only.max().max())
    plot_scatter_heatmap(df, axs, True, True, cmap, norm)

    plt.tight_layout()
    plt.show()


@define
class PlotGenerator:
    host: str
    output_directory: str 

    def generate_plots(self) -> None:
        for specification in plot_specifications():
            self._generate_plot(specification)

    def _generate_plot(self, specification: PlotSpecification) -> None:
        cohorts = set(c.index_int for c in specification.cohorts)
        plugins = specification.plugins
        plugins = cast(tuple[GNNModel, GNNModel], plugins)
        phenotypes = list(specification.phenotypes)
        attribute_order = self._get_attribute_order(specification)
        retriever = ImportanceFractionAndTestRetriever(self.host, specification.study)
        retriever.initialize()
        dfs_selected = tuple(
            retriever.retrieve(cohorts, phenotypes, plugin)[attribute_order] for plugin in plugins
        )
        plot_2_heatmaps(
            cast(tuple[DataFrame, DataFrame], dfs_selected),
            plugins,
            specification.study,
            output_directory=self.output_directory,
            cohort_map={c.index_int: c.label for c in specification.cohorts},
            concat_axis=specification.orientation,
            figsize=specification.figure_size
        )

    @staticmethod
    def _get_attribute_order(specification: PlotSpecification) -> list[str]:
        attribute_order = list(specification.attribute_order)
        if attribute_order is None:
            attribute_order = specification.phenotypes.copy()
        if 'cohort' not in attribute_order:
            attribute_order.append('cohort')
        return attribute_order

PhenotypeDataFrames = tuple[tuple[str, DataFrame], ...]

@define
class ImportanceFractionAndTestRetriever:
    host: str
    study: str
    access: DataAccessor | None = None
    count_important: int = 100
    df_phenotypes: PhenotypeDataFrames | None = None

    def initialize(self) -> None:
        self.access = DataAccessor(self.study, host=self.host)

    def get_access(self) -> DataAccessor:
        return cast(DataAccessor, self.access)

    def get_df_phenotypes(self) -> PhenotypeDataFrames:
        return cast(PhenotypeDataFrames, self.df_phenotypes)

    def retrieve(self, cohorts: set[int], phenotypes: list[str], plugin: str) -> DataFrame:
        df = DataFrame(columns=MultiIndex.from_product([phenotypes, ['p_value', 'important_fraction']]))
        self.df_phenotypes = tuple(
            (str(phenotype), self.get_access().counts(phenotype).astype(int))
            for phenotype in df.columns.get_level_values(0).unique()
        )
        important_proportions = {
            phenotype: self.get_access().important(phenotype, plugin=plugin)
            for phenotype, _ in self.get_df_phenotypes()
        }
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


def make_plots(args: Namespace):
    plt.rcParams['font.size'] = 14
    generator = PlotGenerator(args.host, args.output_directory)
    generator.generate_plots()


if __name__ == '__main__':
    parser = ArgumentParser()
    add = parser.add_argument
    add('host', type=str, help='SPT API endpoint host to query')
    add('output_directory', type=str, default='', help='Directory in which to save SVGs.')
    args = parser.parse_args()
    make_plots(args)
