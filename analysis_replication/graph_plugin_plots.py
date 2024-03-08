import os
from argparse import ArgumentParser

import numpy as np
from pandas import DataFrame, MultiIndex, concat
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import SymLogNorm
from scipy.stats import fisher_exact

from accessors import DataAccessor


def df_study(study: str, host: str, cohorts: set[int], phenotypes: list[str], plugin_name: str = 'cg-gnn'):
    access = DataAccessor(study, host=host)
    df = DataFrame(columns=MultiIndex.from_product([phenotypes, ['p_value', 'p_important']]))
    specimens_to_delete: set[str] = set()
    s_cohort = None
    for phenotype in df.columns.get_level_values(0).unique():
        df_phenotype = access.counts(phenotype).astype(int)
        df_phenotype = df_phenotype[df_phenotype['cohort'].isin(cohorts)]

        df_phenotype.reset_index(inplace=True)
        df_phenotype.sort_values(['cohort', 'sample'], inplace=True)
        df_phenotype.set_index('sample', inplace=True)

        if s_cohort is None:
            s_cohort = df_phenotype['cohort']
        df_phenotype = df_phenotype.iloc[:, [
            df_phenotype.columns.get_loc('all cells'),
            df_phenotype.columns.get_indexer_for([phenotype])[0],
        ]]
        if df.shape[0] == 0:
            df['Cell count'] = df_phenotype['all cells']
        else:
            assert (df['Cell count'] == df_phenotype.drop(specimens_to_delete)['all cells']).all()
            specimens_to_delete = set()
        important_proportion = access.important(phenotype,
                                                plugin=plugin_name,
                                                # datetime_of_run='2023-12-31 00:00:00',
                                                # plugin_version='0',
                                                # cohort_stratifier='',
                                                )

        for specimen, row in df_phenotype.iterrows():
            if important_proportion[specimen] is None:
                specimens_to_delete.add(specimen)
                continue
            n_cells_of_this_phenotype = row[phenotype]
            n_cells_total = row['all cells']
            n_important_cells_of_this_phenotype = important_proportion[specimen]
            n_important_cells_total = 100
            odd_ratio, p_value = fisher_exact([
                [n_important_cells_of_this_phenotype,
                 n_important_cells_total - n_important_cells_of_this_phenotype],
                [n_cells_of_this_phenotype - n_important_cells_of_this_phenotype,
                 n_cells_total - n_cells_of_this_phenotype - n_important_cells_total + n_important_cells_of_this_phenotype],
            ])
            df.loc[specimen, (phenotype, 'p_important')] = n_important_cells_of_this_phenotype / 100
            df.loc[specimen, (phenotype, 'p_value')] = p_value
        df = df[~df.index.isin(specimens_to_delete)]
    df['cohort'] = s_cohort.astype(int)
    return df


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
    df.sort_values(['cohort', df.index.name], inplace=True)

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
    df_p_important = df.xs('p_important', axis=0, level=1)

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
                    model_names: tuple[str, str],
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
        plt.savefig(os.path.join(output_directory, f'{study_name}.svg'))
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
    df_values_only = df.drop('cohort', axis=1, level=0).xs('p_important', axis=1, level=1)
    norm = SymLogNorm(linthresh=0.001, linscale=0.001,
                      vmin=df_values_only.min().min(), vmax=df_values_only.max().max())
    plot_scatter_heatmap(df, axs, True, True, cmap, norm)

    plt.tight_layout()
    plt.show()


def generate_study_heatmaps(study_name: str,
                            host: str,
                            cohorts: set[int],
                            phenotypes: list[str],
                            figsize: tuple[int, int],
                            output_directory: str | None = None,
                            channel_order: list[str] | None = None,
                            cohort_map: dict[int, str] | None = None,
                            concat_axis: str = 'horizontal',
                            plugin_names: tuple[str, ...] = ('cg-gnn', 'graph-transformer'),
                            ):
    dfs = [df_study(study_name, host, cohorts, phenotypes, plugin_name=plugin_name)
           for plugin_name in plugin_names]
    if channel_order is None:
        channel_order = phenotypes.copy()
    if 'cohort' not in channel_order:
        channel_order.append('cohort')
    dfs_heatmap = [df.drop('Cell count', axis=1, level=0)[channel_order] for df in dfs]
    plot_2_heatmaps(tuple(dfs_heatmap),
                    plugin_names,
                    study_name,
                    output_directory=output_directory,
                    cohort_map=cohort_map,
                    concat_axis=concat_axis,
                    figsize=figsize)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('host', type=str, help='SPT API endpoint host to query')
    parser.add_argument('output_directory', type=str, default='', help='Directory to save SVGs in.')
    args = parser.parse_args()

    plt.rcParams['font.size'] = 14

    phenotypes_miil2 = ['Tumor',
                        'Adipocyte or Langerhans cell',
                        'Nerve',
                        'B cell',
                        'Natural killer cell',

                        # T cells
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

                        # Macrophages
                        'CD163+MHCII- macrophage',
                        'CD163+MHCII+ macrophage',
                        'CD68+MHCII- macrophage',
                        'CD68+MHCII+ macrophage',
                        'Other macrophage/monocyte CD14+',
                        'Other macrophage/monocyte CD4+',
                        ]
    channel_order_miil2 = [
        # Mostly active
        'Tumor',
        'Adipocyte or Langerhans cell',
        'Natural killer cell',
        'CD4+ T cell',

        # Macrophages
        'CD163+MHCII- macrophage',
        'CD163+MHCII+ macrophage',
        'CD68+MHCII- macrophage',
        'CD68+MHCII+ macrophage',
        'Other macrophage/monocyte CD14+',
        'Other macrophage/monocyte CD4+',

        # Slightly active
        'Nerve',
        'B cell',

        # T cells useful for only one cohort
        'CD4+/CD8+ T cell',
        'CD4+ regulatory T cell',
        'CD8+ natural killer T cell',
        'CD8+ regulatory T cell',
        'CD8+ T cell',
        'Double negative regulatory T cell',
        'T cell/null phenotype',

        # Mostly inactive
        'Natural killer T cell',
        'CD4+ natural killer T cell',
    ] + ['cohort']
    miil2_cohort_map = {
        1: 'Non-responder',
        3: 'Ex. responder',
    }
    generate_study_heatmaps('Melanoma intralesional IL2',
                            args.host,
                            set(miil2_cohort_map.keys()),
                            phenotypes_miil2,
                            (11, 8),
                            output_directory=args.output_directory,
                            channel_order=channel_order_miil2,
                            cohort_map=miil2_cohort_map,
                            concat_axis='horizontal',
                            )

    phenotypes_uro = ['CD4- CD8- T cell',
                      'intratumoral CD3+ LAG3+',
                      'Macrophage',
                      'Regulatory T cell',
                      'T cytotoxic cell',
                      'T helper cell',
                      'Tumor',
                      ]
    channel_order_uro = [
        'Tumor',
        'CD4- CD8- T cell',
        'T cytotoxic cell',
        'T helper cell',
        'Macrophage',
        'intratumoral CD3+ LAG3+',
        'Regulatory T cell',
    ] + ['cohort']
    uro_cohort_map = {
        1: 'Responder',
        2: 'Non-responder',
    }
    generate_study_heatmaps('Urothelial ICI',
                            args.host,
                            set(uro_cohort_map.keys()),
                            phenotypes_uro,
                            (14, 5),
                            output_directory=args.output_directory,
                            channel_order=channel_order_uro,
                            cohort_map=uro_cohort_map,
                            concat_axis='vertical',
                            )
