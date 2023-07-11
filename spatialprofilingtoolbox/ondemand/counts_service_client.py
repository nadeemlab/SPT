"""The TCP client for the fast cell counts service."""
import re
import json
import socket
import os

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCriteria
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCount
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import PhenotypeCounts
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import CompositePhenotype
from spatialprofilingtoolbox.db.exchange_data_formats.metrics import \
    ProximityMetricsComputationResult


class CountRequester:
    """TCP client for requesting counts from the fast cell counts service."""
    def __init__(self, host: str | None=None, port: int | None=None):
        _host, _port = None, None
        if host is None and port is None:
            _host, _port = self.get_ondemand_host_port()
        if host is not None:
            _host = host
        if port is not None:
            _port = port
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((_host, _port))

    def get_counts_by_specimen(self,
            positive_signature_channels: list[str],
            negative_signature_channels: list[str],
            study_name: str,
            number_cells: int,
        ) -> PhenotypeCounts:
        query = self.form_query(
            [self.sanitize_token(c) for c in positive_signature_channels],
            [self.sanitize_token(c) for c in negative_signature_channels],
            self.sanitize_token(study_name),
        )
        self.tcp_client.sendall(query)
        response = self.parse_response()
        return PhenotypeCounts(
            counts=[
                PhenotypeCount(
                    specimen=specimen,
                    count=count,
                    percentage=self.fancy_round(count / count_all_in_specimen)
                )
                for specimen, (count, count_all_in_specimen) in response.items()
            ],
            phenotype=CompositePhenotype(
                name=None,
                identifier=None,
                criteria=PhenotypeCriteria(
                    positive_markers=positive_signature_channels,
                    negative_markers=negative_signature_channels,
                ),
            ),
            number_cells_in_study=number_cells,
        )

    @staticmethod
    def fancy_round(ratio):
        return 100 * round(ratio * 10000)/10000

    def get_proximity_metrics(self, study, radius, signature) -> ProximityMetricsComputationResult:
        positives1, negatives1, positives2, negatives2 = signature
        separator = self.get_record_separator()
        groups = [
            self.sanitize_token(study),
            str(radius),
            separator.join([self.sanitize_token(c) for c in positives1]),
            separator.join([self.sanitize_token(c) for c in negatives1]),
            separator.join([self.sanitize_token(c) for c in positives2]),
            separator.join([self.sanitize_token(c) for c in negatives2]),
        ]
        query = self.get_group_separator().join(groups).encode('utf-8')
        self.tcp_client.sendall(query)
        response = self.parse_response()
        return ProximityMetricsComputationResult(
            values = response['metrics'],
            is_pending=response['pending'],
        )

    def form_query(self, positive_signature_channels, negative_signature_channels, study_name):
        group1 = study_name
        group2 = self.get_record_separator().join(positive_signature_channels)
        group3 = self.get_record_separator().join(negative_signature_channels)
        return self.get_group_separator().join([group1, group2, group3]).encode('utf-8')

    def parse_response(self):
        received = None
        buffer = bytearray()
        bytelimit = 1000000
        while (not received in [self.get_end_of_transmission(), '']) and (len(buffer) < bytelimit):
            if not received is None:
                buffer.extend(received)
            received = self.tcp_client.recv(1)
        return json.loads(buffer.decode('utf-8'))

    def sanitize_token(self, text):
        return re.sub('[' + self.get_record_separator() + self.get_group_separator() + ']', ' ',
                      text)

    def get_group_separator(self):
        return chr(29)

    def get_record_separator(self):
        return chr(30)

    def get_end_of_transmission(self):
        return bytes([4])

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.tcp_client.close()

    @staticmethod
    def get_ondemand_host_port():
        host = os.environ['COUNTS_SERVER_HOST']
        port = int(os.environ['COUNTS_SERVER_PORT'])
        return (host, port)
