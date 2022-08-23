import re
import json
import socket


class CountRequester:
    def __init__(self, host, port):
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((host, port))

    def get_counts(self, partial_signature_channels, study_name):
        query = self.form_query([self.sanitize_token(c) for c in partial_signature_channels], self.sanitize_token(study_name))
        self.tcp_client.sendall(query)
        return self.get_counts_by_specimen()

    def form_query(self, partial_signature_channels, study_name):
        return self.get_record_separator().join(
            [study_name] + partial_signature_channels
        ).encode('utf-8')

    def get_counts_by_specimen(self):
        received = None
        buffer = bytearray()
        bytelimit = 100000
        while (not received in [self.get_end_of_transmission(), '']) and (len(buffer) < bytelimit):
            if not received is None:
                buffer.extend(received)
            received = self.tcp_client.recv(1)
        return json.loads(buffer.decode('utf-8'))

    def sanitize_token(self, text):
        return re.sub(self.get_record_separator(), ' ', text)

    def get_record_separator(self):
        return chr(30)

    def get_end_of_transmission(self):
        return bytes([4])

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.tcp_client.close()
