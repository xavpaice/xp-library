#!/usr/bin/env python3
import socket
import platform

UDP_IP = "0.0.0.0"
UDP_PORT = 9090


sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)
    response = '%s: HELLO, I AM ALIVE!!!\n' % platform.node()
    sent = sock.sendto(response.encode(), addr)
