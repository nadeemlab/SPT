"""Data analysis script for one dataset."""
import sys

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'Melanoma CyTOF ICI'
    access = DataAccessor(study, host=host)

    name1 = 'Cytotoxic T cell antigen-experienced'
    name2 = 'Melanoma'

    print('Not especially statistically significant, but matches prior finding:')
    df = access.proximity([name1, name2])
    prox = f'proximity, {name1} and {name2}'
    print(f'Proximity of {name1} to {name2}')
    values1 = df[df['cohort'] == '1'][prox]
    values2 = df[df['cohort'] == '2'][prox]
    compare(values1, values2, expected_fold=1.66, show_pvalue=True, show_auc=True)

    df = access.proximity([name2, name1])
    prox = f'proximity, {name2} and {name1}'
    print(f'Proximity of {name2} to {name1}')
    values1 = df[df['cohort'] == '1'][prox]
    values2 = df[df['cohort'] == '2'][prox]
    compare(values1, values2, expected_fold=1.34, show_pvalue=True, show_auc=True)

    df = access.neighborhood_enrichment([name1, name2])
    ne = f'neighborhood enrichment, {name1} and {name2}'
    print(f'Neighborhood enrichment for {name1} w.r.t. {name2}.')
    values1 = df[df['cohort'] == '1'][ne]
    values2 = df[df['cohort'] == '2'][ne]
    compare(values1, values2, expected_fold=0.75, show_pvalue=True)

    df = access.neighborhood_enrichment([name2, name1])
    ne = f'neighborhood enrichment, {name2} and {name1}'
    print(f'Neighborhood enrichment for {name2} w.r.t. {name1}.')
    values1 = df[df['cohort'] == '1'][ne]
    values2 = df[df['cohort'] == '2'][ne]
    compare(values1, values2, expected_fold=0.405, show_pvalue=True)

    # Two phenotypes spatial
    print('\nResults involving spatial metrics for 2 phenotypes (shown in both orders for reference)')
    for p1, p2, fold in zip(
        ['Cytotoxic T cell antigen-experienced', 'T regulatory cells', 'Cytotoxic T cell antigen-experienced', 'Naive cytotoxic T cell'],
        ['T regulatory cells', 'Cytotoxic T cell antigen-experienced', 'Naive cytotoxic T cell', 'Cytotoxic T cell antigen-experienced'],
        [0.285, 0.369, 0.299, 0.5],
    ):
        df = access.neighborhood_enrichment([p1, p2])
        ne = f'neighborhood enrichment, {p1} and {p2}'
        values1 = df[df['cohort'] == '1'][ne].dropna()
        values2 = df[df['cohort'] == '2'][ne].dropna()
        print(f'Neighborhood enrichment for {p1} and {p2}')
        compare(values1, values2, expected_fold=fold, show_pvalue=True, do_log_fold=True, show_auc=True)

    for p1, p2, fold in zip(
        ['Naive cytotoxic T cell', 'T regulatory cells', 'Naive cytotoxic T cell', 'T helper cell antigen-experienced'],
        ['T regulatory cells', 'Naive cytotoxic T cell', 'T helper cell antigen-experienced', 'Naive cytotoxic T cell'],
        [0.683, 0.417, 0.899, 0.400],
    ):
        df = access.proximity([p1, p2])
        prox = f'proximity, {p1} and {p2}'
        print(f'Proximity of {p1} to {p2}')
        values1 = df[df['cohort'] == '1'][prox]
        values2 = df[df['cohort'] == '2'][prox]
        compare(values1, values2, expected_fold=fold, show_pvalue=True, show_auc=True)

    print('\nSingle channel or phenotype results')

    def p(channel):
        return {'positive_markers':[channel], 'negative_markers':[]}

    CD3CD45RO = {'positive_markers': ['CD3', 'CD45RO'], 'negative_markers': []}
    name = 'CD3+ CD45RO+'
    fold = 0.0008
    df = access.neighborhood_enrichment([CD3CD45RO, CD3CD45RO])
    ne = f'neighborhood enrichment, {name} and {name}'
    values1 = df[df['cohort'] == '1'][ne].dropna()
    values2 = df[df['cohort'] == '2'][ne].dropna()
    print(f'Neighborhood enrichment for {name} and itself')
    compare(values1, values2, expected_fold=fold, show_pvalue=True, do_log_fold=True, show_auc=True)

    ### Channel
    for channel, fold in zip(['ICOS'], [0.791]):
        df = access.proximity([p(channel), p(channel)])
        prox = f'proximity, {channel}+ and {channel}+'
        print(f'Proximity of {channel} to {channel}')
        values1 = df[df['cohort'] == '1'][prox]
        values2 = df[df['cohort'] == '2'][prox]
        compare(values1, values2, expected_fold=fold, show_pvalue=True, show_auc=True)

    ### Phenotype
    for phenotype, fold in zip(['B cells'], [0.0826]):
        df = access.spatial_autocorrelation(phenotype)
        autocorr = f'spatial autocorrelation, {phenotype}'
        values1 = df[df['cohort'] == '1'][autocorr]
        values2 = df[df['cohort'] == '2'][autocorr]
        print(f'Spatial autocorrelation for {phenotype}')
        compare(values1, values2, expected_fold=fold, show_pvalue=True, show_auc=True)

    for phenotype, fold in zip(['T helper cell antigen-experienced', 'Cytotoxic T cell antigen-experienced'], [12.42, 0.278]):
        df = access.neighborhood_enrichment([phenotype, phenotype])
        ne = f'neighborhood enrichment, {phenotype} and {phenotype}'
        values1 = df[df['cohort'] == '1'][ne].dropna()
        values2 = df[df['cohort'] == '2'][ne].dropna()
        print(f'Neighborhood enrichment for {phenotype} and itself')
        compare(values1, values2, expected_fold=fold, show_pvalue=True, do_log_fold=True, show_auc=True)


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
