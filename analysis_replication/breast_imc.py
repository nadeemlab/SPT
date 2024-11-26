"""Data analysis script for one dataset."""
import sys

from numpy import mean
from numpy import inf

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Breast cancer IMC'
    access = DataAccessor(study, host=host)

    KRT = {
    '5': {'positive_markers': ['KRT5', 'CK'], 'negative_markers': []},
    '7': {'positive_markers': ['KRT7', 'CK'], 'negative_markers': []},
    '14': {'positive_markers': ['KRT14', 'CK'], 'negative_markers': []},
    '19': {'positive_markers': ['KRT19', 'CK'], 'negative_markers': []},
    }

    df = access.proximity([KRT['14'], KRT['7']])
    values1 = df[df['cohort'] == '1']['proximity, KRT14+ CK+ and KRT7+ CK+']
    values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT7+ CK+']
    # handle_expected_actual(1.6216, mean2 / mean1)
    # # handle_expected_actual(1.69, mean2 / mean1)
    compare(values1, values2, expected_fold=1.6216, show_pvalue=True, show_auc=True)

    df = access.proximity([KRT['14'], KRT['5']])
    values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT5+ CK+']
    values3 = df[df['cohort'] == '3']['proximity, KRT14+ CK+ and KRT5+ CK+']
    # # handle_expected_actual(0.65, mean2 / mean3)
    # handle_expected_actual(1.265, mean2 / mean3)
    compare(values3, values2, expected_fold=1.7463, show_pvalue=True)

    df = access.counts([KRT['14'], KRT['7']])
    fractions = df['KRT14+ CK+ and KRT7+ CK+'] / df['all cells']
    mean0 = float(mean(fractions))
    print(mean0)

    df = access.counts([KRT['14'], KRT['5']])
    fractions = df['KRT14+ CK+ and KRT5+ CK+'] / df['all cells']
    mean0 = float(mean(fractions))
    print(mean0)

    df = access.counts([KRT['14'], KRT['19']])
    fractions = df['KRT14+ CK+'] / df['KRT19+ CK+']
    fractions = fractions[fractions != inf]
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    fractions3 = fractions[df['cohort'] == '3']
    compare(fractions3, fractions2, expected_fold=111.32, show_pvalue=True)
    compare(fractions1, fractions2, expected_fold=11.39, show_pvalue=True)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(get_default_host(None))
