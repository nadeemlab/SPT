import re
import socket


class CountRequester:
    def __init__(self, host, port):
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect((host, port))

    def get_count(self, partial_signature_channels, study_name):
        query = self.form_query(self.sanitize_token(partial_signature_channels), study_name)
        self.tcp_client.sendall(query)
        return self.get_bytes_of_int64_response()

    def form_query(partial_signature_channels, study_name):
        return self.get_record_separator().join(
            [study_name] + partial_signature_channels
        ).encode('utf-8')

    def get_bytes_of_int64_response(self):
        received = self.tcp_client.recv(8)
        return int.from_bytes(received, 'little')

    def sanitize_token(text):
        return re.sub(CountRequest.get_record_separator(), ' ', text)

    def get_record_separator():
        return chr(30)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.tcp_client.close()
