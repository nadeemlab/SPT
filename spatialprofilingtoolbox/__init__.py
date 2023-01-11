import re
import pkgutil

from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger
from spatialprofilingtoolbox.standalone_utilities.configuration_settings import get_version
from spatialprofilingtoolbox.workflow import get_workflow
from spatialprofilingtoolbox.workflow import get_workflow_names as get_workflow_names  # pylint: disable=useless-import-alias


def get_subpackage_name(module_info):
    name = re.sub(r'^spatialprofilingtoolbox\.?', '', module_info.name)
    if '.' in name:
        return ''
    return name


submodule_names = [
    get_subpackage_name(module_info)
    for module_info in pkgutil.walk_packages(__path__)
    if module_info.ispkg and get_subpackage_name(module_info) != ''
]


logger = colorized_logger(__name__)

__version__ = get_version()


def get_dataset_design(workflow=None, **kwargs):
    return get_workflow(workflow).dataset_design(**kwargs)


def get_computational_design(workflow=None, **kwargs):
    ComputationalDesign = get_workflow(workflow).computational_design
    dataset_design = get_dataset_design(workflow=workflow, **kwargs)
    computational_design = ComputationalDesign(
        dataset_design=dataset_design, **kwargs)
    return computational_design


def get_initializer(workflow=None, **kwargs):
    dataset_design = get_dataset_design(workflow=workflow, **kwargs)
    computational_design = get_computational_design(
        workflow=workflow, **kwargs)
    Initializer = get_workflow(workflow).initializer
    return Initializer(
        dataset_design=dataset_design,
        computational_design=computational_design,
        **kwargs,
    )


def get_core_job(workflow=None, **kwargs):
    dataset_design = get_dataset_design(workflow=workflow, **kwargs)
    computational_design = get_computational_design(
        workflow=workflow, **kwargs)
    CoreJob = get_workflow(workflow).core_job
    return CoreJob(
        dataset_design=dataset_design,
        computational_design=computational_design,
        **kwargs,
    )


def get_integrator(workflow=None, **kwargs):
    computational_design = get_computational_design(
        workflow=workflow, **kwargs)

    Integrator = get_workflow(workflow).integrator
    return Integrator(
        computational_design=computational_design,
        **kwargs,
    )
