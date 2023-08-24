"""Data analysis script for one dataset."""

import sys

from numpy import mean

from accessors import DataAccessor

study = 'Melanoma CyTOF ICI'
if len(sys.argv) == 1:
    access = DataAccessor(study)
else:
    access = DataAccessor(study, host=sys.argv[1])

antigen_experienced_cytotoxic = {'positive_markers': ['CD8A', 'CD3', 'CD45RO'], 'negative_markers': []}
proliferative = {'positive_markers': ['MKI67'], 'negative_markers': []}
df = access.counts([antigen_experienced_cytotoxic, proliferative])
print(df)

# On average, the fraction of cells that are CD8A+ CD3+ CD45RO+ and MKI67+ is 1.41 times higher
# in cohort 1 than in cohort 2.
fractions = df['CD8A+ CD3+ CD45RO+ and MKI67+'] / df['all cells']
fractions1 = fractions[df['cohort'] == '1']
fractions2 = fractions[df['cohort'] == '2']
mean1 = mean(fractions1)
mean2 = mean(fractions2)
print((mean1, mean2, mean1 / mean2))

print('')

df = access.neighborhood_enrichment([antigen_experienced_cytotoxic, 'Melanoma'])
print(df)
values1 = df[df['cohort'] == '1']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
values2 = df[df['cohort'] == '2']['neighborhood enrichment, CD8A+ CD3+ CD45RO+ and Melanoma']
mean1 = mean(values1)
mean2 = mean(values2)
print((mean1, mean2, mean1 / mean2))
