"""Custom TCP server for on demand metrics."""

from socketserver import TCPServer, BaseRequestHandler

from attr import define

from spatialprofilingtoolbox.ondemand.providers.counts_provider import CountsProvider
from spatialprofilingtoolbox.ondemand.providers.proximity_provider import ProximityProvider
from spatialprofilingtoolbox.ondemand.providers.squidpy_provider import SquidpyProvider


@define
class OnDemandProviderSet:
    """Gather together the set/collection of ondemand providers."""
    counts: CountsProvider | None
    proximity: ProximityProvider | None
    squidpy: SquidpyProvider | None


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
