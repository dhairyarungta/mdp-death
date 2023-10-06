from queue import Queue
import socket
import sys
import json
import threading

from Camera import capture, preprocess_img 
import os
import base64

from rpi_config import *

class PCInterface:
    def __init__(self,RPiMain):
        self.RPiMain = RPiMain
        self.host = RPI_IP
        self.port = PC_PORT
        self.client_socket = None
        self.msg_queue = Queue()

    def connect(self):
        # 1. Solution for thread-related issues: always attempt to disconnect first before connecting
        self.disconnect()

        # 2. Wait and accept PC connection
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print("[PC] Socket established successfully.")
                sock.bind((self.host, self.port))
                sock.listen(128) # the maximum number of queued connections that the server can handle simultaneously

                print("[PC] Waiting for PC connection...")
                # with socket.timeout(30):
                self.client_socket, self.address = sock.accept()

        # Handle any errors that may occur during the connection attempt.
        except socket.error as e:
            print("[PC] ERROR: Failed to connect -", str(e))

        # Log the connection attempt.
        print("[PC] PC connected successfully:", self.address)
        
    def disconnect(self):
        try:
            if self.client_socket is not None: #TODO
                self.client_socket.close()
                self.client_socket = None
                print("[PC] Disconnected from PC successfully.")
        except Exception as e:
            print("[PC] Failed to disconnect from PC:", str(e))

    def disconnect_forced(self):
        self.disconnect()
        sys.exit(0) 

    def reconnect(self):
        self.disconnect()
        self.connect()


    def listen(self):
        while True:
            try:
                message = self.client_socket.recv(PC_BUFFER_SIZE) # the maximum number of bytes to be received

                if not message:
                    print("[PC] PC disconnected remotely. Reconnecting...")
                    self.reconnect()

                decodedMsg = message.decode("utf-8")
                if len(decodedMsg) <= 1:
                    continue
                print("[PC] Read from PC:", decodedMsg[:150])
                parsedMsg = json.loads(decodedMsg)
                type = parsedMsg["type"]
                
                # PC -> Rpi -> STM
                if type == 'NAVIGATION':
                    self.RPiMain.STM.msg_queue.put(message)

                # PC -> Rpi -> Android
                elif type == 'IMAGE_RESULTS':
                    self.RPiMain.Android.msg_queue.put(message) 
                    
                # PC -> Rpi -> Android
                elif type in ['COORDINATES', 'PATH']:
                    self.RPiMain.Android.msg_queue.put(message)

                else:
                    print("[PC] ERROR: Received message with unknown type from PC -", message)

            # TODO handle exceptions
            except socket.error as e:
                print("[PC] SOCKET ERROR: Failed to read from PC-", str(e))
            except IOError as ie:
                print("[PC] IO ERROR: Failed to read from PC-", str(ie))
            except Exception as e2:
                print("[PC] ERROR: Failed to read from PC-", str(e2))
            except ConnectionResetError:
                print("[PC] ConnectionResetError")
            except:
                print("[PC] Unknown error")

    def send(self):
        while True:
            message = self.msg_queue.get()
            # add the first 4 bytes is length of the 
            message_len = len(message)
            length_bytes = message_len.to_bytes(4, byteorder="big")
            result_bytes = length_bytes + message
            exception = True
            while exception: 
                try:
                    message_sized = self.prepend_msg_size(message)
                    self.client_socket.send(message_sized)
                    print("[PC] Write to PC:", message.decode("utf-8")[:150])
                except Exception as e:
                    print("[PC] ERROR: Failed to write to PC -", str(e))
                    self.connect()
                else:
                    exception = False 


    def prepend_msg_size(self, message):
        length_bytes = len(message).to_bytes(4, byteorder="big")
        return length_bytes + message

            