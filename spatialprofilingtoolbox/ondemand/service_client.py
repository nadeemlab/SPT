"""TCP client for on demand metrics service."""

import re
import json
import socket
import os

from spatialprofilingtoolbox.db.exchange_data_formats.metrics import (
    PhenotypeCriteria,
    PhenotypeCount,
    PhenotypeCounts,
    CompositePhenotype,
    UnivariateMetricsComputationResult,
)
from spatialprofilingtoolbox.standalone_utilities.log_formats import colorized_logger

logger = colorized_logger(__name__)


class OnDemandRequester:
    """TCP client for requesting from the on-demand service."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        service: str | None = None,
    ):
        _host, _port = None, None
        if host is None and port is None:
            _host, _port = self._get_ondemand_host_port(service=service)
        if host is not None:
            _host = host
        if port is not None:
            _port = port
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((_host, _port))

    def get_counts_by_specimen(
        self,
        positive_signature_channels: list[str],
        negative_signature_channels: list[str],
        study_name: str,
        number_cells: int,
        cells_selected: set[int] | None = None,
    ) -> PhenotypeCounts:
        query = self._form_counts_query(
            [self._sanitize_token(c) for c in positive_signature_channels],
            [self._sanitize_token(c) for c in negative_signature_channels],
            self._sanitize_token(study_name),
            None if (cells_selected is None) else [str(c) for c in cells_selected],
        )
        self.tcp_client.sendall(query)
        logger.debug('Query to counts service: %s', query)
        response = self._parse_response()
        return PhenotypeCounts(
            counts=[
                PhenotypeCount(
                    specimen=specimen,
                    count=count,
                    percentage=self._fancy_round(count / count_all_in_specimen)
                    if ((count is not None) and (count_all_in_specimen not in {0, None})) else None,
                )
                for specimen, (count, count_all_in_specimen) in response.items()
            ],
            phenotype=CompositePhenotype(
                name='',
                identifier='',
                criteria=PhenotypeCriteria(
                    positive_markers=positive_signature_channels,
                    negative_markers=negative_signature_channels,
                ),
            ),
            number_cells_in_study=number_cells,
        )

    @staticmethod
    def _fancy_round(ratio: float) -> float:
        return 100 * round(ratio * 10000)/10000

    def get_proximity_metrics(
        self,
        study: str,
        radius: float,
        signature: tuple[list[str], list[str], list[str], list[str]]
    ) -> UnivariateMetricsComputationResult:
        positives1, negatives1, positives2, negatives2 = signature
        separator = self._get_record_separator()
        groups = [
            'proximity',
            self._sanitize_token(study),
            str(radius),
            separator.join([self._sanitize_token(c) for c in positives1]),
            separator.join([self._sanitize_token(c) for c in negatives1]),
            separator.join([self._sanitize_token(c) for c in positives2]),
            separator.join([self._sanitize_token(c) for c in negatives2]),
        ]
        query = self._get_group_separator().join(groups).encode('utf-8')
        self.tcp_client.sendall(query)
        response = self._parse_response()
        return UnivariateMetricsComputationResult(
            values=response['metrics'],
            is_pending=response['pending'],
        )

    def _form_counts_query(
        self,
        positive_signature_channels: list[str],
        negative_signature_channels: list[str],
        study_name: str,
        cells_selected: list[str] | None = None,
    ) -> bytes:
        group1 = study_name
        group2 = self._get_record_separator().join(positive_signature_channels)
        group3 = self._get_record_separator().join(negative_signature_channels)
        return self._get_group_separator().join(
            ['counts', group1, group2, group3] + (
                [] if (cells_selected is None) else
                [self._get_record_separator().join(cells_selected)]
            )
        ).encode('utf-8')

    def _parse_response(self):
        received = None
        buffer = bytearray()
        bytelimit = 10000000
        while (not received in [self._get_end_of_transmission(), '']) and (len(buffer) < bytelimit):
            if not received is None:
                buffer.extend(received)
            received = self.tcp_client.recv(1)
        return json.loads(buffer.decode('utf-8'))

    def _sanitize_token(self, text: str) -> str:
        return re.sub(
            '[' + self._get_record_separator() + self._get_group_separator() + ']', ' ', text)

    def _get_group_separator(self):
        return chr(29)

    def _get_record_separator(self):
        return chr(30)

    def _get_end_of_transmission(self):
        return bytes([4])

    def get_squidpy_metrics(
        self,
        study: str,
        signature: list[list[str]],
        feature_class: str,
        radius: float | None = None,
    ) -> UnivariateMetricsComputationResult:
        """Get spatial proximity statistics between phenotype clusters as calculated by Squidpy."""
        if not len(signature) in {2, 4}:
            message = f'Expected 2 or 4 channel lists (1 or 2 phenotypes) but got {len(signature)}.'
            raise ValueError(message)
        separator = self._get_record_separator()
        groups = [feature_class, self._sanitize_token(study)]
        groups.extend(separator.join([self._sanitize_token(c) for c in s]) for s in signature)
        if feature_class == 'co-occurrence':
            if radius is None:
                raise ValueError('You must supply a radius value.')
            groups = groups + [str(radius)]
        query = self._get_group_separator().join(groups).encode('utf-8')
        self.tcp_client.sendall(query)
        response = self._parse_response()
        return UnivariateMetricsComputationResult(
            values=response['metrics'],
            is_pending=response['pending'],
        )

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.tcp_client.close()

    @staticmethod
    def _get_ondemand_host_port(service: str | None = None):
        host = None
        port = None
        if service is not None:
            host_variable = f'{service.upper()}_HOST'
            port_variable = f'{service.upper()}_PORT'
            if host_variable in os.environ and port_variable in os.environ:
                host = os.environ[host_variable]
                port = int(os.environ[port_variable])
        if host is None or port is None:
            host_variable = 'ONDEMAND_HOST'
            port_variable = 'ONDEMAND_PORT'
            if host_variable in os.environ and port_variable in os.environ:
                host = os.environ[host_variable]
                port = int(os.environ[port_variable])
        if host is None or port is None:
            message = 'Specify ONDEMAND_HOST and ONDEMAND_PORT or else a specific service variant.'
            raise EnvironmentError(message)
        logger.debug('Host and port (with service "%s"): %s', service, (host, port))
        return (host, port)
