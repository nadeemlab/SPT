"""Data analysis script for one dataset."""
import sys

from numpy import inf
from pandas import DataFrame

from accessors import DataAccessor
from accessors import get_default_host
from accessors import univariate_pair_compare as compare

class Assessor:
    df: DataFrame

    def __init__(self, df: DataFrame):
        self.df = df

    def handle_fractions(self, fractions, expected_fold: float) -> None:
        fractions = fractions[fractions != inf]
        fractions1 = fractions[self.df['cohort'] == '1']
        fractions2 = fractions[self.df['cohort'] == '2']
        compare(fractions1, fractions2, expected_fold=expected_fold, show_pvalue=True, show_auc=True)

def test(host):
    study = 'LUAD progression'
    access = DataAccessor(study, host=host)

    df = access.spatial_autocorrelation('B cell')
    values1 = df[df['cohort'] == '1']['spatial autocorrelation, B cell']
    values2 = df[df['cohort'] == '2']['spatial autocorrelation, B cell']
    compare(values1, values2, expected_fold=1.478, show_pvalue=True)

    df = access.neighborhood_enrichment(['CD163+ macrophage', 'Regulatory T cell'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
    compare(values1, values2, expected_fold=2.99, do_log_fold=True, show_pvalue=True)

    df = access.neighborhood_enrichment(['CD163+ macrophage', 'Endothelial cell'])
    values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
    values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
    compare(values1, values2, expected_fold=2.312, do_log_fold=True, show_pvalue=True)

    klrd1_fcgr3a = {'positive_markers': ['KLRD1', 'FCGR3A'], 'negative_markers': []}
    kit_fcgr3a = {'positive_markers': ['KIT', 'FCGR3A'], 'negative_markers': []}

    df = access.counts([klrd1_fcgr3a, kit_fcgr3a])
    Assessor(df).handle_fractions(df['KLRD1+ FCGR3A+'] / df['KIT+ FCGR3A+'], 1/2.07)


if __name__=='__main__':
    host: str | None
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = get_default_host(None)
    if host is None:
        raise RuntimeError('Could not determine API server.')
    test(host)
