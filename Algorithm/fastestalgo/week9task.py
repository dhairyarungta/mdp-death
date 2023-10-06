import logging
import os
from Algorithm.mdpalgo import constants
from Algorithm.mdpalgo.communication.comms import AlgoClient
from Algorithm.mdpalgo.communication.message_parser import MessageType
from Algorithm.mdpalgo.interface.simulator import *
import json

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

    def run(self):
        """Listen to RPI for image data and send image rec result"""
        self.start_algo_client()
        while constants.RPI_CONNECTED:
            try:
                all_data = self.commsClient.recv()

                if all_data is None:
                    continue

                message_type_and_data = json.loads(all_data)
                message_data = message_type_and_data["data"]
                if message_type_and_data["type"] == MessageType.IMAGE_TAKEN:
                    self.on_receive_image_taken_message(message_data)

            except (IndexError, ValueError) as e:
                print("Invalid command: " + all_data)

    def on_receive_image_taken_message(self, message_data: dict):
        img_id = self.simulator.get_img_id_from_image_taken(message_data)


        image_result_string = self.get_image_result_string(target_id)

        # send image result string to rpi
        self.send_message_to_rpi(image_result_string)

        if target_id == "Others":
            return

        self.save_image(image)

        # change obstacle_id to 2 after sending first image result
        if self.obstacle_id == 1:
            self.obstacle_id = 2

        # run predict function after image result of obstacle 2 has been sent to rpi
        elif self.obstacle_id == 2:
            os.system(f'python -m imagerec.predict \"{self.image_folder}\"')

    def save_image(self, image):
        # get list of images
        list_of_images = list(self.image_folder.glob("*.jpg"))
        print("List of images:", list_of_images)

        # set image name
        if len(list_of_images) == 0:
            image_name = "img_1"
        else:
            latest_image = max(list_of_images, key=os.path.getctime)
            print("Latest:", latest_image)
            previous_image_name = latest_image.stem
            print("Previous image name:", previous_image_name)
            image_number = int(previous_image_name.split("_")[-1]) + 1
            image_name = "img_" + str(image_number)

        print("Image name:", image_name)
        image.save(self.image_folder.joinpath(f"{image_name}.jpg"))

    def send_message_to_rpi(self, message: str):
        if constants.RPI_CONNECTED:
            self.comms.send(message)

    def check_infer_result(self, infer_result):
        if infer_result == "Nothing detected":
            return "Others"
        elif type(infer_result) != list:
            print(f"Strange behaviour from imagerec. Infer result: {infer_result}. Neither a list nor \"Nothing detected\" string")
            return "Others"

        for result in infer_result:
            if result == "Left" or result == "Right":
                return result

        return "Others"

    def get_image_result_string(self, target_id):
        image_result_list = ["TARGET", target_id]
        return '/'.join([str(elem) for elem in image_result_list])

if __name__ == "__main__":
    # unit test
    constants.WIFI_IP = constants.TEST_IP
    X = Week9Task()

    # Test the check infer result
    infer_result = ["Left"]
    label = X.check_infer_result(infer_result)
    assert label == "Left"

    infer_result = ["A", "Right"]
    label = X.check_infer_result(infer_result)
    assert label == "Right"

    infer_result = "Nothing detected"
    label = X.check_infer_result(infer_result)
    assert label == "Others"

    infer_result = ["A", "One", "Two"]
    label = X.check_infer_result(infer_result)
    assert label == "Others"

    infer_result = "Invalid string"
    label = X.check_infer_result(infer_result)
    assert label == "Others"

    # Test the receiving image function
    import fastestalgo.tests.images
    image_folder = get_path_to(fastestalgo.tests.images)

    # Send first image only bullseye (so not saved)
    image_path = image_folder.joinpath("Bullseye.jpg")
    with Image.open(image_path) as image:
        image.load()
    data_dict = {"image": image}
    X.on_receive_image_taken_message(data_dict)

    # Send first image only bullseye (so not saved)
    image_path = image_folder.joinpath("Bullseye.jpg")
    with Image.open(image_path) as image:
        image.load()
    data_dict = {"image": image}
    X.on_receive_image_taken_message(data_dict)

    # Send first image only bullseye (so not saved)
    image_path = image_folder.joinpath("Bullseye.jpg")
    with Image.open(image_path) as image:
        image.load()
    data_dict = {"image": image}
    X.on_receive_image_taken_message(data_dict)

    # Send first image
    image_path = image_folder.joinpath("left_arrow.jpg")
    with Image.open(image_path) as image:
        image.load()
    data_dict = {"image": image}
    X.on_receive_image_taken_message(data_dict)

    # Send second image only bullseye (so not saved)
    image_path = image_folder.joinpath("Bullseye.jpg")
    with Image.open(image_path) as image:
        image.load()
    data_dict = {"image": image}
    X.on_receive_image_taken_message(data_dict)

    # Send second image (predict on finish should be called after this)
    image_path2 = image_folder.joinpath("right_arrow.jpg")
    with Image.open(image_path2) as image2:
        image2.load()
    data_dict2 = {"image": image2}
    X.on_receive_image_taken_message(data_dict2)

    # Send second image (predict on finish should be called after this)
    image_path2 = image_folder.joinpath("right_arrow.jpg")
    with Image.open(image_path2) as image2:
        image2.load()
    data_dict2 = {"image": image2}
    X.on_receive_image_taken_message(data_dict2)
