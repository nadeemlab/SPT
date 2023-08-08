"""Custom TCP server for on demand metrics."""

from socketserver import TCPServer, BaseRequestHandler

from attr import define

from spatialprofilingtoolbox.ondemand.providers import (
    CountsProvider,
    ProximityProvider,
    SquidpyProvider,
)


@define
class OnDemandProviderSet:
    """Gather together the set/collection of ondemand providers."""
    counts: CountsProvider
    proximity: ProximityProvider
    squidpy: SquidpyProvider


class OnDemandTCPServer(TCPServer):
    """Custom TCP server for on demand metrics."""

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseRequestHandler],
        providers: OnDemandProviderSet,
    ) -> None:
        """Create a custom TCP server for on demand metrics."""
        TCPServer.__init__(self, server_address, request_handler_class)
        self.providers = providers
