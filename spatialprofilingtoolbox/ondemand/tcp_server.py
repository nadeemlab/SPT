"""Custom TCP server for on demand metrics."""

from socketserver import TCPServer, BaseRequestHandler

from spatialprofilingtoolbox.ondemand.providers import (
    CountsProvider,
    ProximityProvider,
    SquidpyProvider,
)

class OnDemandTCPServer(TCPServer):
    """Custom TCP server for on demand metrics."""

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseRequestHandler],
        counts_provider: CountsProvider,
        proximity_provider: ProximityProvider,
        squidpy_provider: SquidpyProvider,
    ) -> None:
        """Create a custom TCP server for on demand metrics."""
        TCPServer.__init__(self, server_address, request_handler_class)
        self.counts_provider = counts_provider
        self.proximity_provider = proximity_provider
        self.squidpy_provider = squidpy_provider
