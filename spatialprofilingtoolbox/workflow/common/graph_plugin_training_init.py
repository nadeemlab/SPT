"""Set up graph plugin workflow components."""

from typing import Callable

TRUEY = ('true', 't', 'yes', 'y', '1')
FALSY = ('false', 'f', 'no', 'n', '0')


def create_process_inputs(
    image_template: str,
    cuda_required: bool = False,
) -> Callable[[dict[str, str | bool]], None]:
    """Return a function to process input parameters for the graph plugin workflow.

    Parameters
    ----------
    image_template: str
        The name of the Docker Hub image to use for the workflow. If the workflow has both CUDA and
        non-CUDA versions, template should include a `{cuda}` placeholder that can be replaced with
        the .format() method.
    cuda_required: bool = False
        Whether the workflow requires CUDA. If True, the `cuda` parameter will be set to True if
        not specified in the configuration file and an error will be raised if it is set to False.
    """
    def process_inputs(params: dict[str, str | bool]) -> None:
        """Ensure that the necessary input parameters are specified."""
        for param in ('graph_config_file', ):
            if param not in params:
                raise ValueError(f'Must specify {param}.')
        if cuda_required and (params['cuda'] in FALSY):
            raise ValueError('This workflow requires CUDA, but it was set to False.')
        for param in ('cuda', 'upload_importances'):
            if param not in params:
                params[param] = cuda_required
            else:
                if params[param] in TRUEY:
                    params[param] = True
                elif params[param] in FALSY:
                    params[param] = False
                else:
                    raise ValueError(f'{param} must be true or false if provided.')
        if params['container_platform'] not in {'docker', 'singularity'}:
            raise ValueError(
                'For the cg-gnn workflow, the container_platform must be either `docker` or '
                f'`singularity`, not `{params["container_platform"]}`.')
        params['graph_plugin_image'] = \
            image_template.format(cuda="cuda-" if params["cuda"] else "")
        params['graph_plugin_singularity_run_options'] = '--nv' if \
            ((params['container_platform'] == 'singularity') and params['cuda']) else ''
    return process_inputs


assets_needed: list[tuple[str, str, bool]] = [
    ('graph_generation', 'graph_generation.nf', False),
    ('assets', 'upload_importance_scores.nf', False),
    ('assets', 'graph_plugin_training.nf', True),
]
