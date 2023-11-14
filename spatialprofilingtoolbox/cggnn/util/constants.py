"""Consistent names for dict field strings."""

from typing import Literal

INDICES = 'histological_structure'
FEATURES = 'features'
CENTROIDS = 'centroid'
IMPORTANCES = 'importance'
SETS = ('train', 'validation', 'test')
SETS_type = Literal['train', 'validation', 'test']
