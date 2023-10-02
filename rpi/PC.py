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
        self.msg_queue = Queue()

    def connect(self):
        # 1. Solution for thread-related issues: always attempt to disconnect first before connecting
        self.disconnect()

        # 2. Wait and accept PC connection
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print("Socket established successfully.")
                sock.bind((self.host, self.port))
                sock.listen(128) # the maximum number of queued connections that the server can handle simultaneously

                print("Waiting for PC connection...")
                with socket.timeout(20):
                    self.client_socket, self.address = sock.accept()

        # Handle any errors that may occur during the connection attempt.
        except socket.error as e:
            print('PC connection failed: {}'.format(str(e)))

        # Log the connection attempt.
        print('PC connected successfully: {}'.format(self.address))
        
    def disconnect(self):
        try:
            if self.client_sock is not None:
                self.client_sock.close()
                self.client_sock = None
                print("Disconnected from PC successfully.")
        except Exception as e:
            print("Failed to disconnect from PC: " + str(e))

    def disconnect_forced(self):
        self.disconnect()
        sys.exit(0) 

    def get_image(self,obs_id):
        # capture img to img_pth 
        img_pth = "img.jpg"
        capture(img_pth)
        # preprocessing image
        preprocess_img(img_pth)
                    
        # construct image
        if os.path.isfile(img_pth):
            with open(img_pth, "rb") as img:
                encoded_string = base64.b64encode(img.read()).decode('utf-8')
                message = {
                    "type": 'IMAGE_TAKEN',
                    "data":{
                        "obs_id": obs_id,
                        "image": encoded_string
                     }
                    }
                self.msg_queue.put(json.dumps(message).encode("utf-8"))      


    def listen(self):
        while True:
            try:
                message = self.client_socket.recv(PC_BUFFER_SIZE) # the maximum number of bytes to be received

                if not message:
                    print("PC disconnected remotely.")
                    break

                decodedMsg = message.decode("utf-8")
                if len(decodedMsg) <= 1:
                    continue
                print("Read from PC: " + decodedMsg)
                parsedMsg = json.loads(decodedMsg)
                type = parsedMsg["type"]
                
                # PC -> Rpi -> STM
                if type == 'NAVIGATION':
                    self.RPiMain.STM.msg_queue.put(message)

                # PC -> Rpi -> Android
                elif type == 'IMAGE_RESULTS':
                    self.RPiMain.Android.msg_queue.put(message) 

                # PC -> Rpi -> PC
                elif type == 'GET_IMAGE':
                    obs_id = parsedMsg["data"]["obs_id"]
                    # Start a new thread to capture and send the image
                    capture_and_send_image_thread = threading.Thread(target=self.get_image, args=(obs_id,))
                    capture_and_send_image_thread.start()
                    
                    
                    
                # PC -> Rpi -> Android
                elif type == 'COORDINATES':
                    self.RPiMain.Android.msg_queue.put(message)

                else:
                    print("ERROR: Received message with unknown type from PC.", message)
           
            except socket.error as e:
                print("Socket Error. Failed to read from PC: %s" %str(e))
                break
            except IOError as ie:
                print("IO Error. Failed to read from PC: %s" %str(ie))
                break
            except Exception as e2:
                print("Failed to read from PC: %s" %str(e2))
                break
            except ConnectionResetError:
                print("ConnectionResetError")
                break
            except:
                print("Unknown error")
                break

    def send(self):
        while True:
            message = self.msg_queue.get()
            exception = True
            while exception: 
                try:
                    self.client_socket.send(message)
                    print("Write to PC: " + message.decode("utf-8"))
                except Exception as e:
                    print("ERROR: Failed to write to PC -", str(e))
                    self.connect()
                else:
                    exception = False 

            