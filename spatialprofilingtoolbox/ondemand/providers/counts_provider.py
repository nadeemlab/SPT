"""Count cells for a specific signature, over the specially-created binary-format index."""

from typing import Any
from typing import cast

from pandas import Index

from spatialprofilingtoolbox.db.simple_method_cache import simple_instance_method_cache
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class CountsProvider(OnDemandProvider):
    """Scan binary-format expression matrices for specific signatures."""

    def __init__(self, timeout: int, database_config_file: str | None, load_centroids: bool = False) -> None:
        """Load from precomputed binary expression files and a JSON index in the data directory.

        Note: CountsProvider never loads centroids because it does not need them. It also does not
        using the pending system, so the timeout is irrelevant.
        """
        super().__init__(0, database_config_file)

    @classmethod
    def service_specifier(cls) -> str:
        return 'counts'

    # Feature specification stuff:

    # def _get_phenotype_counts_spec(
    #     self,
    #     groups: list[str],
    # ) -> tuple[str, list[str], list[str], set[int] | None]:
    #     study_name = groups[0]
    #     positive_channel_names = groups[1].split(RECORD_SEPARATOR)
    #     negative_channel_names = groups[2].split(RECORD_SEPARATOR)
    #     positive_channel_names = self._trim_empty_entry(positive_channel_names)
    #     negative_channel_names = self._trim_empty_entry(negative_channel_names)
    #     if len(groups) == 4 and groups[3] != '':
    #         cells_selected = {int(s) for s in groups[3].split(RECORD_SEPARATOR)}
    #         truncation: list[str | int] = list(cells_selected)
    #         if len(truncation) > 5:
    #             truncation = truncation[0:4] + [f'(... {len(cells_selected)} items)']
    #         logger.info('Cells selected: %s', str(truncation))
    #     else:
    #         cells_selected = None
    #     return study_name, positive_channel_names, negative_channel_names, cells_selected


    # def _handle_single_phenotype_counts_request(self) -> bool:

    #     specification = self._get_phenotype_counts_spec()
    #     study_name = specification[0]
    #     positive_channel_names = specification[1]
    #     negative_channel_names = specification[2]

    #     positives_signature, negatives_signature = self._get_signatures(
    #         study_name,
    #         specification[1],
    #         specification[2],
    #     )
    #     if self._handle_unparseable_signature(positives_signature, specification[1]):
    #         return True
    #     if self._handle_unparseable_signature(negatives_signature, specification[2]):
    #         return True
    #     assert (positives_signature is not None) and (negatives_signature is not None)

    #     counts = self._get_counts(
    #         study_name,
    #         positives_signature,
    #         negatives_signature,
    #         specification[3],
    #     )
    #     message = dumps(counts) + self._get_end_of_transmission()
    #     self.request.sendall(message.encode('utf-8'))
    #     return True

    # def _get_signatures(
    #     self,
    #     study_name: str,
    #     positives: list[str],
    #     negatives: list[str],
    # ) -> tuple[int | None, int | None]:
    #     assert self.server.providers.counts is not None
    #     measurement_study_name = self._get_measurement_study(study_name)
    #     signature1 = self.server.providers.counts.compute_signature(positives, measurement_study_name)
    #     signature2 = self.server.providers.counts.compute_signature(negatives, measurement_study_name)
    #     return signature1, signature2


    # Dispatch:

    # def _get_counts(
    #     self,
    #     study: str,
    #     positives_signature: int,
    #     negatives_signature: int,
    #     cells_selected: set[int] | None = None,
    # ) -> dict[str, tuple[int, int] | tuple[None, None]]:
    #     assert self.server.providers.counts is not None
    #     measurement_study = self._get_measurement_study(study)
    #     return self.server.providers.counts.count_structures_of_partial_signed_signature(
    #         positives_signature,
    #         negatives_signature,
    #         measurement_study,
    #         tuple(sorted(list(cells_selected))) if cells_selected else None,
    #     )


    @simple_instance_method_cache(maxsize=50000)
    def count_structures_of_partial_signed_signature(
        self,
        positives_signature: int,
        negatives_signature: int,
        measurement_study: str,
        cells_selected: tuple[int, ...] | None = None,
    ) -> dict[str, tuple[int, int] | tuple[None, None]]:
        """Count the number of structures per specimen that match this signature."""
        counts: dict[str, tuple[int, int] | tuple[None, None]] = {}
        selection = Index(list(cells_selected)) if cells_selected else None
        for specimen, data_array in self.data_arrays[measurement_study].items():
            count = 0
            if len(data_array) == 0:
                raise ValueError(f'Data array for specimen "{specimen}" is empty.')
            integers = cast(
                list[int],
                data_array['integer'] if (selection is None) else
                data_array.loc[data_array.index.intersection(selection), 'integer'],
            )
            if len(integers) == 0:
                counts[specimen] = (None, None)
                continue
            count = self.get_count(integers, positives_signature, negatives_signature)
            counts[specimen] = (count, len(integers))
        return counts

    def get_count(self, integers: list[int], positives_mask: int, negatives_mask: int) -> int:
        """Counts the number of elements of the list of integer-represented binary numbers which
        equal to 1 along the bits indicated by the positives mask, and equal to 0 along the bits
        indicated by the negatives mask.
        """
        count = 0
        for entry in integers:
            if (entry | positives_mask == entry) and (~entry | negatives_mask == ~entry):
                count = count + 1
        return count

    def compute_signature(self, channel_names: list[str], measurement_study: str) -> int | None:
        """Compute int signature of this channel name combination."""
        target_by_symbol = self.studies[measurement_study]['target by symbol']
        target_index_lookup = self.studies[measurement_study]['target index lookup']
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
