
from .environment.settings_wrappers import JobsPaths, DatasetSettings
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
        elementary_phenotypes_file = kwargs['elementary_phenotypes_file']
        complex_phenotypes_file = kwargs['complex_phenotypes_file']
        del kwargs['elementary_phenotypes_file']
        del kwargs['complex_phenotypes_file']

        DatasetDesign = get_dataset_design(workflow = workflow)
        Analyzer = workflows[workflow].analyzer
        return Analyzer(
            dataset_design = DatasetDesign(
                elementary_phenotypes_file,
            ),
            complex_phenotypes_file = complex_phenotypes_file,
            **kwargs,
        )
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
        DatasetDesign = get_dataset_design(workflow = workflow)
        ComputationalDesign = get_computational_design(worklow = workflow)
        Integrator = workflows[workflow].integrator
        return Integrator(
            jobs_paths = JobsPaths(
                kwargs['job_working_directory'],
                kwargs['jobs_path'],
                kwargs['logs_path'],
                kwargs['schedulers_path'],
                kwargs['output_path'],
            ),
            dataset_settings = DatasetSettings(
                kwargs['input_path'],
                kwargs['file_manifest_file'],
                kwargs['outcomes_file'],
            ),
            computational_design = ComputationalDesign(
                dataset_design = DatasetDesign(
                    kwargs['elementary_phenotypes_file'],
                ),
                complex_phenotypes_file = kwargs['complex_phenotypes_file'],
            ),
        )
    else:
        logger.error('Workflow "%s" not supported.', str(workflow))
        raise TypeError
