"""The TCP client for the fast cell counts service."""
import re
import json
import socket


class CountRequester:
    """TCP client for requesting counts from the fast cell counts service."""
    def __init__(self, host, port):
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((host, port))

    def get_counts_by_specimen(
            self, positive_signature_channels, negative_signature_channels, study_name):
        query = self.form_query(
            [self.sanitize_token(c) for c in positive_signature_channels],
            [self.sanitize_token(c) for c in negative_signature_channels],
            self.sanitize_token(study_name),
        )
        self.tcp_client.sendall(query)
        return self.parse_response()

    def form_query(self, positive_signature_channels, negative_signature_channels, study_name):
        group1 = study_name
        group2 = self.get_record_separator().join(positive_signature_channels)
        group3 = self.get_record_separator().join(negative_signature_channels)
        return self.get_group_separator().join([group1, group2, group3]).encode('utf-8')

    def parse_response(self):
        received = None
        buffer = bytearray()
        bytelimit = 100000
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
