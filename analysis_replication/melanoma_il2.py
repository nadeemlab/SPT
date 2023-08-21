"""Data analysis script for one dataset."""

import sys

from numpy import mean

from accessors import DataAccessor

study = 'Melanoma intralesional IL2'
if len(sys.argv) == 1:
    access = DataAccessor(study)
else:
    access = DataAccessor(study, host=sys.argv[1])

exhausted = {'positive_markers': ['KI67', 'PD1', 'LAG3', 'TIM3'], 'negative_markers': []}
df = access.counts(['CD8+ T cell', exhausted])

fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['all cells']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))

df = df.combine_first(access.counts(['CD8+ T cell']))
fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['CD8+ T cell']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))

mhci = {'positive_markers': ['MHCI'], 'negative_markers': []}
df = access.counts(['Tumor', mhci])
df = df.combine_first(access.counts(['Tumor']))
fractions = df['Tumor and MHCI+'] / df['Tumor']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))
