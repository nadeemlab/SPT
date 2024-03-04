"""Data analysis script for one dataset."""
import sys

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare
from accessors import get_fractions

def test(host):
    study = 'Urothelial ICI'
    access = DataAccessor(study, host=host)

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

    df = access.counts([cd8ki67tumoral, tumor])
    fractions1, fractions2 = get_fractions(df, 'CD8+ KI67+ intratumoral+', 'PanCK-SOX10+', '1', '2', omit_zeros=False)
    compare(fractions2, fractions1, expected_fold=6.50, show_pvalue=True, show_auc=True)

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

    print('\nSpatial results:')
    

if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
