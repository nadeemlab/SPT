"""Initialize the CG-GNN workflow components."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules


def process_inputs(params: dict[str, str | bool]) -> None:
    """Ensure that the necessary input parameters are specified."""
    for param in ('default_docker_image', 'network', 'graph_config_file'):
        if param not in params:
            raise ValueError(f'Must specify {param}.')
    for param in ('cuda', 'upload_importances'):
        if param not in params:
            params[param] = False
        else:
            try:
                params[param] = bool(params[param])
            except ValueError:
                raise ValueError(f'{param} must be true or false if provided.')


components = WorkflowModules(
    is_database_visitor=True,
    config_section_required=True,
    process_inputs=process_inputs,
)
