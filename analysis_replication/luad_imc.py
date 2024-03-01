"""Data analysis script for one dataset."""
import sys

from numpy import inf

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

def test(host):
    study = 'LUAD progression'
    access = DataAccessor(study, host=host)

    df = access.spatial_autocorrelation('B cell')
    values1 = df[df['cohort'] == '1']['spatial autocorrelation, B cell']
    values2 = df[df['cohort'] == '2']['spatial autocorrelation, B cell']
    compare(values1, values2, expected_fold=1.513, show_pvalue=True)

    df = access.neighborhood_enrichment(['CD163+ macrophage', 'Regulatory T cell'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
    compare(values1, values2, expected_fold=467.1, do_log_fold=True, show_pvalue=True)

    df = access.neighborhood_enrichment(['CD163+ macrophage', 'Endothelial cell'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
    compare(values1, values2, expected_fold=5.336, do_log_fold=True, show_pvalue=True)

    klrd1 = {'positive_markers': ['KLRD1'], 'negative_markers': []}
    cd14 = {'positive_markers': ['CD14'], 'negative_markers': []}
    cd14_fcgr3a = {'positive_markers': ['CD14', 'FCGR3A'], 'negative_markers': []}

    df = access.counts([klrd1, cd14, cd14_fcgr3a])
    fractions = df['KLRD1+'] / df['CD14+ FCGR3A+']
    fractions = fractions[fractions != inf]
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions1, fractions2, expected_fold=4.56, show_pvalue=True)

    fractions = df['KLRD1+'] / df['CD14+']
    fractions = fractions[fractions != inf]
    fractions1 = fractions[df['cohort'] == '1']
    fractions2 = fractions[df['cohort'] == '2']
    compare(fractions1, fractions2, expected_fold=3.78, show_pvalue=True)

if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
