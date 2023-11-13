"""The integration phase of the proximity workflow."""


from spatialprofilingtoolbox.workflow.component_interfaces.integrator import Integrator


class GraphGenerationIntegrator(Integrator):
    """The main class of the integration phase."""

    def calculate(self, **kwargs):
        pass
