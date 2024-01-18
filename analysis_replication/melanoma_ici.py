"""Data analysis script for one dataset."""
import sys

from numpy import mean

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Melanoma CyTOF ICI'
    access = DataAccessor(study, host=host)

    antigen_experienced_cytotoxic = {'positive_markers': ['CD8A', 'CD3', 'CD45RO'], 'negative_markers': []}
    antigen_experienced_cytotoxic_min = {'positive_markers': ['CD8A', 'CD45RO'], 'negative_markers': []}

    # # The average value of the neighborhood enrichment score for phenotype(s) CD3+ CD45RO+ CD8A+ and
    # # Melanoma is ... times higher in cohort 1 than in cohort 2.
    # df = access.neighborhood_enrichment([antigen_experienced_cytotoxic, 'Melanoma'])
    # values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    # values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
    # # handle_expected_actual(1.234, mean1 / mean2)
    # # # handle_expected_actual(1.39, mean1 / mean2)
    # compare(values2, values1, expected_fold=3.094, show_pvalue=True)

    # df = access.neighborhood_enrichment([antigen_experienced_cytotoxic_min, 'Melanoma'])
    # values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD8A+ CD45RO+ and Melanoma']
    # values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD8A+ CD45RO+ and Melanoma']
    # # handle_expected_actual(1.234, mean1 / mean2)
    # # # handle_expected_actual(1.39, mean1 / mean2)
    # compare(values2, values1, expected_fold=2.57, show_pvalue=True)

    # # On average, the fraction of cells that are CD8A+ CD3+ CD45RO+ and MKI67+ is ... times higher
    # # in cohort 1 than in cohort 2.
    # proliferative = {'positive_markers': ['MKI67'], 'negative_markers': []}
    # df = access.counts([antigen_experienced_cytotoxic, proliferative])
    # fractions = df['CD8A+ CD3+ CD45RO+ and MKI67+'] / df['all cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.299, show_pvalue=True)


    # # Poor p-values
    # df = access.counts(['Cytotoxic T cell antigen-experienced', 'Naive cytotoxic T cell'])
    # fractions = df['Cytotoxic T cell antigen-experienced'] / df['Naive cytotoxic T cell']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.311, show_pvalue=True)

    # fractions = df['Naive cytotoxic T cell'] / df['Cytotoxic T cell antigen-experienced']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.47, show_pvalue=True)

    # df = access.counts(['Cytotoxic T cell antigen-experienced', 'T helper cell antigen-experienced'])
    # fractions = df['Cytotoxic T cell antigen-experienced'] / df['T helper cell antigen-experienced']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.237, show_pvalue=True)

    # fractions = df['T helper cell antigen-experienced'] / df['Cytotoxic T cell antigen-experienced']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.11, show_pvalue=True)

    # df = access.counts(['Naive cytotoxic T cell', 'Lineage including macrophage'])
    # fractions = df['Naive cytotoxic T cell'] / df['Lineage including macrophage']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=260.99, show_pvalue=True)

    # fractions = df['Lineage including macrophage'] / df['Naive cytotoxic T cell']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.44, show_pvalue=True)

    # df = access.counts(['T cells', 'Lineage including macrophage'])
    # fractions = df['T cells'] / df['Lineage including macrophage']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=30.49, show_pvalue=True)

    # fractions = df['Lineage including macrophage'] / df['T cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.58, show_pvalue=True)

    # df = access.counts(['Naive cytotoxic T cell', 'Lineage including monocyte'])
    # fractions = df['Naive cytotoxic T cell'] / df['Lineage including monocyte']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=161.3, show_pvalue=True)

    # fractions = df['Lineage including monocyte'] / df['Naive cytotoxic T cell']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.467, show_pvalue=True)

    # df = access.counts(['B cells', 'T regulatory cells'])
    # fractions = df['B cells'] / df['T regulatory cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.033, show_pvalue=True)

    # fractions = df['T regulatory cells'] / df['B cells']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=1.69, show_pvalue=True)

    df = access.counts(['Endothelial stroma', 'Melanoma'])
    fractions = df['Endothelial stroma'] / df['Melanoma']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=7.44, show_pvalue=True)

    fractions = df['Melanoma'] / df['Endothelial stroma']
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions2, fractions1, expected_fold=0.101, show_pvalue=True)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    print(f'Using API server: {host}')
    test(host)
