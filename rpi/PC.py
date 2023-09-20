import socket
import sys
import json 
import cv2
import os
import base64
from .capture import capture, preprocess_img

class PCInterface:
    
    def __init__(self, RPiMain=None):
        self.RPiMain = RPiMain
        self.host = "192.168.14.1"
        self.port = 8888
        self.connected = False
        self.threadListening = False

    def connect(self):

        # 1. Solution for thread-related issues: always attempt to disconnect first before connecting
        self.disconnect()

        # 2. Establish and bind socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket established successfully.")

        try:
            self.socket.bind((self.host, self.port))
            print("Socket binded successfully.")
        except socket.error as e:
            print("Socket binding failed: %s" %str(e))
            sys.exit()

        # 3. Wait and accept PC connection
        print("Waiting for PC connection...")
        self.socket.listen(128) # the maximum number of queued connections that the server can handle simultaneously
        self.client_socket, self.address = self.socket.accept()
        print("PC connected successfully.")

        # 4. Set flag to true
        self.connected = True

    def disconnect(self):
        try:
            self.socket.close()
            self.connected = False
            self.threadListening = False
            print("Disconnected from PC successfully.")
        except Exception as e:
            print("Failed to disconnect from PC: %s" %str(e))

    def listen(self):
        
        # 1. Set flag to true
        self.threadListening = True

        # 2. Loop for listening
        while True:
            try:
                message = self.client_socket.recv(1024) # the maximum number of bytes to be received

                if not message:
                    print("PC disconnected remotely.")
                    break

                # 3. Parse json message 
                decodedMsg = message.decode("utf-8")
                if len(decodedMsg) <= 1:
                    continue
                print("Read from PC: " + decodedMsg)
                parsedMsg = json.loads(decodedMsg)
                type = parsedMsg["type"]
                
                # PC -> Rpi -> STM
                # Not sure for each command, an array or just a string
                if type == 'NAVIGATION':
                    self.RPiMain.STM.send(parsedMsg["data"]["commands"]) # ["LF090", "SB005"]

                # PC -> Rpi -> Android
                if type == 'IMAGE_RESULTS':
                    self.RPiMain.Android.send(decodedMsg) #As Android needs type

                # PC -> Rpi -> PC
                if type == 'GET_IMAGE':
                    obs_id = parsedMsg["data"]["obs_id"]
                    # capture img to img_pth 
                    img_pth = "img.jpg"
                    capture(img_pth)
                    # preprocessing image
                    preprocess_img(img_pth)
                    
                    # send image
                    if os.path.isfile(img_pth):
                        with open(img_pth, "rb") as img:
                            encoded_string = base64.b64encode(img.read()).decode('utf-8')
                            message = {
                                "type": "IMAGE",
                                "data":{
                                    "obs_id": obs_id,
                                    "image": encoded_string
                                    }
                                }
                            self.send(json.dumps(message).encode("utf-8"))
                    
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
        
        # 4. End of listening loop - set flags to false
        self.threadListening = False
        self.connected = False


    def send(self, message):
        # message is expected to be a byte object
        try:
            # add the first 4 bytes is length of the 
            message_len = len(message)
            length_bytes = message_len.to_bytes(4, byteorder="big")
            result_bytes = length_bytes + message
            self.client_socket.send(result_bytes)
            print("Send to PC: " + message)
        except ConnectionResetError:
            print("Failed to send to PC: ConnectionResetError")
            self.disconnect()
        except socket.error:
            print("Failed to send to PC: socket.error")
            self.disconnect()
        except IOError as e:
            print("Failed to send to PC: %s" %str(e))
            self.disconnect()

if __name__ == "__main__":
    pc = PCInterface()
    pc.connect()
    pc.listen()


