"""Wrapper class for describing the components of a given workflow."""

from typing import NamedTuple, Callable, Type

from spatialprofilingtoolbox.workflow.component_interfaces import (
    JobGenerator,
    Initializer,
    CoreJob,
    Integrator,
)


class WorkflowModules(NamedTuple):
    """A wrapper object in which to list implementation classes comprising a workflow definition.
    
    Parameters
    ----------
    is_database_visitor: bool
        Whether the workflow is a database visitor.
    assets_needed: list[tuple[str, str]]
        What file assets the workflow needs. The first tuple entry is the directory inside
        `spatialprofilingtoolbox.workflow` that contains the asset (using period separators like
        in Python imports), and the second is the filename of the asset. One of the filenames must
        be `main.nf`, which is the entry point for the workflow. All other files will be copied to
        a subdirectory `nf_files` at configuration time; make sure to write includes in your
        Nextflow files to reflect this runtime directory structure if you're using them.
    generator: Type[JobGenerator] | None = None
    initializer: Type[Initializer] | None = None
    core_job: Type[CoreJob] | None = None
    integrator: Type[Integrator] | None = None
    config_section_required: bool = False
        Whether the workflow requires a custom config file section.
    process_inputs: Callable[[dict[str, str | bool]], None] = lambda _: None
        A function to process input parameters from the general and workflow-specific sections
        of the configuration file.
    image: str = 'nadeemlab/spt'
        The name of the Docker Hub image to use for the workflow.
    """
    is_database_visitor: bool
    assets_needed: list[tuple[str, str]]
    generator: Type[JobGenerator] | None = None
    initializer: Type[Initializer] | None = None
    core_job: Type[CoreJob] | None = None
    integrator: Type[Integrator] | None = None
    config_section_required: bool = False
    process_inputs: Callable[[dict[str, str | bool]], None] = lambda _: None
    image: str = 'nadeemlab/spt'
