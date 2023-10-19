import logging
import os
from Algorithm.mdpalgo import constants
from Algorithm.mdpalgo.communication.comms import AlgoClient
from Algorithm.mdpalgo.communication.message_parser import MessageType
from Algorithm.mdpalgo.interface.simulator import *
import json
from image_rec import image_rec

from imagerec.infer import infer
from imagerec.helpers import get_path_to
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
        assert message_type_and_data["type"] == MessageType.START_TASK.value
        print("1")
        result_message = {
            "type": "PATH",
            "data": {
                "UF200"
            }
        }
        self.commsClient.send(result_message)
        

        # STEP 2: Detect picture
        print("2")
        img_dic_one = {38:"firstRight", 39:"firstLeft"}
        message_type_and_data = self.receive_message()
        assert message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value

        message_data = message_type_and_data["data"]
        img_id = self.get_img_id_from_image_taken(message_data)

        result_message ={
            "type": "NAVIGATION",
            "data": {
            "commands": [img_dic_one[img_id],"YF150", "SB010"]
            }
        }

        self.commsClient.send(result_message)

        #STEP3
        print ("3")
        message_type_and_data = self.receive_message()
        assert message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value

        message_data = message_type_and_data["data"]
        img_id = self.get_img_id_from_image_taken(message_data)
        img_dic_two = {38:"secondRight", 39:"secondLeft"}

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



    def get_img_id_from_image_taken(self, message_data, arrow: bool = False):
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




    # def on_receive_image_taken_message(self, message_data: dict):
    #     img_id = self.simulator.get_img_id_from_image_taken(message_data, arrow=True)

    #     result_message = {
    #         "type": "IMAGE_RESULTS",
    #         "data": {
    #             "obs_id": self.obstacle_id,
    #             "img_id": img_id
    #         }
    #     }

    #     # send image result string to rpi
    #     self.send_message_to_rpi(image_result_string)

    #     # change obstacle_id to 2 after sending first image result
    #     if self.obstacle_id == 1:
    #         self.obstacle_id = 2

    # def send_message_to_rpi(self, message: str):
    #     if constants.RPI_CONNECTED:
    #         self.comms.send(message)

    # def check_infer_result(self, infer_result):
    #     if infer_result == "Nothing detected":
    #         return "Others"
    #     elif type(infer_result) != list:
    #         print(f"Strange behaviour from imagerec. Infer result: {infer_result}. Neither a list nor \"Nothing detected\" string")
    #         return "Others"

    #     for result in infer_result:
    #         if result == "Left" or result == "Right":
    #             return result

    #     return "Others"

    # def get_image_result_string(self, target_id):
    #     image_result_list = ["TARGET", target_id]
    #     return '/'.join([str(elem) for elem in image_result_list])

if __name__ == "__main__":
    # unit test
    constants.WIFI_IP = constants.TEST_IP
    X = Week9Task()
    X.run()

    # # Test the check infer result
    # infer_result = ["Left"]
    # label = X.check_infer_result(infer_result)
    # assert label == "Left"

    # infer_result = ["A", "Right"]
    # label = X.check_infer_result(infer_result)
    # assert label == "Right"

    # infer_result = "Nothing detected"
    # label = X.check_infer_result(infer_result)
    # assert label == "Others"

    # infer_result = ["A", "One", "Two"]
    # label = X.check_infer_result(infer_result)
    # assert label == "Others"

    # infer_result = "Invalid string"
    # label = X.check_infer_result(infer_result)
    # assert label == "Others"

    # # Test the receiving image function
    # import fastestalgo.tests.images
    # image_folder = get_path_to(fastestalgo.tests.images)

    # # Send first image only bullseye (so not saved)
    # image_path = image_folder.joinpath("Bullseye.jpg")
    # with Image.open(image_path) as image:
    #     image.load()
    # data_dict = {"image": image}
    # X.on_receive_image_taken_message(data_dict)

    # # Send first image only bullseye (so not saved)
    # image_path = image_folder.joinpath("Bullseye.jpg")
    # with Image.open(image_path) as image:
    #     image.load()
    # data_dict = {"image": image}
    # X.on_receive_image_taken_message(data_dict)

    # # Send first image only bullseye (so not saved)
    # image_path = image_folder.joinpath("Bullseye.jpg")
    # with Image.open(image_path) as image:
    #     image.load()
    # data_dict = {"image": image}
    # X.on_receive_image_taken_message(data_dict)

    # # Send first image
    # image_path = image_folder.joinpath("left_arrow.jpg")
    # with Image.open(image_path) as image:
    #     image.load()
    # data_dict = {"image": image}
    # X.on_receive_image_taken_message(data_dict)

    # # Send second image only bullseye (so not saved)
    # image_path = image_folder.joinpath("Bullseye.jpg")
    # with Image.open(image_path) as image:
    #     image.load()
    # data_dict = {"image": image}
    # X.on_receive_image_taken_message(data_dict)

    # # Send second image (predict on finish should be called after this)
    # image_path2 = image_folder.joinpath("right_arrow.jpg")
    # with Image.open(image_path2) as image2:
    #     image2.load()
    # data_dict2 = {"image": image2}
    # X.on_receive_image_taken_message(data_dict2)

    # # Send second image (predict on finish should be called after this)
    # image_path2 = image_folder.joinpath("right_arrow.jpg")
    # with Image.open(image_path2) as image2:
    #     image2.load()
    # data_dict2 = {"image": image2}
    # X.on_receive_image_taken_message(data_dict2)



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