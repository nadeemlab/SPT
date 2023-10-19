"""Initialize the CGGNN workflow components.

(The components aren't actually used, but are being kept in case the pattern is changed to match
the visitors)
"""


from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules

from spatialprofilingtoolbox.workflow.cggnn.core import CGGNNCoreJob
from spatialprofilingtoolbox.workflow.cggnn.integrator import CGGNNIntegrator
from spatialprofilingtoolbox.workflow.cggnn.initializer import CGGNNInitializer
from spatialprofilingtoolbox.workflow.cggnn.job_generator import CGGNNJobGenerator

# None of this is actually used except for the bool flags.
components = WorkflowModules(
    is_database_visitor=True,
    generator=CGGNNCoreJob,
    initializer=CGGNNIntegrator,
    core_job=CGGNNInitializer,
    integrator=CGGNNJobGenerator,
    is_cggnn=True,
)
