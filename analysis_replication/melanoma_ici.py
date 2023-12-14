"""Data analysis script for one dataset."""
import sys

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Melanoma CyTOF ICI'
    access = DataAccessor(study, host=host)

    antigen_experienced_cytotoxic = {'positive_markers': ['CD8A', 'CD3', 'CD45RO'], 'negative_markers': []}

    # The average value of the neighborhood enrichment score for phenotype(s) CD3+ CD45RO+ CD8A+ and
    # Melanoma is 1.39 times higher in cohort 1 than in cohort 2.
    df = access.neighborhood_enrichment([antigen_experienced_cytotoxic, 'Melanoma'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    # handle_expected_actual(1.234, mean1 / mean2)
    # # handle_expected_actual(1.39, mean1 / mean2)
    compare(values2, values1, expected_fold=1.234, do_log_fold=True)

    # On average, the fraction of cells that are CD8A+ CD3+ CD45RO+ and MKI67+ is 1.41 times higher
    # in cohort 1 than in cohort 2.
    proliferative = {'positive_markers': ['MKI67'], 'negative_markers': []}
    df = access.counts([antigen_experienced_cytotoxic, proliferative])
    fractions = df['CD8A+ CD3+ CD45RO+ and MKI67+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=1.41)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
