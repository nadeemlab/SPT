
from squidpy import __version__ as version_squidpy
from pandas import __version__ as version_pandas
from numpy import __version__ as version_numpy
from scipy import __version__ as version_scipy
from sklearn import __version__ as version_sklearn
from umap import __version__ as version_umap

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import SoftwareComponentVersion

def get_software_component_versions() -> list[SoftwareComponentVersion]:
    V = SoftwareComponentVersion
    versions = []
    versions.append(V(component_name='Squidpy python package', version=version_squidpy))
    versions.append(V(component_name='Pandas python package', version=version_pandas))
    versions.append(V(component_name='NumPy python package', version=version_numpy))
    versions.append(V(component_name='SciPy python package', version=version_scipy))
    versions.append(V(component_name='scikit-learn python package', version=version_sklearn))
    versions.append(V(component_name='umap-learn python package', version=version_umap))
    return versions
