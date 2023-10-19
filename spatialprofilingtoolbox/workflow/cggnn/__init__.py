"""Initialize the CGGNN workflow components.

(The components aren't actually used, but are being kept in case the pattern is changed to match
the visitors)
"""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules

# None of this is actually used except for the bool flags.
components = WorkflowModules(
    is_database_visitor=True,
)
