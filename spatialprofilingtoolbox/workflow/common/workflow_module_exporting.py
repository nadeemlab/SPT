"""Wrapper class for describing the components of a given workflow."""

from typing import NamedTuple, Callable, Type

from spatialprofilingtoolbox.workflow.component_interfaces import (
    JobGenerator,
    Initializer,
    CoreJob,
    Integrator,
)


class WorkflowModules(NamedTuple):
    """A wrapper object in which to list implementation classes comprising a workflow definition."""
    is_database_visitor: bool
    generator: Type[JobGenerator] | None = None
    initializer: Type[Initializer] | None = None
    core_job: Type[CoreJob] | None = None
    integrator: Type[Integrator] | None = None
    config_section_required: bool = False
    process_inputs: Callable[[dict[str, str | bool]], None] = lambda _: None
