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

    # Poor p values
    # # # The average value of the neighborhood enrichment score for phenotype(s) CD3+ CD45RO+ CD8A+ and
    # # # Melanoma is ... times higher in cohort 1 than in cohort 2.
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

    # df = access.counts(['Endothelial stroma', 'Melanoma'])
    # fractions = df['Endothelial stroma'] / df['Melanoma']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=7.44, show_pvalue=True)

    # fractions = df['Melanoma'] / df['Endothelial stroma']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.101, show_pvalue=True)


    # Middling p
    # On average, the ratio of the number of cells that are Lineage including macrophage and B cellss to those that are Naive cytotoxic T cells is 3.21 times higher in cohort 2 than in cohort 1.
    # df = access.counts(['Lineage including macrophage', 'B cells'])
    # df2 = access.counts(['Naive cytotoxic T cell', 'B cells'])
    # fractions = df['Lineage including macrophage and B cells'] / df2['Naive cytotoxic T cell']
    # fractions1 = fractions[df['cohort'] == '1']
    # fractions2 = fractions[df['cohort'] == '2']
    # compare(fractions2, fractions1, expected_fold=0.280, show_pvalue=True)  # p=0.12

    # Poor p:

    # On average, the ratio of the number of cells that are Lineage including monocyte and B cellss to those that are Naive cytotoxic T cells is 3.73 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are Naive T helper cells and B cells to those that are Naive cytotoxic T cells is 4.08 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are Naive T helper cells and B cells to those that are T regulatory cellss is 34.96 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are T helper cells antigen-experienced and B cells to those that are Naive cytotoxic T cells is 3.44 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are T helper cells antigen-experienced and B cells to those that are T regulatory cellss is 24.75 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are Naive cytotoxic T cells and Cytotoxic T cell antigen-experienced to those that are Lineage including monocyte is 201.55 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are Naive cytotoxic T cells and Cytotoxic T cell antigen-experienced to those that are Lineage including macrophage is 269.05 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are Lineage including monocyte and Lineage including macrophage to those that are B cellss is 31.80 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are T helper cells antigen-experienced and Naive T helper cell to those that are T regulatory cellss is 3.95 times higher in cohort 2 than in cohort 1.
    # ...

    # On average, the ratio of the number of cells that are T helper cells antigen-experienced and Naive T helper cell to those that are Lineage including macrophage is 5.56 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are T helper cells antigen-experienced and Naive T helper cell to those that are Lineage including monocyte is 7.75 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are T regulatory cellss and T helper cell antigen-experienced to those that are Lineage including monocyte is 95.74 times higher in cohort 1 than in cohort 2.
    # ...

    # On average, the ratio of the number of cells that are T regulatory cellss and T helper cell antigen-experienced to those that are Lineage including macrophage is 87.68 times higher in cohort 1 than in cohort 2.
    # ...

    # channels = ['ICOS', 'PDL1', 'CD8A', 'CD20', 'CD45RA']
    def p(channel):
        return {'positive_markers':[channel], 'negative_markers':[]}

    for channel, fold in zip(['ICOS', 'CD8A'], [0.791, 0.782]):
        df = access.proximity([p(channel), p(channel)])
        prox = f'proximity, {channel}+ and {channel}+'
        print(f'Proximity of {channel} to {channel}')
        values1 = df[df['cohort'] == '1'][prox]
        values2 = df[df['cohort'] == '2'][prox]
        compare(values1, values2, expected_fold=fold, show_pvalue=True, show_auc=True)

    for channel, fold in zip(['ICOS', 'CD8A', 'PDL1', 'CD45RA'], [2.366, 2.708, 14.49, 0.475]):
        df = access.spatial_autocorrelation(p(channel))
        autocorr = f'spatial autocorrelation, {channel}+'
        values1 = df[df['cohort'] == '1'][autocorr]
        values2 = df[df['cohort'] == '2'][autocorr]
        print(f'Spatial autocorrelation for {channel}+')
        compare(values1, values2, expected_fold=fold, show_pvalue=True, show_auc=True)

    for channel, fold in zip(['CD20', 'PDL1'], [2.467, 0.136]):
        df = access.neighborhood_enrichment([p(channel), p(channel)])
        ne = f'neighborhood enrichment, {channel}+ and {channel}+'
        values1 = df[df['cohort'] == '1'][ne].dropna()
        values2 = df[df['cohort'] == '2'][ne].dropna()
        print(f'Neighborhood enrichment for {channel}+ and itself')
        compare(values2, values1, expected_fold=fold, show_pvalue=True, do_log_fold=True, show_auc=True)


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
