"""Initialize the CG-GNN workflow components."""

from spatialprofilingtoolbox.workflow.common.workflow_module_exporting import WorkflowModules

TRUEY = ('true', 't', 'yes', 'y', '1')
FALSY = ('false', 'f', 'no', 'n', '0')


def process_inputs(params: dict[str, str | bool]) -> None:
    """Ensure that the necessary input parameters are specified."""
    for param in ('default_docker_image', 'network', 'graph_config_file'):
        if param not in params:
            raise ValueError(f'Must specify {param}.')
    for param in ('cuda', 'upload_importances'):
        if param not in params:
            params[param] = False
        else:
            if params[param] in TRUEY:
                params[param] = True
            elif params[param] in FALSY:
                params[param] = False
            else:
                raise ValueError(f'{param} must be true or false if provided.')


components = WorkflowModules(
    is_database_visitor=True,
    config_section_required=True,
    process_inputs=process_inputs,
)
