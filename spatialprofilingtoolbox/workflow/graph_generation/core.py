"""Generate graphs from a single specimen."""

from spatialprofilingtoolbox.workflow.component_interfaces.core import CoreJob


class GraphGenerationCoreJob(CoreJob):
    """Core parallelizable functionality for the graph generation workflow."""

    def _calculate(self):
        pass
