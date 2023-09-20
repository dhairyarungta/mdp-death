import re
import serial
import threading
import time

from RPi_config import *

class STMInterface:
    def __init__(self, RPiMain):
        self.RPiMain = RPiMain # TODO
        self.baudrate = STM_BAUDRATE
        self.serial = 0
        self.connected = False
        self.threadListening = False

    def connect(self):
        try:
            #Serial COM Configuration
            self.serial = serial.Serial("/dev/ttyUSB0", self.baudrate, write_timeout = 0)
            print("Connected to STM 0 successfully.")
            self.connected = True
        except:
            try:
                self.serial = serial.Serial("/dev/ttyUSB1", self.baudrate, write_timeout = 0)
                print("Connected to STM 1 successfully.")
                self.connected = True
            except Exception as e2:
                print("Failed to connect to STM: %s" %str(e2))
                self.connected = False

    def listen(self):
        if not self.connected:
            print("Failed to start listening: STM is not connected.")
            return
        
        self.threadListening = True
        while True:
            try:
                message = str(self.serial.read(SERIAL_BUFFER_SIZE))
                print("Read from STM:", message)
                message = message
                length = len(message)
                
                # TODO  wait for ACK ?
                if message == STM_ACK_MSG:
                    self.RPiMain.PC.send(STM_ACK_MSG) 
                    # TODO FORWARD ACK TO PC? OR GET ULTRASONIC AND FORWARD THAT TO PC?
                    # maybe when not ack, we send the last followed command back to PC, or we try again?
                elif length <= 1:
                    # print("Ignoring message with length <=1 from STM")
                    continue
        
            except Exception as e:
                print("Failed to read from STM:", str(e))
                # TODO: need to reconnect after fail to read message?
                self.threadListening = False 
                return
    
    def wait_for_ACK(self): #TODO REUSE LISTEN FUNCTION     
        while True:
            print("Waiting for ACK from STM...")
            try:
                message = self.serial.read(10)
                print('Read from STM: %s' %str(message))
                message = str(message)
                length = len(message)
                
                if length <= 1:
                    continue
                if "A" in message:
                    break

            except Exception as e:
                print("Failed to read from STM: %s" %str(e))
                return
            
    def send(self, message):
        if not self.validate_message(message):
            print("Invalid message to STM rejected:", message)
            return
        
        try:
            encoded_string = message.encode()
            byte_array = bytearray(encoded_string)
            self.serial.write(byte_array)
            print("Write to STM: " + message)
        except Exception as e:
            print("Failed to write to STM: %s" %str(e))
    
    def validate_message(self, message):
        if re.match(STM_COMMAND_FORMAT, message):
            return True
        else:
            return False
