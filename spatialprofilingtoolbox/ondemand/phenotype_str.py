"""Helper functions for translating phenotype definition strings."""
from ast import literal_eval

def phenotype_to_phenotype_str(phenotype):
    return str( (tuple(phenotype['positive']), tuple(phenotype['negative'])) )

def phenotype_str_to_phenotype(phenotype_str):
    parts = literal_eval(phenotype_str)
    return {'positive': parts[0], 'negative': parts[1]}
