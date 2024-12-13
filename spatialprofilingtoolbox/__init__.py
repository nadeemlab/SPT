"""Spatial Profiling Toolbox python package."""
import re
import warnings

from numba.core.errors import NumbaDeprecationWarning  # type: ignore

from spatialprofilingtoolbox.standalone_utilities.configuration_settings import get_version
from spatialprofilingtoolbox.workflow import get_workflow
from spatialprofilingtoolbox.workflow import get_workflow_names as get_workflow_names  # pylint: disable=useless-import-alias

warnings.simplefilter('ignore', category=NumbaDeprecationWarning)

from os.path import exists

def consider_print_build_timestamp():
    filename = '/build-date.txt'
    if exists(filename):
        with open(filename, 'rt', encoding='utf-8') as file:
            timestamp = file.read()
        print(f'Container built at: {timestamp}')

def get_subpackage_name(module_info):
    name = re.sub(r'^spatialprofilingtoolbox\.?', '', module_info.name)
    if '.' in name:
        return ''
    return name

submodule_names = ['apiserver', 'graphs', 'db', 'ondemand', 'workflow']

__version__ = get_version()


def get_initializer(workflow=None, **kwargs):
    return get_workflow(workflow).initializer(**kwargs)


def get_core_job(workflow=None, **kwargs):
    return get_workflow(workflow).core_job(**kwargs)


def get_integrator(workflow=None, **kwargs):
    return get_workflow(workflow).integrator(**kwargs)
