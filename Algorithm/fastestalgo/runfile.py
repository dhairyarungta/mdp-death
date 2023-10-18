
import os
from Algorithm.mdpalgo import constants
from Algorithm.mdpalgo.communication.comms import AlgoClient
from Algorithm.mdpalgo.communication.message_parser import MessageType
from Algorithm.mdpalgo.interface.simulator import *
import json

# for image recognition
from imagerec.infer import infer
from imagerec.helpers import get_path_to


# for saving the image
from PIL import Image

class Week9Task:
    def __init__(self):
        self.comms = None
        self.image_folder = get_path_to(fastestalgo.images)
        self.obstacle_id = 1 # obstacle_id = 1 or 2
        self.simulator = Simulator()

    def start_algo_client(self):
        """Connect to RPi wifi server"""
        self.commsClient = AlgoClient()
        self.commsClient.connect()
        constants.RPI_CONNECTED = True




"""
TASK 2 FLOW:
# 18 Oct
1. android sends START_TASK message to PC
2. PC sends NAVIGATION message with commands [OF150] no path to RPi, forward to STM
3. STM moves to directly in front of obstacle 1
4. RPi gets image, send to PC
5. PC sends NAVIGATION message with commands [firstLeft/firstRight, OF150, SB010] no path to RPi, convert and forward to STM
6. STM moves around obstacle 1 then forward to in front of the image on obstacle 2
>>>> STM NEEDS TO MOVE UNTIL ULTRASONIC STOP AND RETURN YDIST
7. RPi gets image, send to PC
8. PC sends NAVIGATION message with commands [secondLeft/secondRight] no path to RPi, convert and forward to STM
9. RPi records second_arrow, required for returning to carpark later
10.  STM moves around obstacle 2, ending up on side of obstacle 2 in opposite direction than second_arrow 
>>>> STM NEEDS TO MOVE UNTIL IR REACHES END OF OBS, STOP AND RETURN XDIST
11.  RPi calls return_to_carpark(xdist, ydist), sending STM commands to return home



# STM COMMAND TYPES
- SF/SBxxx LF/RFxxx LB/RBxxx return A
- ultrasonic stop 
  - UFxxx: return A
  - YFxxx: return ydist (###)
- IR stop
  - IL/IRxxx: return A, check left IR
  - XL/XRxxx: return xdist (###), check left/right IR

"""