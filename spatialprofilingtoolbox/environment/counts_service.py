import socket

class CountRequester:
    @staticmethod
    def get_count(partial_signature_channels):
        host_ip = '127.0.0.1'
        server_port = 8016
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            tcp_client.connect((host_ip, server_port))
            record_separator = chr(30)
            record = record_separator.join(partial_signature_channels)
            tcp_client.sendall(record.encode('utf-8'))
            received = tcp_client.recv(8)
        finally:
            tcp_client.close()
        return int.from_bytes(received, 'little')
