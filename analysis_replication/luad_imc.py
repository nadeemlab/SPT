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
print(df)
values1 = df[df['cohort'] == '1']['B cell']
values2 = df[df['cohort'] == '2']['B cell']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean2, mean1, mean2 / mean1))


df = access.neighborhood_enrichment(['CD163+ macrophage', 'Regulatory T cell'])
values1 = df[df['cohort'] == '1']['CD163+ macrophage and Regulatory T cell']
values2 = df[df['cohort'] == '2']['CD163+ macrophage and Regulatory T cell']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean2, mean1, mean2 / mean1))


# df = access.proximity([KRT['14'], KRT['7']])
# values1 = df[df['cohort'] == '1']['proximity, KRT14+ CK+ and KRT7+ CK+']
# values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT7+ CK+']
# mean1 = mean(values1)
# mean2 = mean(values2)
# print((mean2, mean1, mean2 / mean1))

# df = access.proximity([KRT['14'], KRT['5']])
# values2 = df[df['cohort'] == '2']['proximity, KRT14+ CK+ and KRT5+ CK+']
# values3 = df[df['cohort'] == '3']['proximity, KRT14+ CK+ and KRT5+ CK+']
# mean2 = mean(values2)
# mean3 = mean(values3)
# print((mean2, mean3, mean2 / mean3))

# df = access.counts([KRT['14'], KRT['7']])
# fractions = df['KRT14+ CK+ and KRT7+ CK+'] / df['all cells']
# print(mean(fractions))


# df = access.counts([KRT['14'], KRT['5']])
# fractions = df['KRT14+ CK+ and KRT5+ CK+'] / df['all cells']
# print(mean(fractions))

# df = access.counts([KRT['14'], KRT['19']])
# fractions = df['KRT14+ CK+'] / df['KRT19+ CK+']
# fractions = fractions[fractions != inf]
# fractions1 = fractions[df['cohort'] == '1']
# fractions2 = fractions[df['cohort'] == '2']
# fractions3 = fractions[df['cohort'] == '3']
# mean1 = mean(fractions1)
# mean2 = mean(fractions2)
# mean3 = mean(fractions3)
# print((mean2, mean3, mean2 / mean3))
# print((mean2, mean1, mean2 / mean1))
