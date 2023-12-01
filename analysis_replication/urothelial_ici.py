"""Data analysis script for one dataset."""
import sys

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Urothelial ICI'
    access = DataAccessor(study, host=host)

    cd3tumoral = {'positive_markers': ['CD3', 'intratumoral'], 'negative_markers': []}
    cd4tumoral = {'positive_markers': ['CD4', 'intratumoral'], 'negative_markers': []}
    lag3 = {'positive_markers': ['LAG3'], 'negative_markers': []}
    df = access.counts([cd3tumoral, lag3])

    # fractions = df['CD3+ intratumoral+ and LAG3+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=2.454, show_pvalue=True)

    # fractions = df['CD3+ intratumoral+ and LAG3+'] / df['CD3+ intratumoral+']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.546, show_pvalue=True)

    cd3lag3 = {'positive_markers': ['CD3', 'LAG3'], 'negative_markers': []}
    cd8ki67 = {'positive_markers': ['CD8', 'KI67'], 'negative_markers': []}
    cd8ki67tumoral = {'positive_markers': ['CD8', 'KI67', 'intratumoral'], 'negative_markers': []}
    cd8tumoral = {'positive_markers': ['CD8', 'intratumoral'], 'negative_markers': []}
    cd8pd1lag3 = {'positive_markers': ['CD8', 'PD1', 'LAG3'], 'negative_markers': []}
    cd3pd1lag3 = {'positive_markers': ['CD3', 'PD1', 'LAG3'], 'negative_markers': []}
    cd3pd1lag3stromal = {'positive_markers': ['CD3', 'PD1', 'LAG3', 'stromal'], 'negative_markers': []}
    cd8pd1lag3stromal = {'positive_markers': ['CD8', 'PD1', 'LAG3', 'stromal'], 'negative_markers': []}
    cd3stromal = {'positive_markers': ['CD3', 'stromal'], 'negative_markers': []}
    cd8stromal = {'positive_markers': ['CD8', 'stromal'], 'negative_markers': []}
    tumor = {'positive_markers': ['PanCK-SOX10'], 'negative_markers': []}
    tumoral = {'positive_markers': ['intratumoral'], 'negative_markers': []}
    stromal = {'positive_markers': ['stromal'], 'negative_markers': []}

    df = access.counts([cd8ki67, tumoral])
    fractions = df['CD8+ KI67+ and intratumoral+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=3.520, show_pvalue=True)

    df = access.counts([cd8ki67tumoral, tumor])
    fractions = df['CD8+ KI67+ intratumoral+'] / df['PanCK-SOX10+']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=6.508, show_pvalue=True)

    df = access.counts([cd8tumoral, tumor])
    fractions = df['CD8+ intratumoral+'] / df['PanCK-SOX10+']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=3.113, show_pvalue=True)

    # df = access.counts([cd4tumoral, tumor])
    # fractions = df['CD4+ intratumoral+'] / df['PanCK-SOX10+']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.336, show_pvalue=True)

    df = access.counts([cd3tumoral, tumor])
    fractions = df['CD3+ intratumoral+'] / df['PanCK-SOX10+']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=2.718, show_pvalue=True)

    df = access.counts([cd8pd1lag3, tumoral])
    fractions = df['CD8+ PD1+ LAG3+ and intratumoral+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=3.095, show_pvalue=True)

    # df = access.counts([cd8pd1lag3, stromal])
    # fractions = df['CD8+ PD1+ LAG3+ and stromal+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.063, show_pvalue=True)

    # df = access.counts([cd3pd1lag3, tumoral])
    # fractions = df['CD3+ PD1+ LAG3+ and intratumoral+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=2.151, show_pvalue=True)

    # df = access.counts([cd3pd1lag3, stromal])
    # fractions = df['CD3+ PD1+ LAG3+ and stromal+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.535, show_pvalue=True)

    df = access.counts([cd3pd1lag3stromal, cd3stromal])
    fractions = df['CD3+ PD1+ LAG3+ stromal+'] / df['CD3+ stromal+']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=2.921, show_pvalue=True)

    # df = access.counts([cd8pd1lag3stromal, cd8stromal])
    # fractions = df['CD8+ PD1+ LAG3+ stromal+'] / df['CD8+ stromal+']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.4999, show_pvalue=True)

if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
