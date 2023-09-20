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
        self.connected = False
        self.threadListening = False

    def connect(self):

        #Establish and bind socket
        self.socket = bt.BluetoothSocket(bt.RFCOMM)
        print("Android socket established successfully.")
    
        try:
            self.port = self.socket.getsockname()[1] #4
            print("Waiting for connection on RFCOMM channel %d" % self.port)
            self.socket.bind((self.host, bt.PORT_ANY)) #bind to port
            print("Android socket binded successfully.")
            
            #Turning advertisable
            subprocess.call(['sudo', 'hciconfig', 'hci0', 'piscan'])
            self.socket.listen(128)
            
            bt.advertise_service(self.socket, "Group14-Server", service_id = self.uuid, service_classes = [self.uuid, bt.SERIAL_PORT_CLASS], profiles = [bt.SERIAL_PORT_PROFILE],)
        
        except socket.error as e:
            print("Android socket binding failed: %s" %str(e))
            sys.exit()
            
        print("Waiting for Android connection...")

        try:
            self.client_socket, self.client_info = self.socket.accept()
            print("Accepted connection from ", self.client_info)
            
        except socket.error as e:
            print('Disconnecting...')
            self.disconnectForced()
        self.connected = True
        return 1

    def disconnect(self):
        try:
            self.socket.close()
            self.connected = False
            self.threadListening = False
            print("Disconnected from Android successfully.")
        except Exception as e:
            print("Failed to disconnect from Android: %s" %str(e))
            
    def disconnectForced(self):
        try:
            self.socket.close()
            self.connected = False
            self.threadListening = False
            print("Disconnected from Android successfully.")
        except Exception as e:
            print("Failed to disconnect from Android: %s" %str(e))
        sys.exit(0) # TODO: later

    def listen(self):
    
        self.threadListening = True
        
        while True:
            try:
                message = self.client_socket.recv(BT_BUFFER_SIZE) 

                if not message:
                    print("Android disconnected remotely.")
                    break

                # 3. Parse json message
                decodedMsg = message.decode("utf-8")
                if len(decodedMsg) <= 1:
                    continue
                print("Read from Android: " + decodedMsg)
                parsedMsg = json.loads(decodedMsg)
                type = parsedMsg["type"]

                # Android -> rpi -> STM
                if type == 'NAVIGATION':
                    self.RPiMain.STM.send(message) 

                # Android -> rpi -> PC
                if type == 'START_TASK':
                    self.RPiMain.PC.send(message)

            except socket.error as e:
                print("Socket Error. Failed to read from Android: %s" %str(e))
                break

            except IOError as ie:
                print("IO Error. Failed to read from Android: %s" %str(ie))
                break

            except Exception as e2:
                print("Failed to read from Android: %s" %str(e2))
                break

            except ConnectionResetError:
                print("ConnectionResetError")
                break

            except:
                print("Unknown error")
                break
                
        #end of listening loop - set flags to false
        self.threadListening = False
        self.connected = False

    def send(self, message):
        try:
            self.client_socket.send(message)
            print("Write to Android: " + message.decode("utf-8"))
        except Exception as e:
            print("Failed to write to Android: %s" %str(e))
            self.disconnect()
