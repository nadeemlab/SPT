"""Data analysis script for one the "Melanoma intralesional IL2" study."""

import sys
from pandas import DataFrame
from numpy import mean

from scipy.stats import fisher_exact

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare
from accessors import handle_expected_actual


def test(host):
    study = 'Melanoma intralesional IL2'
    access = DataAccessor(study, host=host)

    exhausted = {'positive_markers': ['KI67', 'PD1', 'LAG3', 'TIM3'], 'negative_markers': []}
    df = access.counts(['CD8+ T cell', exhausted])

    # On average, the fraction of cells that are CD8+ T cells and KI67+ LAG3+ PD1+ TIM3+ is 24.51
    # times higher in cohort 3 than in cohort 1.
    fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=24.51, show_pvalue=True, show_auc=True)

    # On average, the ratio of the number of cells that are CD8+ T cells and KI67+ LAG3+ PD1+ TIM3+
    # to those that are CD8+ T cells is 6.29 times higher in cohort 3 than in cohort 1.
    fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['CD8+ T cell']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=6.29, show_pvalue=True, show_auc=True)

    mhci = {'positive_markers': ['MHCI'], 'negative_markers': []}
    df = access.counts(['Tumor', mhci])

    # On average, the ratio of the number of cells that are MHCI+ and Tumor to those that are Tumor
    # is 1.86 times higher in cohort 3 than in cohort 1.
    fractions = df['Tumor and MHCI+'] / df['Tumor']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=1.86, show_auc=True)

    # The average value of the proximity score for phenotype(s) B cells is 3.59 times higher in
    # cohort 3 than in cohort 1.
    df = access.proximity(['B cell', 'B cell'])
    values1 = df[df['cohort'] == '1']['proximity, B cell and B cell']
    values3 = df[df['cohort'] == '3']['proximity, B cell and B cell']
    compare(values1, values3, expected_fold=3.59)

    # Some not-so-statistically significant results
    s100b = 'Adipocyte or Langerhans cell'
    df = access.counts([s100b, 'B cell'])
    fractions = df[s100b] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=0.226, show_pvalue=True, show_auc=True)

    df = access.spatial_autocorrelation(s100b)
    values1 = df[df['cohort'] == '1'][f'spatial autocorrelation, {s100b}']
    values3 = df[df['cohort'] == '3'][f'spatial autocorrelation, {s100b}']
    compare(values1, values3, expected_fold=0.06690, show_pvalue=True, show_auc=True)

    df = access.proximity([s100b, s100b])
    values1 = df[df['cohort'] == '1'][f'proximity, {s100b} and {s100b}']
    values3 = df[df['cohort'] == '3'][f'proximity, {s100b} and {s100b}']
    compare(values1, values3, expected_fold=0.146, show_pvalue=True, show_auc=True)

    # The average value of the neighborhood enrichment score for phenotype(s) B cells is 9.39 times
    # higher in cohort 1 than in cohort 3.
    df = access.neighborhood_enrichment(['B cell', 'B cell'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, B cell and B cell']
    values3 = df[df['cohort'] == '3']['neighborhood enrichment, B cell and B cell']
    compare(values1, values3, expected_fold=0.106, show_pvalue=True, show_auc=True)

    for phenotype, expected_baseline, expected_percentage, expected_p in [
        ('Adipocyte or Langerhans cell', 3.593e-2, 15.33, [3, 9]),
        ([{'positive_markers': ['S100B'], 'negative_markers': ['SOX10']}], 6.710e-2, 18.33, [3, 9])
    ]:
        result_df = DataFrame(columns=['odds ratio', 'p-value'])
        result_df.index.name = 'specimen'
        df = access.counts(phenotype)
        df = df[df['cohort'].isin({'1', '3'})]
        important_number = access.important(phenotype)
        important_number = {key: value for key, value in important_number.items() if key in df.index}
        if (type(phenotype) is list):
            phenotype = access.name_for_all_phenotypes(phenotype)
        for specimen, _row in df.iterrows():
            row = _row.drop_duplicates()
            number_cells_of_this_phenotype = row[phenotype]
            number_cells_total = row['all cells']
            important_and_phenotype = important_number[specimen]
            b = number_cells_of_this_phenotype - important_and_phenotype
            c = 100 - important_and_phenotype
            d = important_and_phenotype
            a = number_cells_total - b - c - d
            odds_ratio, p_value = fisher_exact([[a, b], [c, d]])
            result_df.loc[specimen] = [odds_ratio, p_value]
        print(f'\nBaseline presence of {phenotype}')
        handle_expected_actual(expected_baseline, (df[phenotype].iloc[:, 0]/df['all cells']).mean())
        print(f'\nPercentage of top 100 most important cells for GNN classification, of this phenotype')
        handle_expected_actual(expected_percentage, mean(list(important_number.values())))
        assert expected_p[1] == result_df.shape[0]
        print(f'\nNumber of Fisher exact test p-values (out of {expected_p[1]}) less than 0.001')
        handle_expected_actual(expected_p[0], sum(1 for p in list(result_df['p-value']) if p < 0.001))
        print('')


if __name__ == '__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
