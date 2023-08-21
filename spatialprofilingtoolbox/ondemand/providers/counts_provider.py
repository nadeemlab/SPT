"""Count cells for a specific signature, over the specially-created binary-format index."""

from typing import Any
from typing import Iterable
from typing import cast
from spatialprofilingtoolbox.db.simple_method_cache import simple_instance_method_cache

from spatialprofilingtoolbox.ondemand.providers import OnDemandProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CountsProvider(OnDemandProvider):
    """Scan binary-format expression matrices for specific signatures."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from precomputed binary expression files and a JSON index in the data directory.

        Note: CountsProvider never loads centroids because it does not need them.
        """
        super().__init__(data_directory, False)

    @simple_instance_method_cache(maxsize=50000)
    def count_structures_of_partial_signed_signature(
        self,
        positives_signature: int,
        negatives_signature: int,
        study_name: str,
    ) -> dict[str, list[int]]:
        """Count the number of structures that part of this signature, in signs."""
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            if len(data_array) == 0:
                raise ValueError(f'Data array for specimen "{specimen}" is empty.')
            count = self.get_count(data_array['integer'], positives_signature, negatives_signature)
            counts[specimen] = [count, len(data_array)]
        return counts

    def get_count(self, integers: Iterable, positives_mask: int, negatives_mask: int) -> int:
        """Counts the number of elements of the list of integer-represented binary numbers which
        equal to 1 along the bits indicated by the positives mask, and equal to 0 along the bits
        indicated by the negatives mask.
        """
        count = 0
        for entry in integers:
            if (entry | positives_mask == entry) and (~entry | negatives_mask == ~entry):
                count = count + 1
        return count

    def compute_signature(self, channel_names: list[str], study_name: str) -> int | None:
        """Compute int signature of this channel name combination."""
        target_by_symbol = self.studies[study_name]['target by symbol']
        target_index_lookup = self.studies[study_name]['target index lookup']
        if not all(name in target_by_symbol.keys() for name in channel_names):
            return None
        identifiers = [target_by_symbol[name] for name in channel_names]
        indices = [target_index_lookup[identifier] for identifier in identifiers]
        signature = 0
        for index in indices:
            signature = signature + (1 << index)
        return signature

    def get_status(self) -> list[dict[str, Any]]:
        """Get the status of all studies."""
        return [
            {
                'study': study_name,
                'counts by channel': [
                    {
                        'channel symbol': symbol,
                        'count': self.count_structures_of_partial_signed_signature(
                            cast(int, self.compute_signature([cast(str, symbol)], study_name)),
                            cast(int, self.compute_signature([], study_name)),
                            study_name
                        ),
                    }
                    for symbol in sorted(list(targets['target by symbol'].keys()))
                ],
                'total number of cells': len(self.data_arrays[study_name]),
            }
            for study_name, targets in self.studies.items()
        ]

    def has_study(self, study_name: str) -> bool:
        """Check if this study is available in this provider."""
        return study_name in self.studies
