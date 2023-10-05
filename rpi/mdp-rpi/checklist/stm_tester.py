# for testing reading and writing from STM

import re
import serial

from rpi_config import *


serial_sock = serial.Serial("/dev/ttyUSB0", 115200, write_timeout = 0)
print("[STM] Connected to STM 0 successfully.")

while True: 
    command = input("Enter command: ").strip().upper()
    if re.match('^[SLR][FB][0-9]{3}$', command):
        encoded_string = command.encode()
        byte_array = bytearray(encoded_string)
        serial_sock.write(byte_array)

        message = None
        while True:
            print("[STM] In listening loop...")
            message = str(serial_sock.read())
            print("[STM] Read from STM:", message)
            
            if len(message) < 1:
                print("[STM] Ignoring message with length <1 from STM")
                continue
            else: 
                break

        print("RECEIVE:", message)
    else:
        print("Invalid command. Please use format <L/R/S><F/B>XXX.")