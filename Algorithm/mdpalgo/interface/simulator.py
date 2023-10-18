import base64
import logging
import os
import queue
import threading
import json

import pygame

from constants import mdp_constants
import pygame
from algorithm.hamiltonian_planner_controller_euclidean_and_angle import HamiltonianPlannerController
from algorithm.hamiltonian_planner_service_nearest_or_greedy import BruteForcePermutationHamiltonianPathPlanner, GreedyHamiltonianPathPlanner
from algorithm.a_to_b_planner_controller import AtoBPathPlan
from communication.comms import AlgoClient
from communication.message_parser import MessageType, TaskType
from image_rec import image_rec
from interface.panel import Panel
from map.grid import Grid
from robot.robot import Robot

from mdpalgo.map.cell import Cell, CellStatus
from mdpalgo.map.obstacle import Obstacle
import argparse
# Set the HEIGHT and WIDTH of the screen
WINDOW_SIZE = [960, 660]


class Simulator:

    def __init__(self, id_list=[]):
        self.obs_ar = []
        self.obs_idx = 0
        self.obs_hashmap = {}
        self.obs_id_click = 1

        self.grid_surface = None
        self.commsClient = None

        # Initialize pygame
        self.root = pygame
        self.root.init()
        self.root.display.set_caption("MDP Algorithm Simulator")
        self.screen = None
        if not mdp_constants.HEADLESS:
            self.screen = pygame.display.set_mode(WINDOW_SIZE)
            self.screen.fill(mdp_constants.SIMULATOR_BG)

        # Callback methods queue - for passing of callback functions from worker thread to main UI thread
        self.callback_queue = queue.Queue()

        # Astar class
        self.astar = None
        # Path planner class
        self.a_to_b_path_planner = None
        # Astar hamiltonian class
        self.hamiltonian_planner_ctlr = None
        # Hamiltonian path planner class
        self.hamiltonian_planner_svc = None

        # This is the margin around the left and top of the grid on screen display
        self.grid_from_screen_top_left = (120, 120)
        # Initialise 20 by 20 Grid
        self.grid = Grid(20, 20, 20, self.grid_from_screen_top_left)
        if not mdp_constants.HEADLESS:
            # Draw the grid
            self.redraw_grid()

        # Initialise side panel with buttons
        self.panel = Panel(self.screen)

        # Used to manage how fast the screen updates
        # self.clock = pygame.time.Clock()
        self.startTime = pygame.time.get_ticks() / 1000
        self.ticks = 0

        # Car printing process
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "car.png")
        car_image = pygame.image.load(image_path)
        self.car = Robot(self, self.screen, self.grid, mdp_constants.ROBOT_W, mdp_constants.ROBOT_H,
                         mdp_constants.ROBOT_STARTING_X, mdp_constants.ROBOT_STARTING_Y, mdp_constants.ROBOT_STARTING_ANGLE,
                         car_image)
        # Draw the car
        self.car.draw_car()

        # parser to parse messages from RPi
        # self.parser = MessageParser()

        # count of 'no image result' exception
        self.no_image_result_count = 0

    def redraw_grid(self):
        self.grid_surface = self.grid.get_updated_grid_surface()
        self.screen.blit(self.grid_surface, self.grid_from_screen_top_left)

    def run(self):

        # Loop until the user clicks the close button.
        done = False
        print('HEADLESS is:', mdp_constants.HEADLESS)  # default is False

        # -------- Main Program Loop -----------
        if mdp_constants.HEADLESS:  # to simplify implementation, we use 2 threads even if headless
            print("Waiting to connect")
            self.start_algo_client()
            while True:
                try:
                    self.handle_worker_callbacks()
                except queue.Empty:  # raised when queue is empty
                    continue

        else:
            while not done:
                # Check for callbacks from worker thread
                while True:
                    try:
                        # TODO what is this
                        self.handle_worker_callbacks()
                    except queue.Empty:  # raised when queue is empty
                        break

                # this is constantly running in a separate thread from handle_worker_callbacks()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        # User clicks the mouse. Get the position
                        pos = pygame.mouse.get_pos()
                        if self.is_pos_clicked_within_grid(pos):
                            x, y = self.grid.pixel_to_grid((pos[0], pos[1]))
                            self.obs_hashmap[str(x) + "-" + str(y)] = self.obs_id_click
                            self.obs_id_click += 1
                            self.grid.grid_clicked(pos[0], pos[1])
                            self.redraw_grid()
                            self.car.draw_car()  # Redraw the car

                        else:  # otherwise, area clicked is outside of grid
                            self.check_button_clicked(pos)

                now = pygame.time.get_ticks() / 1000
                if now - self.startTime > 1 / mdp_constants.FPS:
                    self.startTime = now
                    self.root.display.flip()

        # Be IDLE friendly. If you forget this line, the program will 'hang' on exit.
        print("closing")
        self.root.quit()

    def is_pos_clicked_within_grid(self, pos):
        grid_from_screen_left = self.grid_from_screen_top_left[0]
        grid_from_screen_top = self.grid_from_screen_top_left[1]

        grid_pixel_size_x, grid_pixel_size_y = self.grid.get_total_pixel_size()
        if grid_from_screen_left < pos[0] < grid_from_screen_left + grid_pixel_size_x and \
            grid_from_screen_top < pos[1] < grid_from_screen_top + grid_pixel_size_y:
            return True
        return False

    def start_algo_client(self):
        """Connect to RPi wifi server and start a thread to receive messages """
        self.commsClient = AlgoClient()
        self.commsClient.connect()
        mdp_constants.RPI_CONNECTED = True
        self.receiving_process_EDITME()

    def handle_worker_callbacks(self):
        """Check for callbacks from worker thread and handle them

        Raises:
            queue.Empty if the callback queue is empty
        """
        callback = self.callback_queue.get(False)  # doesn't block
        if isinstance(callback, list):
            logging.info("Current callback: \n%s", callback)
            logging.info("Logging 1: ", str(callback[1]))
            # todo what is this
            callback[0](callback[1])
        else:
            callback()

    def receiving_process_EDITME(self):
        """
        Method to be run in a separate thread to listen for commands from the socket
        Methods that update the UI must be passed into self.callback_queue for running in the main UI thread
        Running UI updating methods in a worker thread will cause a flashing effect as both threads attempt to update the UI
        """

        while True:
            try:
                all_data = self.commsClient.recv()
                message_type_and_data = json.loads(all_data)
                print('message type: ', message_type_and_data['type'])
                message_data = message_type_and_data["data"]
                if message_type_and_data["type"] == MessageType.START_TASK.value:
                    self.on_receive_start_task_message(message_data)

                elif message_type_and_data["type"] == MessageType.IMAGE_TAKEN.value:
                    self.on_receive_image_taken_message(message_data)

                # elif message_type_and_data["type"] == MessageType.UPDATE_ROBOT_POSE:
                #     self.on_receive_update_robot_pose(message_data)


            except (IndexError, ValueError) as e:
                print(e)
                print("Invalid command: " + all_data.decode())

    def on_receive_start_task_message(self, message_data: dict):
        if message_data['task'] == TaskType.TASK_EXPLORATION.value:  # Week 8 Task
            # Reset first
            self.reset_button_clicked()
            # Set robot starting pos
            robot_params = message_data['robot']
            logging.info("Setting robot position: %s", robot_params)
            robot_x, robot_y, robot_dir = int(robot_params["x"]), int(robot_params["y"]), robot_params["dir"]
            if robot_dir == "N":
                robot_dir = 0
            elif robot_dir == "S":
                robot_dir = 180
            elif robot_dir == "E":
                robot_dir = -90
            elif robot_dir == "W":
                robot_dir = 90
            self.car.update_robot(robot_dir, self.grid.grid_to_pixel((robot_x, robot_y)))
            self.car.redraw_car_refresh_screen()

            # Create obstacles given parameters
            logging.info("Creating obstacles...")
            for obstacle in message_data["obstacles"]:
                logging.info("Obstacle: %s", obstacle)
                id, grid_x, grid_y, dir = obstacle["id"], int(obstacle["x"]), int(obstacle["y"]), obstacle["dir"]
                if dir == "N":
                    dir = 0
                elif dir == "S":
                    dir = 180
                elif dir == "E":
                    dir = -90
                elif dir == "W":
                    dir = 90
                self.grid.create_obstacle([id, grid_x, grid_y, dir])
                self.obs_hashmap[str(grid_x) + "-" + str(grid_y)] = id

            # Update grid, start explore
            self.car.redraw_car_refresh_screen()

            logging.info("[AND] Doing path calculation...")
            self.start_button_clicked()

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

    def on_receive_image_taken_message(self, message_data: dict):
        img_id = self.get_img_id_from_image_taken(message_data)
        result_message = {
            "type": "IMAGE_RESULTS",
            "data": {
                "obs_id": self.obs_ar[self.obs_idx],
                "img_id": img_id
            }
        }
        self.obs_idx += 1
        self.commsClient.send(result_message)

    # def on_receive_update_robot_pose(self, message_data: dict):
    #     print("Received updated robot pose")
    #     status = message_data["status"]
    #     if status == "DONE":
    #         self.a_to_b_path_planner.update_num_move_completed(message_data["num_move"])
    #     else:
    #         raise ValueError("Unimplemented response for updated robot pose")

    def reprint_screen_and_buttons(self):
        self.screen.fill(mdp_constants.SIMULATOR_BG)
        self.panel.redraw_buttons()

    def check_button_clicked(self, pos):
        # Check if start button was pressed first:
        start_button = self.panel.buttons[-1]
        x, y, l, h = start_button.get_xy_and_lh()
        if (x < pos[0] < (l + x)) and (y < pos[1] < (h + y)):
            self.start_button_clicked()
            return

        for button in self.panel.buttons[0:-1]:
            x, y, l, h = button.get_xy_and_lh()
            if (x < pos[0] < (l + x)) and (y < pos[1] < (h + y)):
                button_func = self.panel.get_button_clicked(button)
                if button_func == "RESET":
                    print("Reset button pressed.")
                    self.reset_button_clicked()
                if button_func == "CONNECT":
                    print("Connect button pressed.")
                    self.start_algo_client()
                elif button_func == "DISCONNECT":
                    print("Disconnect button pressed.")
                    self.commsClient.disconnect()
                    mdp_constants.RPI_CONNECTED = False
                    self.commsClient = None

                # for testing purposes
                elif button_func == "FORWARD":
                    self.car.move_forward()
                elif button_func == "BACKWARD":
                    self.car.move_backward()
                elif button_func == "FORWARD_RIGHT":
                    self.car.move_forward_steer_right()
                elif button_func == "FORWARD_LEFT":
                    self.car.move_forward_steer_left()
                elif button_func == "BACKWARD_RIGHT":
                    self.car.move_backward_steer_right()
                elif button_func == "BACKWARD_LEFT":
                    self.car.move_backward_steer_left()
                else:
                    return
            else:
                pass

    # called either when you:
    #   - manually click the start button
    #   - receive a message to do the pathfinding
    def start_button_clicked(self):
        print("START button clicked!")

        # Get the fastest route using AStar Hamiltonian
        if len(self.grid.get_target_locations()) != 0:
            self.hamiltonian_planner_ctlr = HamiltonianPlannerController(self.grid, self.car.grid_x, self.car.grid_y)
            graph = self.hamiltonian_planner_ctlr.create_graph()

            self.hamiltonian_planner_svc = BruteForcePermutationHamiltonianPathPlanner(graph, "start")
            shortest_path, path_length = self.hamiltonian_planner_svc.find_path()
            # print(self.obs_hashmap)
            for coord in range(1, len(shortest_path)):
                # print(shortest_path[coord])
                self.obs_ar.append(self.obs_hashmap[shortest_path[coord]])
            shortest_path_implementation = self.hamiltonian_planner_ctlr.convert_shortest_path_to_ordered_targets(shortest_path)
            self.car.optimized_target_locations = shortest_path_implementation[1:]
            print(f"== SIMULATOR > start_b_c() | Final shortest route is {str(shortest_path)}")
            print(f"== SIMULATOR > start_b_c() | Obstacle list is {self.obs_ar}")
            self.a_to_b_path_planner = AtoBPathPlan(self, self.grid, self.car, shortest_path_implementation)

            self.a_to_b_path_planner.start_robot()

            print(f"== SIMULATOR > start_b_c() | Parsing images to print")

    def reset_button_clicked(self):
        self.grid.reset_data()
        self.redraw_grid()
        self.car.reset()
        self.obs_ar = []
        self.obs_idx = 0
        self.obs_hashmap = {}
        self.obs_id_click = 0


if __name__ == "__main__":
    # Set info logging mode
    logging.basicConfig(level=logging.INFO)

    x = Simulator()

    # Test the method to parse Android messages
    message = "START/EXPLORE/(R,1,1,0)/(00,04,15,-90)/(01,16,17,90)/(02,12,11,180)/(03,07,03,0)/(04,17,04,90)"
    data_dict = x.parser.parse(message)["data"]
    # Test the threading without Android connected
    thread = threading.Thread(target=lambda: x.on_receive_start_task_message(data_dict))
    thread.start()
    x.run()
