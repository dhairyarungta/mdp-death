"""
Parse the raw message from RPi and return a convenient data structure
"""
from enum import Enum
import parse
import base64
import cv2
import numpy as np
from PIL import Image

class MessageType(Enum):
    """Message type is determined by the first token
    """
    START_TASK = "START" # first token is "START"
    UPDATE_ROBOT_POSE = "DONE" # current pose of the robot

class TaskType(Enum):
    """Type of tasks"""
    TASK_EXPLORE = "EXPLORE" # task for exploring all images (week 8)
    TASK_PATH = "PATH" # task for fastest path (week 9)

class MessageParser:
    """Class to parse all the messages received from RPi"""
    def __init__(self):
        pass

    def parse(self, message: str) -> dict:
        """Parse raw into a dictionary for easier manipulation

        The tokens in message are separated by "/".

        returns:
            A data dictionary containing the following (key, value):
                "type": type of message (MessageType)
                "data": data dictionary for this message type (dict)
        """
        # the first token is unique among different message types
        try:
            message_type = message.partition("/")[0]
            message_type = MessageType(message_type)
        except IndexError:
            raise ValueError("Message is not in the correct format separated by /")
        except ValueError:
            raise ValueError("Message type not valid.")

        message_dict = {"type": message_type, "data": {}}
        if message_type == MessageType.START_TASK:
            message_dict["data"] = self.parse_start_task(message)
        elif message_type == MessageType.UPDATE_ROBOT_POSE:
            message_dict["data"] = self.parse_update_robot_pose(message)
        elif message_type == MessageType.IMAGE_TAKEN:
            message_dict["data"] = self.parse_image_taken(message)
        return message_dict

    def parse_start_task(self, message: str) -> dict:
        """Parse message for start task into a dictionary for easier manipulation

        Raises:
            ValueError: if `message` is not in the correct format

        Example:
            >>> message = "START/EXPLORE/(R,1,1,0)/(00,04,15,-90)/(01,16,17,90)"
            >>> parse_start_task(message)
            {"task": TaskType.TASK_EXPLORE, "robot": {"id": "R", "x": 1, "y": 1, "dir": 0},
            "obs": [{"id": "00", "x": 4, "y": 15, "dir": -90}, {"id": "01", "x": 16, "y": 17, "dir": 90}]}
            >>> message = "START/PATH"
            >>> parse_start_task(message)
            {"task": TaskType.TASK_PATH}
        """
        try:
            task = message.split("/")[1]
            task = TaskType(task)
        except IndexError:
            raise ValueError("Start task message does not contain the task type")
        except ValueError:
            raise ValueError(f"Start task message contains invalid task type: {task}")

        data_dict = {"task": task}
        if task == TaskType.TASK_PATH:
            pass
        elif task == TaskType.TASK_EXPLORE: # task for week 8
            data_dict = {**data_dict, **self.parse_explore_task(message)}
        else: # redundancy, just to make sure
            raise ValueError(f"Start task type not yet implemented: {task}")

        return data_dict

    def parse_explore_task(self, message: str) -> dict:
        """Parse message for explore task into a dictionary for easier manipulation

        Raises:
            ValueError: if `message` is not in the correct format

        Example:
            >>> message = "START/EXPLORE/(R,1,1,0)/(00,04,15,-90)/(01,16,17,90)"
            >>> parse_explore_task(message)
            {"task": "EXPLORE", "robot": {"id": "R", "x": 1, "y": 1, "dir": 0},
            "obs": [{"id": "00", "x": 4, "y": 15, "dir": -90}, {"id": "01", "x": 16, "y": 17, "dir": 90}]}
        """
        # Pattern for start_task message for Explore task
        self.explore_task_pattern = parse.compile("{command:w}/{task:w}/({id:w},{x:d},{y:d},{dir:d})/{obs}")
        self.obs_pattern = parse.compile("({id:w},{x:d},{y:d},{dir:d})")

        data_dict = {}
        parse_result = self.explore_task_pattern.parse(message)
        if not parse_result:
            raise ValueError("Message is not in the correct format of EXPLORE task")
        if (parse_result["id"] != "R"):
            raise ValueError("Message is not in the correct format of EXPLORE task: robot id must be R")
        data_dict["robot"] = {key: parse_result[key] for key in ["id", "x", "y", "dir"]}
        data_dict["obs"] = []
        for obs_data in self.obs_pattern.findall(parse_result["obs"]):
            data_dict["obs"].append(obs_data.named)

        return data_dict

    def parse_update_robot_pose(self, message: str) -> dict:
        """Parse message for update robot pose into a dictionary for easier
        manipulation

        Example:
            >>> message = "DONE/5/9-8"
            >>> parse_update_robot_pose(message)
            {"status": "DONE", "num_move", "obstacle_key": {"x": 9, "y": 8}}
        """
        self.update_robot_pose_pattern = parse.compile("{status:w}/{num_move:d}/{x:d}-{y:d}")
        parse_result = self.update_robot_pose_pattern.parse(message)
        if not parse_result:
           raise ValueError("Message is not in the correct format of update robot pose")

        try:
            data_dict = {}
            data_dict["status"] = parse_result["status"]
            data_dict["num_move"] = parse_result["num_move"]
            data_dict["obstacle_key"] = {key: parse_result[key] for key in ["x", "y"]}
        except KeyError:
            raise ValueError("Message is not in the correct format of update robot pose")

        return data_dict

if __name__ == "__main__":
    parser = MessageParser()

    # Test the method to parse EXPLORE task messages
    message = "START/EXPLORE/(R,1,1,0)/(00,04,15,-90)/(01,16,17,90)/(02,12,11,180)/(03,07,03,0)/(04,17,04,90)"
    assert parser.parse(message) == {
        'type': MessageType.START_TASK,
        'data': {
            'task': TaskType.TASK_EXPLORE,
            'robot': {'id': 'R', 'x': 1, 'y': 1, 'dir': 0},
            'obs': [{'id': '00', 'x': 4, 'y': 15, 'dir': -90},
                    {'id': '01', 'x': 16, 'y': 17, 'dir': 90},
                    {'id': '02', 'x': 12, 'y': 11, 'dir': 180},
                    {'id': '03', 'x': 7, 'y': 3, 'dir': 0},
                    {'id': '04', 'x': 17, 'y': 4, 'dir': 90}
                    ]
        }
    }

    # Test the method to parse fastest PATH task messages
    message = "START/PATH"
    assert parser.parse(message) == {
        'type': MessageType.START_TASK,
        'data': {
            'task': TaskType.TASK_PATH
        }
    }

    # Test the method to parse UPDATE robot pose after done with movements and pictures
    message = "DONE/5/9-8"
    assert parser.parse(message) == {
        'type': MessageType.UPDATE_ROBOT_POSE,
        'data': {
            "status": "DONE",
            "num_move": 5,
            "obstacle_key": {"x": 9, "y": 8}
        }
    }
