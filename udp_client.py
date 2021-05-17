#!/usr/bin/env python3
import socket
import sys

MESSAGE = "This is the a msg from the clinet".encode()
sockout = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def one_time_tx_rx(OUT_IP, OUT_PORT):
    sockout.sendto(MESSAGE, (OUT_IP, OUT_PORT))
    msgFromServer = sockout.recvfrom(1024)
    print(msgFromServer[0])


if __name__ == "__main__":
    one_time_tx_rx(sys.argv[1], int(sys.argv[2]))
