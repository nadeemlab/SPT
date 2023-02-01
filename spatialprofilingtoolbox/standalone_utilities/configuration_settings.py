"""Configuration settings."""
from importlib.metadata import version


def get_version():
    return version('spatialprofilingtoolbox')
