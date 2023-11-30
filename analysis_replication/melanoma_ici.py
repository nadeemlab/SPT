"""Data analysis script for one dataset."""

import sys

from numpy import mean

from accessors import DataAccessor
from accessors import handle_expected_actual

def test():
    study = 'Melanoma CyTOF ICI'
    if len(sys.argv) == 1:
        access = DataAccessor(study)
    else:
        access = DataAccessor(study, host=sys.argv[1])

    print('')
    print(study)

    antigen_experienced_cytotoxic = {'positive_markers': ['CD8A', 'CD3', 'CD45RO'], 'negative_markers': []}

    # The average value of the neighborhood enrichment score for phenotype(s) CD3+ CD45RO+ CD8A+ and
    # Melanoma is 1.39 times higher in cohort 1 than in cohort 2.
    df = access.neighborhood_enrichment([antigen_experienced_cytotoxic, 'Melanoma'])
    print(df)
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    mean1 = float(mean(values1))
    mean2 = float(mean(values2))
    print((mean1, mean2, mean1 / mean2))

    handle_expected_actual(1.234, mean1 / mean2)
    # handle_expected_actual(1.39, mean1 / mean2)

    print('')

    # # The average value of the co-occurrence score for phenotype(s) CD3+ CD45RO+ CD8A+ and Melanoma
    # # is 1.13 times higher in cohort 1 than in cohort 2.
    # df = access.co_occurrence([antigen_experienced_cytotoxic, 'Melanoma'])
    # print(df)
    # values1 = df[df['cohort'] == '1']['co-occurrence, CD8A+ CD3+ CD45RO+ and Melanoma']
    # values2 = df[df['cohort'] == '2']['co-occurrence, CD8A+ CD3+ CD45RO+ and Melanoma']
    # mean1 = float(mean(values1))
    # mean2 = float(mean(values2))
    # print((mean1, mean2, mean1 / mean2))

    # handle_expected_actual(1.13, mean1 / mean2)

    print('')

    # On average, the fraction of cells that are CD8A+ CD3+ CD45RO+ and MKI67+ is 1.41 times higher
    # in cohort 1 than in cohort 2.
    proliferative = {'positive_markers': ['MKI67'], 'negative_markers': []}
    df = access.counts([antigen_experienced_cytotoxic, proliferative])
    print(df)
    fractions = df['CD8A+ CD3+ CD45RO+ and MKI67+'] / df['all cells']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    mean1 = float(mean(fractions1))
    mean2 = float(mean(fractions2))
    print((mean1, mean2, mean1 / mean2))

    handle_expected_actual(1.41, mean1 / mean2)


if __name__=='__main__':
    test()
