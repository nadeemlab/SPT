"""Lookup the formal descriptions of the feature derivation methods for features computed by SPT."""

from importlib.resources import as_file
from importlib.resources import files
from csv import reader as csv_reader


def get_feature_description(handle: str) -> str:
    _file = files('spatialprofilingtoolbox.db.data_model').joinpath('feature_descriptions.tsv')
    with as_file(_file) as path:
        with open(path, 'rt', encoding='utf-8') as file:
            reader = csv_reader(file, delimiter='\t')
            descriptions = {row[0] : row[1] for row in reader}
    return descriptions[handle]


def squidpy_feature_classnames() -> tuple[str, ...]:
    return ('neighborhood enrichment', 'co-occurrence', 'ripley', 'spatial autocorrelation')
