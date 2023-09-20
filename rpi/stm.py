# THIS FILE IS A WORK IN PROGRESS #

import json
import re
import serial

from rpi_config import *

class STMInterface:
    def __init__(self, RPiMain):
        self.RPiMain = RPiMain # TODO
        self.baudrate = STM_BAUDRATE
        self.serial = None
        self.connected = False
        self.threadListening = False

    def connect(self):
        try:
            self.serial = serial.Serial("/dev/ttyUSB0", self.baudrate, write_timeout = 0)
            print("Connected to STM 0 successfully.")
            self.connected = True
        except:
            try:
                self.serial = serial.Serial("/dev/ttyUSB1", self.baudrate, write_timeout = 0)
                print("Connected to STM 1 successfully.")
                self.connected = True
            except Exception as e:
                print("Failed to connect to STM:", str(e))
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
                
                if len(message) <= 1:
                    # print("Ignoring message with length <=1 from STM")
                    continue
                else: 
                    return message # TODO check return types

            except Exception as e:
                print("Failed to read from STM:", str(e))
                # TODO: need to handle this in rpi main
                self.threadListening = False 
                return
    
    def wait_for_ack(self): 
        response = self.listen(target_msg= STM_ACK_MSG)
        if response == STM_ACK_MSG:
            return True
        else:
            if response == None:
                print("Error waiting for ACK message from STM")
            else:
                print("Unknown response from STM:", response)
            return False
            
    def send(self, message): # TODO discuss return value
        message_str = message.decode("utf-8")
        message_json = json.loads(message_str)
        message_type = message_json["type"]

        if message_type == "NAVIGATION":
            commands = message_json["data"]["commands"]
            for command in commands:
                if self.is_valid_command(command):
                    # TODO use queue?
                    """
                    - one queue for sending, one for receiving, queue size = 1
                    - some projects use queues for sending everything (android included)
                        - listen function puts messages in queues of other components
                        - send function reads from queue and actually sends messages
                        - this gives 2 threads per component
                        - see MDP_GP28_CODE/MDP_GP28_CODE/RPI/task1.py.txt: from multiprocessing import Process, Value, Queue, Manager, Lock
                        - see SC2079_CZ3004-MDP/RPI/Multithreading/task2/STM_thread.py
                    """
                    try:
                        encoded_string = command.encode()
                        byte_array = bytearray(encoded_string)
                        self.serial.write(byte_array)
                    except Exception as e:
                        print("Failed to write to STM:", str(e)) # TODO retry?
                    else:
                        print("Write to STM [%s], waiting for ACK" % command)
                        if self.wait_for_ack(): 
                            print("Acknowledged by STM") # TODO show command if echo?
                        else: #TODO handle exception or no ack: retry + timeout ??
                            pass
                else:
                    print("Invalid command to STM rejected:", command, "in NAVIGATION message:", message)
                    # TODO return to sender?
                    return
        # elif message_type == "GET_ULTRASONIC": # TODO
        else:
            print("Invalid message type for STM")
            return

    def is_valid_command(self, command):
        if re.match(STM_COMMAND_FORMAT, command):
            return True
        else:
            return False
