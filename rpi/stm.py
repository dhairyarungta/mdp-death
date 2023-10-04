import json
from queue import Queue
import re
import threading
import serial
from Camera import get_image

from rpi_config import *

class STMInterface:
    def __init__(self, RPiMain):
        self.RPiMain = RPiMain 
        self.baudrate = STM_BAUDRATE
        self.serial = None
        self.msg_queue = Queue()

    def connect(self):
        try:
            self.serial = serial.Serial("/dev/ttyUSB0", self.baudrate, write_timeout = 0)
            print("[STM] Connected to STM 0 successfully.")
        except:
            try:
                self.serial = serial.Serial("/dev/ttyUSB1", self.baudrate, write_timeout = 0)
                print("[STM] Connected to STM 1 successfully.")
            except Exception as e:
                print("[STM] ERROR: Failed to connect to STM -", str(e))
    
    def reconnect(self): 
        if self.serial != None and self.serial.is_open:
            self.serial.close()
        self.connect()

    def listen(self):
        message = None
        while True:
            print("[STM] In listening loop...")
            try:
                message = self.serial.read().decode("utf-8")
                print("[STM] Read from STM:", message[:80])
                
                if len(message) < 1:
                    # print("[STM] Ignoring message with length <1 from STM")
                    continue
                else: 
                    break

            except Exception as e:
                message = str(e)
                break

        return message
            
    def send(self): 
        while True: 
            message = self.msg_queue.get()

            message_str = message.decode("utf-8")
            message_json = json.loads(message_str)
            message_type = message_json["type"]

            if message_type == "NAVIGATION":
                commands = message_json["data"]["commands"]
                for command in commands:
                    print("[STM] Sending command", command)
                    if self.is_valid_command(command):
                        exception = True
                        while exception:
                            try:
                                encoded_string = command.encode()
                                byte_array = bytearray(encoded_string)
                                self.serial.write(byte_array)
                            except Exception as e:
                                print("[STM] ERROR: Failed to write to STM -", str(e)) 
                                exception = True
                                self.reconnect() # reconnect and retry

                            else:
                                exception = False
                                message = self.listen()
                                if message  == STM_ACK_MSG:
                                    print("[STM]", command, "acknowledged by STM") 
                                # elif message.isnumeric(): # TODO check STM ultrasonic sensor output format
                                #     print("[STM] WARNING:", command, "caused STM emergency stop, notifying PC") 
                                #     distance = float(message) 
                                #     ultrasonic_message = self.create_ultrasonic_message(command, distance)
                                #     self.RPiMain.PC.msg_queue.put(ultrasonic_message)
                                else:
                                    print("[STM] ERROR: Unexpected message from STM -", message)
                                    self.reconnect() # TODO
                                
                    else:
                        print(f"[STM] ERROR: Invalid command to STM [{command}]. Discarding rest of NAVIGATION message {message}")
                
                # Start a new thread to capture and send the image to PC
                capture_and_send_image_thread = threading.Thread(target=self.send_image_to_pc)
                capture_and_send_image_thread.start()
            else:
                print("[STM] WARNING: Rejecting message with unknown type [%s] for STM" % message_type)

    def send_image_to_pc(self):
        print("[STM] Adding image from camera to PC message queue")
        self.RPiMain.PC.msg_queue.put(get_image())      

    def is_valid_command(self, command):
        if re.match(STM_COMMAND_FORMAT, command):
            return True
        else:
            return False
        
    # def create_ultrasonic_message(self, command, distance):
    #     message = {
    #         "type": "ULTRASONIC",
    #         "data": {
    #             "distance": distance,
    #             "command": command
    #         }
    #     }
    #     return json.dumps(message).encode("utf-8")
