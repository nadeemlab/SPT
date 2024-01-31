"""Initialize the graph-transformer workflow components."""

from spatialprofilingtoolbox.workflow.common.graph_plugin_training_init import (
    create_process_inputs,
    assets_needed,
)
from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules


process_inputs = create_process_inputs(
    'nadeemlab/spt-graph-transformer:0.0.1',
    cuda_required=True,
)


components = WorkflowModules(
    is_database_visitor=True,
    assets_needed=assets_needed,
    config_section_required=True,
    process_inputs=process_inputs,
)
