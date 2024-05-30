"""Data analysis script for one dataset."""
import sys
from typing import Any

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare
from accessors import get_fractions
from accessors import ExpectedQuantitativeValueError


def channel_fractions(access: DataAccessor):
    cd3 = {'positive_markers': ['CD3'], 'negative_markers': []}
    cd3tumoral = {'positive_markers': ['CD3', 'intratumoral'], 'negative_markers': []}
    cd8ki67 = {'positive_markers': ['CD8', 'KI67'], 'negative_markers': []}
    cd8ki67tumoral = {'positive_markers': ['CD8', 'KI67', 'intratumoral'], 'negative_markers': []}
    cd8tumoral = {'positive_markers': ['CD8', 'intratumoral'], 'negative_markers': []}
    cd8pd1lag3 = {'positive_markers': ['CD8', 'PD1', 'LAG3'], 'negative_markers': []}
    cd3pd1lag3 = {'positive_markers': ['CD3', 'PD1', 'LAG3'], 'negative_markers': []}
    cd3pd1 = {'positive_markers': ['CD3', 'PD1'], 'negative_markers': []}
    cd3lag3 = {'positive_markers': ['CD3', 'LAG3'], 'negative_markers': []}
    cd3pd1lag3stromal = {'positive_markers': ['CD3', 'PD1', 'LAG3', 'stromal'], 'negative_markers': []}
    cd3pd1lag3intratumoral = {'positive_markers': ['CD3', 'PD1', 'LAG3', 'intratumoral'], 'negative_markers': []}
    cd3stromal = {'positive_markers': ['CD3', 'stromal'], 'negative_markers': []}
    tumor = {'positive_markers': ['PanCK-SOX10'], 'negative_markers': []}
    tumoral = {'positive_markers': ['intratumoral'], 'negative_markers': []}

    # Not predictive
    df = access.counts([cd3lag3, cd3])
    fractions1, fractions2 = get_fractions(df, 'CD3+ LAG3+', 'CD3+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=1.449, show_pvalue=True, show_auc=True)


    df = access.counts([cd8ki67, tumoral])
    fractions1, fractions2 = get_fractions(df, 'CD8+ KI67+ and intratumoral+', 'all cells', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=3.519, show_pvalue=True, show_auc=True)

    df = access.counts([cd8ki67tumoral, tumoral])
    fractions1, fractions2 = get_fractions(df, 'CD8+ KI67+ intratumoral+', 'intratumoral+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=3.534, show_pvalue=True, show_auc=True)

    df = access.counts([cd3pd1lag3, cd3])
    fractions1, fractions2 = get_fractions(df, 'CD3+ PD1+ LAG3+', 'CD3+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=2.81, show_pvalue=True, show_auc=True)

    df = access.counts([cd3pd1, cd3])
    fractions1, fractions2 = get_fractions(df, 'CD3+ PD1+', 'CD3+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=1.26, show_pvalue=True, show_auc=True)

    df = access.counts([cd3lag3, cd3])
    fractions1, fractions2 = get_fractions(df, 'CD3+ LAG3+', 'CD3+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=1.449, show_pvalue=True, show_auc=True)

    print('\nSome lesser results:')

    df = access.counts([cd8tumoral, tumor])
    fractions1, fractions2 = get_fractions(df, 'CD8+ intratumoral+', 'PanCK-SOX10+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=3.113, show_pvalue=True, show_auc=True)

    df = access.counts([cd3tumoral, tumor])
    fractions1, fractions2 = get_fractions(df, 'CD3+ intratumoral+', 'PanCK-SOX10+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=2.718, show_pvalue=True, show_auc=True)

    df = access.counts([cd8pd1lag3, tumoral])
    fractions1, fractions2 = get_fractions(df, 'CD8+ PD1+ LAG3+ and intratumoral+', 'all cells', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=3.095, show_pvalue=True, show_auc=True)

    df = access.counts([cd3pd1lag3stromal, cd3stromal])
    fractions1, fractions2 = get_fractions(df, 'CD3+ PD1+ LAG3+ stromal+', 'CD3+ stromal+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=2.921, show_pvalue=True, show_auc=True)

    df = access.counts([cd3pd1lag3intratumoral, cd3tumoral])
    fractions1, fractions2 = get_fractions(df, 'CD3+ PD1+ LAG3+ intratumoral+', 'CD3+ intratumoral+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=2.97, show_pvalue=True, show_auc=True)


def phenotype_fractions(access: DataAccessor):
    print('\nPhenotype results (all weak):')
    null = 'CD4- CD8- T cell'
    M = 'Macrophage'
    Treg = 'Regulatory T cell'
    Tc = 'T cytotoxic cell'
    Th = 'T helper cell'
    T = 'Tumor'
    ex = 'intratumoral CD3+ LAG3+'
    cases = (
        (null, T, 1/3.05),
        (null, ex, 14.7),
        (M, null, 4.46),
        (M, Tc, 7.76),
        (M, Th, 4.72),
        (M, ex, 6.29),
        (Treg, T, 1/10.18),
        (Treg, ex, 9.885),
        (Tc, Th, 13.62),
        (Th, Tc, 0.75),
        (Tc, ex, 9.92),
        (Th, T, 1/5.72),
        (Th, ex, 11.32),
    )
    for P1, P2, E in cases:
        df = access.counts([P1, P2])
        fractions1, fractions2 = get_fractions(df, P1, P2, '1', '2', omit_zeros=False)
        compare(fractions2, fractions1, expected_fold=E, show_pvalue=True, show_auc=True)

def nominalize(item):
    if isinstance(item, str):
        return item
    c1 = ' '.join([f'{p}+' for p in item['positive_markers']])
    if len(item['negative_markers']) > 0 and item['negative_markers'] != ['']:
        c2 = ' '.join([f'{p}-' for p in item['negative_markers']])        
        return f'{c1} {c2}'
    return c1

def one_case_spatial(access, P1, P2, E, feature_class: str | None = None):
    if feature_class is None:
        raise ValueError('Specify feature class.')
    if feature_class == 'proximity':
        df = access.proximity([P1, P2])
    if feature_class == 'neighborhood enrichment':
        df = access.neighborhood_enrichment([P1, P2])
    feature = f'{feature_class}, {nominalize(P1)} and {nominalize(P2)}'
    print(feature)
    values = {c: df[df['cohort'] == c][feature] for c in ('1', '2')}
    do_log_fold = feature_class == 'neighborhood enrichment'
    compare(values['1'], values['2'], expected_fold=E, show_pvalue=True, do_log_fold=do_log_fold, show_auc=True)

def spatial(access: DataAccessor):
    print('\nSpatial results:')
    cases: tuple[tuple[Any, ...], ...]
    cases = (
        ('Macrophage', 'Regulatory T cell', 2.110, 1.285),
        ('Macrophage', 'T helper cell', 1.812, 2.089),
    )
    lesser_cases = (
        ('Regulatory T cell', 'CD4- CD8- T cell', 1.578, 1.459),
        ('Macrophage', 'CD4- CD8- T cell', 3.099, 1.221),
        ('Macrophage', 'T cytotoxic cell', 1.453, 2.973),
        ('Macrophage', 'intratumoral CD3+ LAG3+', 2.308, 0.441),
    )
    for P1, P2, E, Ei in cases:
        try:
            one_case_spatial(access, P1, P2, E, feature_class='neighborhood enrichment')
            one_case_spatial(access, P2, P1, Ei, feature_class='neighborhood enrichment')
        except ExpectedQuantitativeValueError as error:
            print(str(error))
            continue

    print('\nLesser significance results:')
    for P1, P2, E, Ei in lesser_cases:
        try:
            one_case_spatial(access, P1, P2, E, feature_class='neighborhood enrichment')
            one_case_spatial(access, P2, P1, Ei, feature_class='neighborhood enrichment')
        except ExpectedQuantitativeValueError as error:
            print(str(error))
            continue

    proximity_cases = (
        ('intratumoral CD3+ LAG3+', 'intratumoral CD3+ LAG3+', 1.8, None),
        ({'positive_markers': ['intratumoral', 'CD3'], 'negative_markers': []}, {'positive_markers': ['PDL1'], 'negative_markers': []}, 1.197, 0.589),
        ('intratumoral CD3+ LAG3+', 'T helper cell', 2.42, 1.593),
    )
    for P1, P2, E, Ei in proximity_cases:
        one_case_spatial(access, P1, P2, E, feature_class='proximity')
        if P1 != P2:
            one_case_spatial(access, P2, P1, Ei, feature_class='proximity')


def test(host):
    study = 'Urothelial ICI'
    access = DataAccessor(study, host=host)    
    channel_fractions(access)
    phenotype_fractions(access)
    spatial(access)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
