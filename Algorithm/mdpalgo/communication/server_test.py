'''
Rapsberry Pi serves as socket server, Algorithm will need a client socket script
as well to establish connection. Should be able to send and receive messages
via the server/client.
This script is used to test the RPi server.
'''

import socket
import threading
import mdpalgo.constants as constants

FORMAT = "UTF-8"
ALGO_SOCKET_BUFFER_SIZE = 1024

class Algorithm:
    def __init__(self):
        print("[Algo] Initialising Algorithm Process")

        self.host = constants.RPI_IP
        self.port = constants.PORT

        self.address = None
        self.client_socket = None
        self.server_socket = None

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        print(f"[Algo] Server Address at: {self.host}:{self.port}")

    def connect(self):
        while True:
            try:
                print(f'[Algo] Accepting Connection to: {self.host}:{self.port}]')
                if self.client_socket is None:
                    self.client_socket, self.address = self.server_socket.accept()
                    print(f'[Algo] Connected to Algoritmh Server at {self.host}:{self.port}')
                    t2 = threading.Thread(target=self.recv_process)
                    t2.start()
                    break

            except Exception as error:
                print(f'[Algo] Failed to setup connection for Algorithm Server at {self.host}:{self.port}')
                self.error_message(error)
                if self.client_socket is not None:
                    self.client_socket.close()
                    self.client_socket = None

            print(f'[Algo] Retrying for a connection to {self.host}:{self.port}')

    def disconnect(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            print(f'[Algo] Disconnected Algorithm Client from Server')

        except Exception as error:
            print(f'[[Algo] Failed to disconnect Algorithm Client from Server')
            self.error_message(error)

    def disconnect_all(self):
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None

            if self.server_socket is not None:
                self.server_socket.close()
                self.server_socket = None

            print(f'[Algo] Disconnected Algorithm sockets')

        except Exception as error:
            print(f'[Algo] Failed to disconnect Algorithm sockets')
            self.error_message(error)

    def recv(self):
        try:
            message = self.client_socket.recv(ALGO_SOCKET_BUFFER_SIZE).strip()
            if len(message) > 0:
                print(f'[Algo] Receive Message from Algo Client: {message}')
                return message
            return None

        except Exception as error:
            print("[Algo] Failed to receive message from Algo Client.")
            self.error_message(error)
            raise error

    def send(self, message):
        try:
            print(f'[Algo] Message to Algo Client: {message}')
            self.client_socket.sendall(message)

        except Exception as error:
            print("[Algo] Failed to send to Algo Client.")
            self.error_message(error)
            raise error

    def error_message(self, message):
        print(f"[Error Message]: {message}")

    def recv_process(self):
        while True:
            recieved = server.recv()
            if recieved is not None:
                print(f"[Server] Received message from client: {recieved}")

if __name__ == '__main__':
    server = Algorithm()
    server.connect()
    # Only allows sending of a single message per execution, to make it clearer what is returned to the server for the command
    # This is because input is a blocking call, and will prevent the worker thread from printing
    message = input("[Server] Send Message to client: ")
    server.send(message.encode(FORMAT))

