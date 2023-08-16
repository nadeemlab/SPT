"""Configuration settings."""
from importlib.metadata import version
from importlib.metadata import PackageNotFoundError
from warnings import warn

def get_version():
    _version = 'unknown'
    try:
        _version = version('spatialprofilingtoolbox')
    except PackageNotFoundError:
        warn('spatialprofilingtoolbox package is used but not installed.')
    return _version
