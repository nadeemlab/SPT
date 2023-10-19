""""""

from spatialprofilingtoolbox.workflow.component_interfaces.initializer import Initializer


class CGGNNInitializer(Initializer):  # pylint: disable=too-few-public-methods
    """Initial job for the CG GNN training workflow. Currently no such initialization is done."""

    def initialize(self, **kwargs):
        pass
