#!/usr/bin/env python3

import socket

host_ip = '127.0.0.1'
server_port = 8016

# Initialize a TCP client socket using SOCK_STREAM
tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Establish connection to TCP server and exchange data
    tcp_client.connect((host_ip, server_port))

    data = input()
    tcp_client.sendall(data.encode())

    # Read data from the TCP server and close the connection
    received = tcp_client.recv(8)
finally:
    tcp_client.close()

print ("Bytes Sent:     {}".format(data))
print ("Bytes Received: {}".format(received.decode()))