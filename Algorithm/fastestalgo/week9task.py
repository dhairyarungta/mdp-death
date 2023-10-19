import logging
import os
import sys

cwd = os.getcwd()
pardir = os.path.dirname(cwd)
mdp_algo_dir = os.path.join(pardir, 'mdpalgo')
sys.path.insert(1, mdp_algo_dir)

from mdpalgo import constants
from mdpalgo.communication.comms import AlgoClient
from mdpalgo.communication.message_parser import MessageType
from mdpalgo.interface.simulator import *
import json
from image_rec import image_rec


# for saving the image
from PIL import Image

class Week9Task:
    def __init__(self):
        self.commsClient = None
        self.obstacle_id = 1 # obstacle_id = 1 or 2
        self.simulator = Simulator()

    def start_algo_client(self):
        """Connect to RPi wifi server"""
        self.commsClient = AlgoClient()
        self.commsClient.connect()
        constants.RPI_CONNECTED = True

    # def run_old(self):
    #     """Listen to RPI for image data and send image rec result"""
    #     self.start_algo_client()
    #     while constants.RPI_CONNECTED:
    #         try:
    #             all_data = self.commsClient.recv()

    #             if all_data is None:
    #                 continue

    #             message_type_and_data = json.loads(all_data)
    #             message_data = message_type_and_data["data"]
    #             if message_type_and_data["type"] == MessageType.IMAGE_TAKEN:
    #                 self.on_receive_image_taken_message(message_data)

    #         except (IndexError, ValueError) as e:
    #             print("Invalid command: " + all_data)
    


    def run(self):

        self.start_algo_client()
        assert constants.RPI_CONNECTED == True
        try:
            self.run_pathing()
            
        except (EOFError) as e:
            print("EOF error")

    def receive_message(self):
        print("listening")
        while True:
            print("reached 1")
            try:
                all_data = self.commsClient.recv()

                if all_data is None:
                    continue

                message_type_and_data = json.loads(all_data)
                return message_type_and_data

            except (IndexError, ValueError) as e:
                print(e)
                print("Invalid command: " + all_data.decode())


    def run_pathing(self):
        # STEP 1: move robot forward until detect obstacle and detect time taken

        message_type_and_data = self.receive_message()
        message_data = message_type_and_data["data"]
        while (message_type_and_data["type"] != MessageType.START_TASK.value):
            message_type_and_data = self.receive_message()
        
        
        print("1")
        result_message = {
            "type": "NAVIGATION",
            "data": {
                "commands": ["UF200"]
            }
        }
        self.commsClient.send(result_message)
        

        # STEP 2: Detect picture
        print("2")
        img_dic_one = {"38":"firstRight", "39":"firstLeft"}
        message_type_and_data = self.receive_message()


        # assert message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value
        while (message_type_and_data["type"]!=MessageType.IMAGE_TAKEN.value):
            message_type_and_data=self.receive_message()


        message_data = message_type_and_data["data"]
        # img_id = ""

        img_id = self.get_img_id_from_image_taken(message_data)
        if (img_id!="38" and img_id!="39"):
            img_id="39" # guess left
            # img_id=self.get_img_id_from_image_taken(message_data)


        result_message ={
            "type": "NAVIGATION",
            "data": {
            "commands": [img_dic_one[img_id],"YF150", "SB012"]
            }
        }

        self.commsClient.send(result_message)

        #STEP3
        print ("3")
        message_type_and_data = self.receive_message()
        # assert message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value
        while (message_type_and_data["type"]!=MessageType.IMAGE_TAKEN.value):
            message_type_and_data=self.receive_message()



        message_data = message_type_and_data["data"]
        
        # img_id=""
        img_id = self.get_img_id_from_image_taken(message_data)
        
        if (img_id!="38" and img_id!="39"):
            img_id = "39" # guess left
            # img_id=self.get_img_id_from_image_taken(message_data)


        img_dic_two = {'38':"secondRight", '39':"secondLeft"}

        result_message ={
            "type": "NAVIGATION",
            "data": {
            "commands": [img_dic_two[img_id]]
            }
        }
        self.commsClient.send(result_message)
        
        print("pc done, closing rpi client")
        self.commsClient.disconnect()
        mdp_constants.RPI_CONNECTED = False
        self.commsClient = None



    def get_img_id_from_image_taken(self, message_data, arrow: bool = True):
        image_data = message_data["image"]
        image_data = image_data.encode('utf-8')
        image_data = base64.b64decode(image_data)
        import uuid
        image_name = f'{str(uuid.uuid4())}.jpg'
        image_path = f"images/{image_name}"
        with open(image_path, "wb") as fh:
            print(f"Image save to {image_path}!")
            fh.write(image_data)

        if os.path.isfile(image_path):
            result_path = f'images_result/{image_name}'
            result = image_rec(image_path, save_path=result_path, arrow=arrow)
            if result is None:
                print('No object detected!')
                img_id = '00'
            else:
                img_id = result["predictions"][0]["class"][2:]
                #Use arrow model if detect arrow
                print(f"Output image is save to {result_path}")
        return img_id

def remove_file_ext(directory, file_ext = '.jpg'):
    for f in os.listdir(directory):
        if f.endswith(file_ext):
            os.remove(os.path.join(directory, f))

if __name__ == "__main__":
    remove_file_ext('images', '.jpg')
    remove_file_ext('images_result', '.jpg')

    
    X = Week9Task()
    X.run()



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