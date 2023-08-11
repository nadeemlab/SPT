"""The fast cell counts service."""
__version__ = '0.9.0'

squidpy_feature_classnames_descriptions = {
    'neighborhood enrichment': '''
        For two given cell phenotypes (first and second specifiers), the estimated p-value (CDF of z-score) of the number of occurrences of neighbor relations between two cells of the given respective phenotypes, the z-score computed in reference to a bootstrapped empirical distribution constructed using 1000 random permutations of the cell set with labels fixed.
    '''.lstrip().rstrip(),
    'co-occurrence': '''
        For two given cell phenotypes (first and second specifiers), and a given radius (third specifier), the ratio of the two probabilities of occurrence of the first phenotype within the given radius around some cell, calculated with and without conditioning on at least one occurrence of the second phenotype in the same radius.
    '''.lstrip().rstrip(),
    'ripley': '''
        For a given cell phenotype (first specifier), the p-value associated with the Ripley F-statistic for the point set of cell locations, at the radius scale for which this p-value is smallest.
    '''.lstrip().rstrip(),
}
