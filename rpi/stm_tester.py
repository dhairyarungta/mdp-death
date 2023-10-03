import json
from queue import Queue
import re
import threading
import serial
from Camera import get_image

from rpi_config import *


serial_sock = serial.Serial("/dev/ttyUSB0", 115200, write_timeout = 0)
print("[STM] Connected to STM 0 successfully.")


# for command in ["SF030", "RF090", "SB030", "LF090", "SF020"]:
while True: 
    command = input("Enter command: ").strip().upper()
    if re.match('^[SLR][FB][0-9]{3}$', command):
        encoded_string = command.encode()
        byte_array = bytearray(encoded_string)
        serial_sock.write(byte_array)

        message = None
        while True:
            print("[STM] In listening loop...")
            message = str(serial_sock.read(SERIAL_BUFFER_SIZE))
            print("[STM] Read from STM:", message)
            
            if len(message) < 1:
                print("[STM] Ignoring message with length <1 from STM")
                continue
            else: 
                break

        print("RECEIVE:", message)
    else:
        print("Invalid command. Please use format <L/R/S><F/B>XXX.")