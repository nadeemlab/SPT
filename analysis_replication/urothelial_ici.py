"""Data analysis script for one dataset."""
import sys

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Urothelial ICI'
    access = DataAccessor(study, host=host)

    cd3tumoral = {'positive_markers': ['CD3', 'intratumoral'], 'negative_markers': []}
    lag3 = {'positive_markers': ['LAG3'], 'negative_markers': []}
    df = access.counts([cd3tumoral, lag3])

    fractions = df['CD3+ intratumoral+ and LAG3+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=0.0857, show_pvalue=True)

    fractions = df['CD3+ intratumoral+ and LAG3+'] / df['CD3+ intratumoral+']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=0.423, show_pvalue=True)

    cd3lag3 = {'positive_markers': ['CD3', 'LAG3'], 'negative_markers': []}
    cd8ki67 = {'positive_markers': ['CD8', 'KI67'], 'negative_markers': []}
    cd8pd1lag3 = {'positive_markers': ['CD8', 'PD1', 'LAG3'], 'negative_markers': []}
    cd3pd1lag3 = {'positive_markers': ['CD3', 'PD1', 'LAG3'], 'negative_markers': []}
    tumoral = {'positive_markers': ['intratumoral'], 'negative_markers': []}
    stromal = {'positive_markers': ['stromal'], 'negative_markers': []}

    # df = access.counts([cd3lag3, tumoral])
    # fractions = df['CD3+ LAG3+ and intratumoral+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions3 = fractions[df['cohort'] == '3']
    # compare(fractions1, fractions3, expected_fold=1.0, show_pvalue=True)

    df = access.counts([cd8ki67, tumoral])
    fractions = df['CD8+ KI67+ and intratumoral+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=0.076, show_pvalue=True)

    df = access.counts([cd8pd1lag3, tumoral])
    fractions = df['CD8+ PD1+ LAG3+ and intratumoral+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=1.0, show_pvalue=True)

    df = access.counts([cd8pd1lag3, stromal])
    fractions = df['CD8+ PD1+ LAG3+ and stromal+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=1.0, show_pvalue=True)

    df = access.counts([cd3pd1lag3, tumoral])
    fractions = df['CD3+ PD1+ LAG3+ and intratumoral+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=1.0, show_pvalue=True)

    df = access.counts([cd3pd1lag3, stromal])
    fractions = df['CD3+ PD1+ LAG3+ and stromal+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions1, fractions3, expected_fold=1.0, show_pvalue=True)

if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
