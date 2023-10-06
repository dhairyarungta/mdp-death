import logging
import json

from communication.message_parser import TaskType
from constants import mdp_constants
from robot.robot import Robot
from algorithm.a_to_b_planner_service_astar import AutoPlanner, RobotMovement
from map.configuration import Pose
from map.grid import Grid

MARGIN = 2


class AtoBPathPlan(object):

    def __init__(self, simulator, grid: Grid, robot: Robot, fastest_route):
        self.filled_coordinates_array = []
        self.simulator = simulator
        self.grid = grid
        self.robot = robot
        self.fastest_route = fastest_route
        self.target_pose: Pose = Pose()  # pose to take a good photo of image
        self.target = None  # list of [x, y, dir, Obstacle_cell]
        self.robot_pose: Pose = self.robot.get_robot_pose()
        self.obstacle_cell = None
        self.collection_of_movements = []  # collection of RobotMovement
        self.movement_string = []
        self.collection_of_robot_pos = []
        self.path_according_to_movements = []  # trail of cells
        self.all_movements_dict = {}
        self.all_take_photo_dict = {}
        self.obstacle_list_rpi = []
        self.skipped_obstacles = []
        self.obstacle_key = None  # the current obstacle key that RPi is going for
        self.num_move_completed_rpi = 0  # completed num moves by RPi to self.obstacle_key
        self.total_num_move_required_rpi = 0  # total required num moves by RPi to self.obstacle_key
        self.auto_planner = AutoPlanner()
        self.full_path = []
        self.robot_pos_string = []

    def start_robot(self):
        # Remove robot starting position from fastest_route
        self.fastest_route.pop(0)

        count_of_obs = 0

        while len(self.fastest_route) != 0:
            count_of_obs += 1
            target = self.fastest_route.pop(0)
            self.plan_path_to(target)

            # self.send_to_rpi()
            # if count_of_obs >= 1:
            #     if mdp_constants.RPI_CONNECTED:
            #         self.send_to_rpi()

        print(f"== A_TO_B_PLANNER > start_robot() | ENDING PATHING")
        self.restart_robot_and_send_to_rpi(self.filled_coordinates_array)

    def plan_path_to(self, target):
        """target is a list [x, y, dir, Cell] where Cell is the obstacle cell
        and (x, y, dir) is the target pose for the car to view the image tag
        """
        print(f"== A_TO_B_PLAN_CTLR > plan_f_p_t() | Current target is {target}")

        self.get_target_pose_obstacle_cell_from(target)
        self.robot_pose = self.robot.get_robot_pose()

        self.reset_collection_of_movements()
        self.reset_path_according_to_movements()
        self.reset_robot_pos_list()
        # else, plan a path using astar search on virtual grid
        try:
            start = list(self.robot.get_robot_pose().to_tuple())
            end = list(self.target_pose.to_tuple())
            cost = 10  # cost per movement
            maze = self.grid.get_virtual_map()
            obstacle_coords = [
                (cell.x_coordinate, cell.y_coordinate) for cell in self.grid.obstacle_cells.values()
            ]
            self.collection_of_movements, self.path_according_to_movements, self.movement_string = self.auto_planner.get_movements_and_path_to_goal(
                maze, cost, start, end, obstacle_coords)
            # [
            #     [[8, 11], [8, 12], [8, 13], [9, 13], [10, 13], [11, 13]],
            #     [[10, 13]],
            #     [[11, 13], [12, 13], [13, 13], [13, 14], [13, 15], [13, 16]],
            #     [[13, 15]]
            # ]
            for ar in self.path_according_to_movements:
                for nested_ar in ar:
                    tmp = []
                    for coord in nested_ar:
                        tmp.append(int(coord))
                    self.filled_coordinates_array.append(tmp)
            print(f"== A_TO_B_PLAN_CTLR > auto_search() | Collection of movements is {self.collection_of_movements}")
            print(f"== A_TO_B_PLAN_CTLR > auto_search() | path according to movements is {self.path_according_to_movements}")
            print(f"== A_TO_B_PLAN_CTLR > auto_search() | MOVEMENT STRING IS {self.movement_string}")
        except Exception as e:
            logging.exception(e)
            # Skip this obstacle first
            print("Search result: ", self.collection_of_movements, " ; Skipping obstacle...")
            self.skip_current_target()
            return

        # execute gray route
        self.execute_planned_path()

    def get_target_id(self, target: list):
        if target[3].id != None:
            return target[3].id
        else:
            return ''

    def get_target_pose_obstacle_cell_from(self, target: list):
        """Get the target pose and obstacle cell from a list of [x, y, dir, Cell]
        """
        self.target = target
        self.target_pose.set_pose(target[:3])
        self.obstacle_cell = target[3]

    def execute_planned_path(self):
        for move_index in range(len(self.collection_of_movements)):
            move = self.collection_of_movements[move_index]
            # print(f"== A_TO_B_PLAN_CTLR > execute_a_s_r | Performing the move: {move}")
            self.robot.perform_move(move)

            path = self.path_according_to_movements[move_index]
            self.draw_path_of_move_on_grid(path)
            # print(f"== A_TO_B_PLAN_CTLR > execute_a_s_r | Drawing the path: {path}")

        self.collection_of_robot_pos.append(self.get_robot_pos())
        print(f"== A_TO_B_PLAN_CTLR > execute_a_s_r | Appending position {self.get_robot_pos()}")
        try:
            self.grid.set_obstacle_as_visited(self.obstacle_cell)
            print(f"== A_TO_B_PLAN_CTLR > execute_a_s_r | Cell {self.obstacle_cell} has been visited")
        except Exception as e:
            logging.exception(e)
            pass
        self.robot.redraw_car_refresh_screen()
        try:
            self.save_path_and_send_to_rpi()
        except Exception as e:
            logging.exception(e)
            pass

    def draw_path_of_move_on_grid(self, cell_coords):
        for x, y in cell_coords:
            self.set_path_status_to_xy_cell(int(x), int(y))

    def skip_current_target(self):
        self.skipped_obstacles.append(self.target)

    def restart_robot_and_send_to_rpi(self, coord_ar):
        msg = {
            "type": "PATH",
            "data": {
               "path": coord_ar,
            }
        }
        print(f"== A_TO_B_PLANNER > restart_robot_and_send_t_r() | Sending {msg}")
        self.simulator.commsClient.send(msg)
        if len(self.skipped_obstacles) == 0:
            print("No skipped obstacles to run")
            self.send_to_rpi()
            return

        print("Restart robot to go to skipped obstacles")
        while len(self.skipped_obstacles) != 0:
            target = self.skipped_obstacles.pop(0)
            self.plan_path_to(target)
            self.send_to_rpi()

    def set_path_status_to_xy_cell(self, x: int, y: int):
        if self.grid.is_xy_coords_within_grid(x, y):
            self.grid.get_cell_by_xycoords(x, y).set_path_status()

    def reset_collection_of_movements(self):
        self.collection_of_movements.clear()

    def reset_movement_string(self):
        self.movement_string.clear()

    def reset_path_according_to_movements(self):
        self.path_according_to_movements.clear()

    def reset_robot_pos_list(self):
        self.collection_of_robot_pos.clear()

    def parse_movements_string_EDITME(self):
        res = {'type': TaskType.TASK_NAVIGATION.value}
        tmp = {'commands': self.movement_string}
        res['data'] = tmp
        # print(self.obstacle_cell.get_obstacle().get_obstacle_id())

        return res
        # movement_list = [
        #     "MOVEMENTS",
        #     self.obstacle_cell.get_obstacle().get_obstacle_id(),
        #     [move.value for move in self.collection_of_movements]
        # ]
        # print("returning", '/'.join([str(elem) for elem in movement_list]))
        # return '/'.join([str(elem) for elem in movement_list])

    def get_current_obstacle_id(self):
        obstacle_id_list = ["OBSTACLE", self.obstacle_cell.get_obstacle().get_obstacle_id()]
        return '/'.join([str(elem) for elem in obstacle_id_list])

    def get_robot_pos(self):
        return (self.robot.grid_x, self.robot.grid_y, self.robot.angle)

    def get_collection_of_robot_pos_string(self):
        return '/'.join([str(pos) for pos in self.collection_of_robot_pos])

    def get_robot_pos_string(self):
        robot_list = ["ROBOT", self.obstacle_cell.get_obstacle().get_obstacle_id(),
                      self.get_collection_of_robot_pos_string()]
        return '/'.join([str(elem) for elem in robot_list])

    def get_take_photo_string(self):
        photo_list = ["PHOTO", self.obstacle_cell.get_obstacle().get_obstacle_id()]
        return '/'.join([str(elem) for elem in photo_list])

    def get_image_result_string(self, target_id):
        image_result_list = ["TARGET", target_id, self.obstacle_key]
        return '/'.join([str(elem) for elem in image_result_list]) + '/'

    def save_path_and_send_to_rpi(self):
        # self.all_movements_dict[self.get_current_obstacle_id()] = self.parse_movements_string_EDITME()
        self.all_movements_dict = self.parse_movements_string_EDITME();
        # self.all_take_photo_dict[self.get_current_obstacle_id()] = self.get_take_photo_string()
        # self.obstacle_list_rpi.append(self.get_current_obstacle_id())
        print(f"== A_TO_B_PLAN_CTLR > save_path_for_rpi | {self.all_movements_dict}")
        print(f"== A_TO_B_PLAN_CTLR > save_path_for_rpi | SENDING MSG")
        self.simulator.commsClient.send(self.all_movements_dict)

        self.reset_collection_of_movements()
        self.reset_robot_pos_list()

    def print_info(self):
        print(self.parse_movements_string_EDITME())
        print(self.get_current_obstacle_id())
        print(self.get_robot_pos_string())
        print(self.get_take_photo_string())

    def send_to_rpi(self):
        if not self.obstacle_list_rpi:
            # self.send_to_rpi_finish_task()
            return

        self.obstacle_key = self.obstacle_list_rpi.pop(0)
        self.reset_num_move_completed_rpi()
        print(f"== A_TO_B_PLAN_CTLR > send_to_rpi() | SENDING THIS TO RPI {self.all_movements_dict}")
        self.simulator.commsClient.send(self.all_movements_dict)
        # print("Remaining obstacles: ", self.obstacle_list_rpi)
        # id = []
        # id.append(str(self.get_target_id(self.target)))
        # self.movement_string = id + self.movement_string
        # self.full_path.append(self.movement_string)
        # self.robot_pos_string.append(",".join(self.robot.robot_pos))
        # self.robot.robot_pos.clear()

    # def send_to_rpi_finish_task(self):
    #     print(f"== A_TO_B > SEND_TO_RPI() |  {self.all_movements_dict}")
    #     self.simulator.commsClient.send(self.all_movements_dict)
    #     # full_path_string = "STM/" + str(self.full_path)
    #     # full_robot_pos_string = "AND/[C10] " + ",".join(self.robot_pos_string)
    #     # print(full_path_string)
    #     # print(full_robot_pos_string)
    #     # try:
    #     #     self.simulator.commsClient.send(full_path_string)  # Send full list of robot coordinates for android to update
    #     #     self.simulator.commsClient.send(full_robot_pos_string)
    #     # except:
    #     #     print('rpi not connected')

    def reset_num_move_completed_rpi(self):
        self.num_move_completed_rpi = 0

    def update_num_move_completed(self, num_moves_completed: int):
        self.num_move_completed_rpi += num_moves_completed

    def is_move_to_current_obstacle_done(self) -> bool:
        return self.num_move_completed_rpi == self.total_num_move_required_rpi

    # def request_photo_from_rpi(self):
    #     self.simulator.commsClient.send(self.all_take_photo_dict[self.obstacle_key])
