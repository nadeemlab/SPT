"""Data analysis script for one dataset."""

import sys

from numpy import mean
from numpy import inf

from accessors import DataAccessor

study = 'LUAD progression'
if len(sys.argv) == 1:
    access = DataAccessor(study)
else:
    access = DataAccessor(study, host=sys.argv[1])


df = access.spatial_autocorrelation('B cell')
values1 = df[df['cohort'] == '1']['spatial autocorrelation, B cell']
values2 = df[df['cohort'] == '2']['spatial autocorrelation, B cell']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean2, mean1, mean2 / mean1))

df = access.neighborhood_enrichment(['CD163+ macrophage', 'Regulatory T cell'])
values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Regulatory T cell']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean2, mean1, mean2 / mean1))

df = access.neighborhood_enrichment(['CD163+ macrophage', 'Endothelial cell'])
values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD163+ macrophage and Endothelial cell']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean2, mean1, mean2 / mean1))

klrd1 = {'positive_markers': ['KLRD1'], 'negative_markers': []}
cd14 = {'positive_markers': ['CD14'], 'negative_markers': []}
cd14_fcgr3a = {'positive_markers': ['CD14', 'FCGR3A'], 'negative_markers': []}

df = access.counts([klrd1, cd14, cd14_fcgr3a])
fractions = df['KLRD1+'] / df['CD14+ FCGR3A+']
fractions = fractions[fractions != inf]
fractions1 = fractions[df['cohort'] == '1']
fractions2 = fractions[df['cohort'] == '2']
mean1 = mean(fractions1)
mean2 = mean(fractions2)
print((mean2, mean1, mean2 / mean1))

fractions = df['KLRD1+'] / df['CD14+']
fractions = fractions[fractions != inf]
fractions1 = fractions[df['cohort'] == '1']
fractions2 = fractions[df['cohort'] == '2']
mean1 = mean(fractions1)
mean2 = mean(fractions2)
print((mean2, mean1, mean2 / mean1))