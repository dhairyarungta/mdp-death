import json
from queue import Queue
import re
import threading
import time
import serial
from Camera import get_image

from rpi_config import *

class STMInterface:
    def __init__(self, RPiMain):
        self.RPiMain = RPiMain 
        self.baudrate = STM_BAUDRATE
        self.serial = None
        self.msg_queue = Queue()
        self.obstacle_count = 0

    def connect(self):
        try:
            self.serial = serial.Serial("/dev/ttyUSB0", self.baudrate, write_timeout = 0)
            print("[STM] Connected to STM 0 successfully.")
            self.clean_buffers()
        except:
            try:
                self.serial = serial.Serial("/dev/ttyUSB1", self.baudrate, write_timeout = 0)
                print("[STM] Connected to STM 1 successfully.")
                self.clean_buffers()
            except Exception as e:
                print("[STM] ERROR: Failed to connect to STM -", str(e))
    
    def reconnect(self): 
        if self.serial != None and self.serial.is_open:
            self.serial.close()
        self.connect()
    
    def clean_buffers(self):
        self.serial.reset_input_buffer() # receiving
        self.serial.reset_output_buffer() # sending
        # print("[STM] Flushed input and output buffers")

    def listen(self):
        message = None
        while True:
            print("[STM] In listening loop...")
            try:
                message = self.serial.read().decode("utf-8")
                print("[STM] Read from STM:", message[:MSG_LOG_MAX_SIZE])
                
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
                # display path on android
                self.send_path_to_android(message_json) 

                commands = self.adjust_commands(message_json["data"]["commands"])
                for command in commands:
                    print("[STM] Sending command", command)
                    self.write_to_stm(command)  
                self.obstacle_count += 1

                # Start a new thread to capture and send the image to PC
                capture_and_send_image_thread = threading.Thread(target=self.send_image_to_pc, daemon=True)
                capture_and_send_image_thread.start()

                if self.obstacle_count % STM_GYRO_RESET_FREQ == 0:
                    print("[STM] Resetting gyroscope after %d obstacles" % self.obstacle_count)
                    self.write_to_stm(STM_GYRO_RESET_COMMAND)
            else:
                print("[STM] WARNING: Rejecting message with unknown type [%s] for STM" % message_type)

    def write_to_stm(self, command):
        self.clean_buffers()
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
                    if command == STM_GYRO_RESET_COMMAND:
                        print("[STM] Waiting %ss for reset" % STM_GYRO_RESET_DELAY)
                        time.sleep(STM_GYRO_RESET_DELAY)
                    else: # navigation command
                        print("[STM] Waiting for ACK")
                        self.wait_for_ack()
        else:
            print(f"[STM] ERROR: Invalid command to STM [{command}]. Discarding rest of NAVIGATION message {message}")

    def wait_for_ack(self):
        message = self.listen()
        if message  == STM_ACK_MSG:
            print("[STM] Received ACK from STM") 
        else:
            print("[STM] ERROR: Unexpected message from STM -", message)
            self.reconnect() 


    def send_image_to_pc(self):
        print("[STM] Adding image from camera to PC message queue")
        self.RPiMain.PC.msg_queue.put(get_image())      

    def send_path_to_android(self, message_json):
        # send path to Android for display
        try: 
            path_message = self.create_path_message(message_json["data"]["path"])
            self.RPiMain.Android.msg_queue.put(path_message)
            print("[STM] Adding NAVIGATION path from PC to Android message queue")
        except:
            print("[STM] No path found in NAVIGATION message")    

    def is_valid_command(self, command):
        if re.match(STM_NAV_COMMAND_FORMAT, command) or command == STM_GYRO_RESET_COMMAND:
            return True
        else:
            return False

    def adjust_commands(self, commands):
        def is_turn_command(command):
            return (command in STM_COMMAND_ADJUSTMENT_MAP.keys())

        def adjust_turn_command(turn_command):
            return STM_COMMAND_ADJUSTMENT_MAP.get(turn_command, turn_command)

        def combine_straight_commands(straight_commands):
            dir_dict = {"SF": 1, "SB": -1} # let forward direction be positive
            total = 0
            for c in straight_commands:
                dir = c[:2]
                val = int(c[2:])
                total += dir_dict.get(dir, 0) * val
            
            if total > 0:
                return "SF%03d" % abs(total)
            elif total < 0:
                return "SB%03d" % abs(total)
            else:
                return None

        def add_command(final, new):
            # check new and preceding are straight commands
            if not is_turn_command(new) and \
                    (len(final) > 0 and not is_turn_command(final[-1])): 
                prev = final.pop(-1) # remove prev
                combined = combine_straight_commands([prev, new])
                if combined != None:
                    final.append(combined)
            else:
                final.append(new)

            return final

        final_commands = []     
        for i in range(len(commands)):
            if is_turn_command(commands[i]): 
                turn_seq = adjust_turn_command(commands[i])
                for c in turn_seq:
                    final_commands = add_command(final_commands, c)
            else:
                final_commands = add_command(final_commands, commands[i])
        return final_commands

    def create_path_message(self, path):
        message = {
            "type": "PATH",
            "data": {
                "path": path
            }
        }
        return json.dumps(message).encode("utf-8")
    
    # functions for task 2 (W9) - fastest car
    def move_back(self,xdist,ydist):
        movement_list = []
        y_adjustment = 10   # to be tested later, range[4, ?]
        x_adjustment = 0.5* xdist
        y_offset = ydist + 20 + y_adjustment
        movement_list.append(f"SF{str(y_offset)}")
        turning_direction = self.get_second_arrow()   # to be implemented later
        if turning_direction == 'r':
            movement_list.append(STM_COMMAND_ADJUSTMENT_MAP["LF090"])
            movement_list.append(f"SF{str(x_adjustment)}")
            movement_list.append(STM_COMMAND_ADJUSTMENT_MAP["RF090"])
        else:
            movement_list.append(STM_COMMAND_ADJUSTMENT_MAP["RF090"])
            movement_list.append(f"SF{str(x_adjustment)}")
            movement_list.append(STM_COMMAND_ADJUSTMENT_MAP["LF090"])
        return movement_list


    