""""""


from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules

from spatialprofilingtoolbox.cggnn.run.core import CGGNNCoreJob
from spatialprofilingtoolbox.cggnn.run.integrator import CGGNNIntegrator
from spatialprofilingtoolbox.cggnn.run.initializer import CGGNNInitializer
from spatialprofilingtoolbox.cggnn.run.job_generator import CGGNNJobGenerator

components = WorkflowModules(
    is_database_visitor=True,
    generator=CGGNNCoreJob,
    initializer=CGGNNIntegrator,
    core_job=CGGNNInitializer,
    integrator=CGGNNJobGenerator,
)
