"""
Algorithm Socket to connect with RPi.
"""

from mdpalgo.constants import mdp_constants
from mdpalgo.image_rec import image_rec

import socket
import struct
import json
import cv2
import numpy as np
import base64
import os

FORMAT = "UTF-8"
ALGO_SOCKET_BUFFER_SIZE = 1024
MAX_MESSAGE_LENGTH_PRINT = 200  # above this value, most likely image


class AlgoClient:

    def __init__(self) -> None:
        print("[Algo Client] Initialising Algo Client.")
        self.client_socket = None
        # self.server_address = None
        self.server_ip = mdp_constants.GRP_14
        self.server_port = mdp_constants.PORT
        self.server_address = (self.server_ip, self.server_port)
        # self.set_server_address()
        print("[Algo Client] Client has been initilised.")

    # def set_server_address(self):
    #     self.server_address = (self.server_ip, self.server_port)

    def connect(self) -> bool:
        try:
            # Connect to RPI via TCP
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(self.server_address)
            print(f"[Algo Client] Client successfully connected to Server at {self.server_address}.")
            return True
        except Exception as error:
            print(f'[Algo] Failed to connect to Algorithm Server at {self.server_address}')
            print(f"[Error Message]: {error}")
            return False

    def disconnect(self) -> bool:
        try:
            if self.client_socket is not None:
                self.client_socket.close()
                self.client_socket = None
            return True
        except Exception as error:
            print(f'[Algo] Failed to disconnect from Algorithm Server at {self.server_address}')
            print(f"[Error Message]: {error}")
            return False

    def recv(self) -> str:
        try:
            # Decode : Converting from Byte to UTF-8 format.
            raw_bytes = self.receive_message_with_size()
            if raw_bytes is not None:
                message = self.decode(raw_bytes)
                # if (len(message) <= MAX_MESSAGE_LENGTH_PRINT):
                #     print(f'[Algo] Received Message from Algo Server: {message}')
                # else:
                #     print(f'[Algo] Received Long Message (likely image) from Algo Server. '
                #           f'First {MAX_MESSAGE_LENGTH_PRINT} characters: {message[:MAX_MESSAGE_LENGTH_PRINT]}')
                return message
            return None
        except Exception as error:
            print("[Algo] Failed to receive message from Algo Server.")
            print(f"[Error Message]: {error}")
            raise error

    def send(self, message):
        try:
            print(f'[Algo] Message to Algo Server: {message}')
            self.client_socket.sendall(self.encode(message))

        except Exception as error:
            print("[Algo] Failed to send to Algo Server.")
            print(f"[Error Message]: {error}")
            raise error

    def encode(self, message: str) -> bytes:
        """Encode a message to a byte array"""
        return message.encode()

    def decode(self, raw_bytes: bytes) -> str:
        """Decode a byte array to a string message"""
        return raw_bytes.strip().decode(FORMAT)

    def receive_message_with_size(self):
        """Receive the raw bytes from the message"""
        try:
            data = self.client_socket.recv(4)  # read the first 4 bytes (data length)
            if len(data) == 0:
                return None
            else:
                number_of_bytes = struct.unpack("!I", data)[0]  # convert 4 bytes into integer
                received_packets = b''
                bytes_to_receive = number_of_bytes
                while len(received_packets) < number_of_bytes:
                    packet = self.client_socket.recv(bytes_to_receive)
                    bytes_to_receive -= len(packet)
                    received_packets += packet
                return received_packets
        except socket.timeout:
            return None
        except:
            return None

def send_message(message):
    print(f"==SENDING {json.dumps(message)}")
    client.send(json.dumps(message))


def get_image_result(message_data): 
    if message_data["type"] == "IMAGE_TAKEN":
        image_data = message_data["data"]["image"]
        image_data = image_data.encode('utf-8')
        image_data = base64.b64decode(image_data)
        with open("test.jpg", "wb") as fh:
            fh.write(image_data)

        if os.path.isfile("test.jpg"):
            result = image_rec("test.jpg", save_path="output.jpg")
            if len(result["predictions"]) > 0:
                result_message = {
                    "type": "IMAGE_RESULTS",
                    "data": {
                        "obs_id": obs_id,
                        "img_id": result["predictions"][0]["class"]
                    }
                }
                return(result_message)

'''
GRP14: MINI-PROGRAM TO TEST CONNECTION BETWEEN RPI AND LAPTOP
'''
if __name__ == '__main__':
    client = AlgoClient()
    connect_status = client.connect()
    assert connect_status  # if the server is up, this should be true

    # import the libraries for parsing messages
    from message_parser import MessageParser, MessageType

    parser = MessageParser()
    obs_id = "00"

    # message = {
    #     "type": "GET_IMAGE",
    #     "data":{
    #         "obs_id": obs_id
    #     }
    # }
    forward_mess = {
        "type": "NAVIGATION",
        "data": {
            "commands": ['SF060'],
        }
    }
    
    send_message(forward_mess)
    recv = client.recv()
    result = get_image_result(json.loads(recv))
    print("result:", result)
    go_around_mess = {
        "type": "NAVIGATION",
        "data": {
            "commands": ['RB090', 'SF065', 'RF180']
        }
    }
    for i in range(3):
        if result is None:
            send_message(go_around_mess)
            recv = client.recv()
            result = get_image_result(json.loads(recv))

    


