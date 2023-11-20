"""Handler for requests for on demand calculations."""

from socketserver import BaseRequestHandler
from json import dumps

from spatialprofilingtoolbox.db.database_connection import DBCursor
from spatialprofilingtoolbox.db.accessors.study import StudyAccess
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.providers.provider import OnDemandProvider
from spatialprofilingtoolbox.ondemand.tcp_server import OnDemandTCPServer
from spatialprofilingtoolbox.db.describe_features import squidpy_feature_classnames
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandRequestHandler(BaseRequestHandler):
    """TCP server for on demand metrics."""

    server: OnDemandTCPServer

    def handle(self):
        """Handle an on demand request."""
        try:
            self._handle()
        except Exception as exception:
            logger.error('Unhandled exception in on demand service.')
            self._send_error_response()
            raise exception

    def _handle(self) -> None:
        """Handle an on demand request."""
        data: bytes = self.request.recv(1000000).strip()
        logger.info('Request: %s', data)
        if self._handle_empty_body(data):
            return
        request_class, groups = self._get_request_class_and_groups(data)
        handled = False
        match request_class:
            case 'counts':
                if self.server.providers.counts is None:
                    self._send_error_response()
                    return
                handled = self._handle_single_phenotype_counts_request(groups)
            case 'proximity':
                if self.server.providers.proximity is None:
                    self._send_error_response()
                    return
                handled = self._handle_proximity_request(groups)
            case _:
                pass
        if not handled:
            if request_class in squidpy_feature_classnames():
                if self.server.providers.squidpy is None:
                    self._send_error_response()
                    return
                handled = self._handle_squidpy_request(request_class, groups)
        if not handled:
            self._send_error_response()

    @staticmethod
    def _get_request_class_and_groups(data: bytes) -> tuple[str, list[str]]:
        group_separator = chr(29)
        components = data.decode('utf-8').split(group_separator)
        return components[0], components[1:]

    def _handle_single_phenotype_counts_request(self, groups: list[str]) -> bool:
        if len(groups) not in {3, 4}:
            return False
        specification = self._get_phenotype_counts_spec(groups)
        study_name = specification[0]
        if self._handle_missing_study(study_name):
            return True

        positives_signature, negatives_signature = self._get_signatures(
            study_name,
            specification[1],
            specification[2],
        )
        if self._handle_unparseable_signature(positives_signature, specification[1]):
            return True
        if self._handle_unparseable_signature(negatives_signature, specification[2]):
            return True
        assert (positives_signature is not None) and (negatives_signature is not None)

        counts = self._get_counts(
            study_name,
            positives_signature,
            negatives_signature,
            specification[3],
        )
        message = dumps(counts) + self._get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def _get_counts(
        self,
        study: str,
        positives_signature: int,
        negatives_signature: int,
        cells_selected: set[int] | None = None,
    ) -> dict[str, tuple[int, int] | tuple[None, None]]:
        assert self.server.providers.counts is not None
        measurement_study = self._get_measurement_study(study)
        return self.server.providers.counts.count_structures_of_partial_signed_signature(
            positives_signature,
            negatives_signature,
            measurement_study,
            tuple(sorted(list(cells_selected))) if cells_selected else None,
        )

    def _handle_unparseable_signature(self, signature: int | None, names: list[str]) -> bool:
        if signature is None:
            logger.error('Could not understand channel names as defining a signature: %s', names)
            self._wrap_up_transmission()
            return True
        return False

    def _get_signatures(
        self,
        study_name: str,
        positives: list[str],
        negatives: list[str],
    ) -> tuple[int | None, int | None]:
        assert self.server.providers.counts is not None
        measurement_study_name = self._get_measurement_study(study_name)
        signature1 = self.server.providers.counts.compute_signature(positives, measurement_study_name)
        signature2 = self.server.providers.counts.compute_signature(negatives, measurement_study_name)
        logger.info('Signature: %s, %s', signature1, signature2)
        return signature1, signature2

    def _get_measurement_study(self, study: str) -> str:
        with DBCursor(study=study) as cursor:
            return StudyAccess(cursor).get_study_components(study).measurement

    def _handle_missing_study(self, study_name: str) -> bool:
        measurement_study_name = self._get_measurement_study(study_name)
        if self._get_default_provider().has_study(measurement_study_name):
            return False
        logger.error('Study not known to ondemand service: %s', study_name)
        self._wrap_up_transmission()
        return True

    def _get_phenotype_counts_spec(
        self,
        groups: list[str],
    ) -> tuple[str, list[str], list[str], set[int] | None]:
        record_separator = chr(30)
        study_name = groups[0]
        positive_channel_names = groups[1].split(record_separator)
        negative_channel_names = groups[2].split(record_separator)
        positive_channel_names = self._trim_empty_entry(positive_channel_names)
        negative_channel_names = self._trim_empty_entry(negative_channel_names)
        logger.info('Study: %s', study_name)
        logger.info('Positives: %s', positive_channel_names)
        logger.info('Negatives: %s', negative_channel_names)
        if len(groups) == 4 and groups[3] != '':
            cells_selected = {int(s) for s in groups[3].split(record_separator)}
            logger.info('Cells selected: %s', cells_selected)
        else:
            cells_selected = None
        return study_name, positive_channel_names, negative_channel_names, cells_selected

    def _handle_proximity_request(self, groups):
        if len(groups) != 6:
            return False
        specification = self._get_phenotype_pair_specification(groups)
        study_name = specification[0]
        if self._handle_missing_study(study_name):
            return True

        try:
            metrics = self._get_proximity_metrics(*specification)
        except Exception as exception:
            message = "Error response." + self._get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            raise exception

        message = dumps(metrics) + self._get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def _get_proximity_metrics(self, study, radius, signature):
        assert self.server.providers.proximity is not None
        positives1, negatives1, positives2, negatives2 = signature
        phenotype1 = PhenotypeCriteria(positive_markers=positives1, negative_markers=negatives1)
        phenotype2 = PhenotypeCriteria(positive_markers=positives2, negative_markers=negatives2)
        return self.server.providers.proximity.get_metrics(
            study,
            phenotype1=phenotype1,
            phenotype2=phenotype2,
            radius=radius,
        )

    def _get_phenotype_pair_specification(self, groups):
        record_separator = chr(30)
        study_name = groups[0]
        radius = float(groups[1])
        channel_lists = [
            self._trim_empty_entry(group.split(record_separator))
            for group in groups[2:6]
        ]
        return [study_name, radius, channel_lists]

    def _handle_squidpy_request(self, feature_class, groups):
        logger.debug(groups)
        match feature_class:
            case 'neighborhood enrichment':
                if len(groups) != 4 + 1:
                    return False
            case 'co-occurrence':
                if len(groups) != 4 + 1 + 1:
                    return False
            case 'ripley':
                if len(groups) != 2 + 1:
                    return False
        study = groups[0]
        radius = None
        if feature_class == 'co-occurrence':
            radius = float(groups[5])
            groups = groups[0:5]
        if self._handle_missing_study(study):
            return True

        channel_lists = self._get_long_phenotype_spec(groups[1:])
        try:
            metrics = self._get_squidpy_metrics(study, feature_class, channel_lists, radius=radius)
        except Exception as exception:
            message = "Error response." + self._get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            raise exception

        message = dumps(metrics) + self._get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def _get_long_phenotype_spec(self, channel_lists_raw: list[str]) -> list[list[str]]:
        record_separator = chr(30)
        return [
            self._trim_empty_entry(phenotype.split(record_separator))
            for phenotype in channel_lists_raw
        ]

    def _get_squidpy_metrics(
        self,
        study: str,
        feature_class: str,
        channel_lists: list[list[str]],
        radius: float | None = None,
    ) -> dict[str, dict[str, float | None] | bool]:
        assert self.server.providers.squidpy is not None
        phenotypes: list[PhenotypeCriteria] = []
        for i in range(len(channel_lists)//2):
            phenotypes.append(PhenotypeCriteria(
                positive_markers=channel_lists[2*i],
                negative_markers=channel_lists[2*i+1],
            ))
        return self.server.providers.squidpy.get_metrics(
            study,
            feature_class=feature_class,
            phenotypes=phenotypes,
            radius=radius,
        )

    def _handle_empty_body(self, data: bytes) -> bool:
        if data == b'':
            logger.info('Empty body. Serving status.')
            status = dumps(self._get_default_provider().get_status(), indent=4)
            message = status + self._get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            return True
        return False

    def _send_error_response(self):
        message = 'Query to on-demand computation service could not be handled.'
        logger.info(message)
        message = dumps({'error': message}) + self._get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))

    def _wrap_up_transmission(self):
        self.request.sendall(self._get_end_of_transmission().encode('utf-8'))

    @staticmethod
    def _get_end_of_transmission():
        return chr(4)

    @staticmethod
    def _trim_empty_entry(element: list[str]) -> list[str]:
        if element == ['']:
            return []
        return element

    def _get_default_provider(self) -> OnDemandProvider:
        if self.server.providers.counts is not None:
            return self.server.providers.counts
        if self.server.providers.proximity is not None:
            return self.server.providers.proximity
        if self.server.providers.squidpy is not None:
            return self.server.providers.squidpy
        raise RuntimeError('No provider available.')
