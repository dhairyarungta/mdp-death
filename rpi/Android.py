from queue import Queue
import bluetooth as bt
import socket
import sys
import subprocess
import json

from rpi_config import *

class AndroidInterface:
    def __init__(self, RPiMain):
        self.RPiMain = RPiMain
        self.host = RPI_IP
        self.uuid = BT_UUID # typical uuid
        self.msg_queue = Queue()

    def connect(self):
        # for BluetoothError 'Permission denied'
        subprocess.run("sudo chmod o+rw /var/run/sdp", shell=True) 

        # Establish and bind socket
        self.socket = bt.BluetoothSocket(bt.RFCOMM)
        print("[Android] BT socket established successfully.")
    
        try:
            self.port = self.socket.getsockname()[1] #4
            print("[Android] Waiting for connection on RFCOMM channel", self.port)
            self.socket.bind((self.host, bt.PORT_ANY)) #bind to port
            print("[Android] BT socket binded successfully.")
            
            # Turning advertisable
            subprocess.run("sudo hciconfig hci0 piscan", shell=True)
            self.socket.listen(128)
            
            bt.advertise_service(self.socket, "Group14-Server", service_id = self.uuid, service_classes = [self.uuid, bt.SERIAL_PORT_CLASS], profiles = [bt.SERIAL_PORT_PROFILE],)
        
        except socket.error as e:
            print("[Android] ERROR: Android socket binding failed -", str(e))
            sys.exit()
            
        print("[Android] Waiting for Android connection...")

        try:
            # with socket.timeout(30):
            self.client_socket, self.client_info = self.socket.accept()
            print("[Android] Accepted connection from", self.client_info)
            
        except socket.error as e:
            print("[Android] ERROR: connection failed -", str(e))
            # self.reconnect() # TODO

    def disconnect(self):
        try:
            self.socket.close()
            print("[Android] Disconnected from Android successfully.")
        except Exception as e:
            print("[Android] ERROR: Failed to disconnect from Android -", str(e))
            
    def disconnectForced(self): # TODO: unused
        self.disconnect()
        sys.exit(0) 

    def reconnect(self):
        self.disconnect()
        self.connect()

    def listen(self):
        while True:
            try:
                message = self.client_socket.recv(BT_BUFFER_SIZE) 

                if not message:
                    print("[Android] Android disconnected remotely. Reconnecting...")
                    self.reconnect()

                decodedMsg = message.decode("utf-8")
                if len(decodedMsg) <= 1:
                    continue
                print("[Android] Read from Android:", decodedMsg)
                parsedMsg = json.loads(decodedMsg)
                type = parsedMsg["type"]

                # Android -> RPi -> STM
                if type == 'NAVIGATION':
                    self.RPiMain.STM.msg_queue.put(message) 

                # Android -> RPi -> PC
                if type == 'START_TASK':
                    self.RPiMain.PC.msg_queue.put(message)

            # TODO should android be asked to resend its message
            except socket.error as e:
                print("[Android] SOCKET ERROR: Failed to read from Android -", str(e))
            except IOError as ie:
                print("[Android] IO ERROR: Failed to read from Android -", str(ie))
            except Exception as e2:
                print("[Android] ERROR: Failed to read from Android -", str(e2))
            except ConnectionResetError:
                print("[Android] ConnectionResetError")
            except:
                print("[Android] Unknown error")

    def send(self):
        while True: 
            message = self.msg_queue.get()
            exception = True
            while exception: 
                try:
                    self.client_socket.send(message)
                    print("[Android] Write to Android: " + message.decode("utf-8"))
                except Exception as e:
                    print("[Android] ERROR: Failed to write to Android -", str(e))
                    self.reconnect() # reconnect and resend
                else:
                    exception = False # done sending, get next message
