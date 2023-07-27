"""Count cells for a specific signature, over the specially-created binary-format index."""

from typing import Any

from spatialprofilingtoolbox.ondemand.providers import Provider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CountsProvider(Provider):
    """Scan binary-format expression matrices for specific signatures."""

    def __init__(self, data_directory: str, load_centroids: bool = False) -> None:
        """Load from a precomputed JSON artifact in the data directory.

        Note: CountsProvider never loads centroids because it does not need them.
        """
        super().__init__(data_directory, False)

    def compute_signature(self, channel_names: list[str], study_name: str) -> int:
        """Compute int signature of this channel name combination."""
        target_by_symbol = self.studies[study_name]['target by symbol']
        target_index_lookup = self.studies[study_name]['target index lookup']
        if not all(name in target_by_symbol.keys() for name in channel_names):
            return None
        identifiers = [target_by_symbol[name] for name in channel_names]
        indices = [target_index_lookup[identifier]
                   for identifier in identifiers]
        signature = 0
        for index in indices:
            signature = signature + (1 << index)
        return signature

    def count_structures_of_exact_signature(
        self,
        signature: int,
        study_name: str,
    ) -> dict[str, list[int]]:
        """Count the number of structures that have this exact channel signature."""
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = (data_array['entry'] == signature).sum()
            # count = 0
            # for entry in data_array:
            #     if entry == signature:
            #         count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def count_structures_of_partial_signature(
        self,
        signature: int,
        study_name: str,
    ) -> dict[str, list[int]]:
        """Count the number of structures that have part of this channel signature."""
        counts = {}
        for specimen, data_array in self.data_arrays[study_name].items():
            count = 0
            for entry in data_array['entry']:
                if entry | signature == entry:
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

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
            for entry in data_array['entry']:
                if (entry | positives_signature == entry) and \
                        (~entry | negatives_signature == ~entry):
                    count = count + 1
            counts[specimen] = [count, len(data_array)]
        return counts

    def get_status(self) -> list[dict[str, Any]]:
        """Get the status of all studies."""
        return [
            {
                'study': study_name,
                'counts by channel': [
                    {
                        'channel symbol': symbol,
                        'count': self.count_structures_of_partial_signed_signature(
                            [symbol], [], study_name),
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
