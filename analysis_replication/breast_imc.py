"""Data analysis script for one dataset."""
import sys

from numpy import mean
from numpy import inf

from accessors import DataAccessor
from accessors import get_default_host
from accessors import handle_expected_actual

def test(host):
    study = 'Breast cancer IMC'
    access = DataAccessor(study, host=host)

    print('')
    print(study)

    KRT = {
    '5': {'positive_markers': ['KRT5', 'CK'], 'negative_markers': []},
    '7': {'positive_markers': ['KRT7', 'CK'], 'negative_markers': []},
    '14': {'positive_markers': ['KRT14', 'CK'], 'negative_markers': []},
    '19': {'positive_markers': ['KRT19', 'CK'], 'negative_markers': []},
    }

    df = access.proximity([KRT['14'], KRT['7']])
    values1 = df[df['cohort'] == '1']['proximity, KRT14+ CK+ and KRT7+ CK+']
    values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT7+ CK+']
    mean1 = float(mean(values1))
    mean2 = float(mean(values2))
    print((mean2, mean1, mean2 / mean1))

    handle_expected_actual(1.6216, mean2 / mean1)
    # handle_expected_actual(1.69, mean2 / mean1)

    df = access.proximity([KRT['14'], KRT['5']])
    values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT5+ CK+']
    values3 = df[df['cohort'] == '3']['proximity, KRT14+ CK+ and KRT5+ CK+']
    mean2 = float(mean(values2))
    mean3 = float(mean(values3))
    print((mean2, mean3, mean2 / mean3))

    # handle_expected_actual(0.65, mean2 / mean3)
    handle_expected_actual(1.265, mean2 / mean3)

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
    mean1 = float(mean(fractions1))
    mean2 = float(mean(fractions2))
    mean3 = float(mean(fractions3))
    print((mean2, mean3, mean2 / mean3))
    print((mean2, mean1, mean2 / mean1))

    handle_expected_actual(111.32, mean2 / mean3)
    handle_expected_actual(11.39, mean2 / mean1)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(get_default_host(None))
