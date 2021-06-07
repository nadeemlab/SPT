
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

def get_design(workflow=None, **kwargs):
    """
    Exposes design parameters to scripts or API users.
    """
    if workflow in workflows:
        return workflows[workflow].design(**kwargs)
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
    if workflow in workflows:
        return workflows[workflow].integrator(**kwargs)
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
