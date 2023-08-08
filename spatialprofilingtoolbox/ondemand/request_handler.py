"""Handler for requests for on demand calculations."""

from socketserver import BaseRequestHandler
from json import dumps

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.ondemand.tcp_server import OnDemandTCPServer
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger('spt ondemand start')


class OnDemandRequestHandler(BaseRequestHandler):
    """TCP server for on demand metrics."""

    server: OnDemandTCPServer

    def handle(self):
        """Handle an on demand request."""
        data = self.request.recv(512).strip()
        logger.info('Request: %s', data)
        if self._handle_empty_body(data):
            return
        if self._handle_single_phenotype_counts_request(data):
            return
        if self._handle_proximity_request(data):
            return
        if self._handle_squidpy_request(data):
            return

    def _handle_proximity_request(self, data):
        groups = self._get_groups(data)
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
        positives1, negatives1, positives2, negatives2 = signature
        phenotype1 = PhenotypeCriteria(positive_markers=positives1, negative_markers=negatives1)
        phenotype2 = PhenotypeCriteria(positive_markers=positives2, negative_markers=negatives2)
        return self.server.providers.proximity.get_metrics(
            study,
            phenotype1=phenotype1,
            phenotype2=phenotype2,
            radius=radius,
        )

    def _handle_single_phenotype_counts_request(self, data):
        groups = self._get_groups(data)
        if len(groups) != 3:
            return False
        specification = self._get_phenotype_spec(groups)
        study_name = specification[0]
        if self._handle_missing_study(study_name):
            return True

        positives_signature, negatives_signature = self._get_signatures(*specification)
        if self._handle_unparseable_signature(positives_signature, specification[1]):
            return True
        if self._handle_unparseable_signature(negatives_signature, specification[2]):
            return True

        counts = self._get_counts(study_name, positives_signature, negatives_signature)
        message = dumps(counts) + self._get_end_of_transmission()
        self.request.sendall(message.encode('utf-8'))
        return True

    def _get_counts(self, study, positives_signature, negatives_signature):
        arguments = [positives_signature, negatives_signature, study]
        return self.server.providers.counts.count_structures_of_partial_signed_signature(*arguments)

    def _handle_unparseable_signature(self, signature, names):
        if signature is None:
            logger.error('Could not understand channel names as defining a signature: %s', names)
            self._wrap_up_transmission()
            return True
        return False

    def _get_signatures(self, study_name, positives, negatives):
        signature1 = self.server.providers.counts.compute_signature(positives, study_name)
        signature2 = self.server.providers.counts.compute_signature(negatives, study_name)
        logger.info('Signature: %s, %s', signature1, signature2)
        return signature1, signature2

    def _handle_missing_study(self, study_name):
        if self.server.providers.counts.has_study(study_name):
            return False
        logger.error('Study not known to counts server: %s', study_name)
        self._wrap_up_transmission()
        return True

    def _get_phenotype_spec(self, groups):
        record_separator = chr(30)
        study_name = groups[0]
        positive_channel_names = groups[1].split(record_separator)
        negative_channel_names = groups[2].split(record_separator)
        positive_channel_names = self._trim_empty_entry(positive_channel_names)
        negative_channel_names = self._trim_empty_entry(negative_channel_names)
        logger.info('Study: %s', study_name)
        logger.info('Positives: %s', positive_channel_names)
        logger.info('Negatives: %s', negative_channel_names)
        return study_name, positive_channel_names, negative_channel_names

    def _get_phenotype_pair_specification(self, groups):
        record_separator = chr(30)
        study_name = groups[0]
        radius = int(groups[1])
        channel_lists = [
            self._trim_empty_entry(group.split(record_separator))
            for group in groups[2:6]
        ]
        return [study_name, radius, channel_lists]

    @staticmethod
    def _get_groups(data):
        group_separator = chr(29)
        return data.decode('utf-8').split(group_separator)

    def _handle_squidpy_request(self, data):
        groups = self._get_groups(data)
        if (len(groups) < 3) or (len(groups) % 2 != 0):
            return False
        study = groups[0]
        if self._handle_missing_study(study):
            return True

        channel_lists = self._get_long_phenotype_spec(groups[1:])
        try:
            metrics = self._get_squidpy_metrics(study, channel_lists)
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
            self._trim_empty_entry(phenotype.split(record_separator[1:]))
            for phenotype in channel_lists_raw
        ]

    def _get_squidpy_metrics(
        self,
        study: str,
        channel_lists: list[list[str]],
    ) -> dict[str, dict[str, float | None] | bool]:
        phenotypes: list[PhenotypeCriteria] = []
        for i in range(len(channel_lists)//2):
            phenotypes.append(PhenotypeCriteria(
                positive_markers=channel_lists[2*i],
                negative_markers=channel_lists[2*i+1],
            ))
        return self.server.providers.squidpy.get_metrics(study, phenotypes=phenotypes)

    def _handle_empty_body(self, data):
        if data == '':
            logger.info('Empty body. Serving status.')
            status = dumps(self.server.providers.counts.get_status(), indent=4)
            message = status + self._get_end_of_transmission()
            self.request.sendall(message.encode('utf-8'))
            return True
        return False

    def _wrap_up_transmission(self):
        self.request.sendall(self._get_end_of_transmission().encode('utf-8'))

    @staticmethod
    def _get_end_of_transmission():
        return chr(4)

    @staticmethod
    def _trim_empty_entry(element):
        if element == ['']:
            return []
        return element
