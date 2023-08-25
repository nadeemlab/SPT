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
print(df)

# On average, the fraction of cells that are CD8+ T cells and KI67+ LAG3+ PD1+ TIM3+ is 24.51
# times higher in cohort 3 than in cohort 1.
fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['all cells']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))

# On average, the ratio of the number of cells that are CD8+ T cells and KI67+ LAG3+ PD1+ TIM3+
# to those that are CD8+ T cells is 6.29 times higher in cohort 3 than in cohort 1.
fractions = df['CD8+ T cell and KI67+ PD1+ LAG3+ TIM3+'] / df['CD8+ T cell']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))

print('')

mhci = {'positive_markers': ['MHCI'], 'negative_markers': []}
df = access.counts(['Tumor', mhci])
print(df)

# On average, the ratio of the number of cells that are MHCI+ and Tumor to those that are Tumor
# is 1.86 times higher in cohort 3 than in cohort 1.
fractions = df['Tumor and MHCI+'] / df['Tumor']
fractions1 = fractions[df['cohort'] == '1']
fractions3 = fractions[df['cohort'] == '3']
mean1 = mean(fractions1)
mean3 = mean(fractions3)
print((mean3, mean1, mean3 / mean1))

# The average value of the proximity score for phenotype(s) B cells is 3.59 times higher in
# cohort 3 than in cohort 1.
df = access.proximity(['B cell', 'B cell'])
print(df)
values1 = df[df['cohort'] == '1']['proximity, B cell and B cell']
values3 = df[df['cohort'] == '3']['proximity, B cell and B cell']
mean1 = mean(values1)
mean3 = mean(values3)
print((mean3, mean1, mean3 / mean1))

# The average value of the neighborhood enrichment score for phenotype(s) B cells is 80.45 times
# higher in cohort 1 than in cohort 3.
df = access.neighborhood_enrichment(['B cell', 'B cell'])
print(df)
values1 = df[df['cohort'] == '1']['neighborhood enrichment, B cell and B cell']
values3 = df[df['cohort'] == '3']['neighborhood enrichment, B cell and B cell']
mean1 = mean(values1)
mean3 = mean(values3)
print((mean1, mean3, mean1 / mean3))
