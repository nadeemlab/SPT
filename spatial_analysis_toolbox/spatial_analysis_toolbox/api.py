
from .environment.configuration import workflows
from .environment.log_formats import colorized_logger

logger = colorized_logger(__name__)

def get_job_generator(workflow=None, **kwargs):
    """
    Exposes job generators to scripts or API users.
    """
    if workflow in workflows:
        return workflows[workflow].generator(**kwargs)
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_dataset_design(workflow=None):
    """
    Exposes design parameters to scripts or API users.
    """
    if workflow in workflows:
        return workflows[workflow].dataset_design
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_computational_design(workflow=None):
    """
    Exposes design parameters to scripts or API users.
    """
    if workflow in workflows:
        return workflows[workflow].computational_design
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_analyzer(workflow=None, **kwargs):
    """
    Exposes pipeline analyzers to scripts or API users.
    """
    if workflow in workflows:
        return workflows[workflow].analyzer(**kwargs)
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError

def get_integrator(workflow=None, **kwargs):
    """
    Exposes pipeline analysis integrators to scripts or API users.
    """
    # Consider pushing code like the below OUT of the constructors for the Analyzers etc., and into this "API" module ?
    # That way the implementation classes do not need to be aware of individual keyword arguments way up at the job generation/deployment level.
    if workflow in workflows:
        DatasetDesign = get_dataset_design(workflow=p['workflow'])
        ComputationalDesign = get_computational_design(worklow=p['workflow'])
        Integrator = workflows[workflow].integrator
        return Integrator(
            jobs_paths=JobsPaths(
                p['job_working_directory'],
                p['jobs_path'],
                p['logs_path'],
                p['schedulers_path'],
                p['output_path'],
            ),
            outcomes_file=p['outcomes_file'],
            computational_design=ComputationalDesign(
                dataset_design=DatasetDesign(
                    p['elementary_phenotypes_file'],
                ),
                complex_phenotypes_file = p['complex_phenotypes_file'],
            ),
        )
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
