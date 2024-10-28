import re

from squidpy import __version__ as version_squidpy
from pandas import __version__ as version_pandas
from numpy import __version__ as version_numpy
from scipy import __version__ as version_scipy
from sklearn import __version__ as version_sklearn
from umap import __version__ as version_umap

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import SoftwareComponentVersion
from spatialprofilingtoolbox import __version__

def _get_postgres_version() -> str | None:
    with DBCursor() as cursor:
        cursor.execute('SELECT version();')
        text = tuple(cursor.fetchall())[0][0]
    match = re.search('^PostgreSQL (\d+).(\d+) ', text)
    if not match:
        return None
    return '.'.join(list(match.groups()))

PG_VERSION = str(_get_postgres_version())

def get_software_component_versions() -> list[SoftwareComponentVersion]:
    V = SoftwareComponentVersion
    versions = []
    def append(*v):
        versions.append(V(
            component_name=v[0],
            format=v[1],
            source=v[2],
            relevant_to_reproducible_computation=v[3],
            version=v[4])
        )
    py = 'Python package'
    pypi = 'Python package index (PyPI)'
    append('Squidpy', py, pypi, True, version_squidpy)
    append('Pandas', py, pypi, True, version_pandas)
    append('NumPy', py, pypi, True, version_numpy)
    append('SciPy', py, pypi, True, version_scipy)
    append('scikit-learn', py, pypi, True, version_sklearn)
    append('umap-learn', py, pypi, True, version_umap)
    append('spatialprofilingtoolbox', py, pypi, True, __version__)
    append('PostgreSQL', 'Database', 'Amazon RDS-managed', False, PG_VERSION)
    return versions
