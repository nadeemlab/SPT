"""The fast cell counts service."""
__version__ = '0.9.0'

squidpy_feature_classnames_descriptions = {
    'neighborhood enrichment': '''
        For two given cell phenotypes (first and second specifier), the z-score of the number of occurrences of neighbor relations between two cells of the given respective phenotypes, the z-score computed in reference to a bootstrapped empirical distribution constructed using 1000 random permutations of the cell set with labels fixed.
    '''.lstrip().rstrip(),
    'co-occurrence': 'y',
    'ripley': 'z',
}

# Calculates nhood_enrichment, co_occurrence, and ripley from squidpy.gr using clusters derived
# from the phenotypes provided. Reference db.squidpy_metrics.convert_df_to_anndata for the
# clustering method.
