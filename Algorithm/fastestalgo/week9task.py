import logging
import os
from mdpalgo import constants
from mdpalgo.communication.comms import AlgoClient
from mdpalgo.communication.message_parser import MessageType
from mdpalgo.interface.simulator import *
import json

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
                if message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value:
                    self.on_receive_image_taken_message(message_data)

            except (IndexError, ValueError) as e:
                print("Invalid command: " + all_data)

    def on_receive_image_taken_message(self, message_data: dict):
        img_id = self.simulator.get_img_id_from_image_taken(message_data, arrow=True)

        result_message = {
            "type": "IMAGE_RESULTS",
            "data": {
                "obs_id": self.obstacle_id,
                "img_id": img_id
            }
        }

        # send image result string to rpi
        self.send_message_to_rpi(image_result_string)

        # change obstacle_id to 2 after sending first image result
        if self.obstacle_id == 1:
            self.obstacle_id = 2

    def send_message_to_rpi(self, message: str):
        if constants.RPI_CONNECTED:
            self.commsClient.send(message)
