"""The fast cell counts service."""
__version__ = '0.9.0'

squidpy_feature_classnames_descriptions = {
    'neighorhood enrichment': 'x',
    'co-occurrence': 'y',
    'ripley': 'z',
}

# Calculates nhood_enrichment, co_occurrence, and ripley from squidpy.gr using clusters derived
# from the phenotypes provided. Reference db.squidpy_metrics.convert_df_to_anndata for the
# clustering method.
