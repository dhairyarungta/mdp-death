from queue import PriorityQueue
import numpy as np

from mdpalgo import constants
from mdpalgo.map.cell import CellStatus
from mdpalgo.map.configuration import Pose
from mdpalgo.robot.robot import RobotMovement

class ImprovedNode:
    """
        A node class for A* Pathfinding
        parent is parent of the current Node
        position is current position of the Node in the maze
        g is cost from start to current Node
        h is heuristic based estimated cost for current Node to end Node
        f is total cost of present node i.e. :  f = g + h
    """

    def __init__(self, parent=None, pose:list=None):
        self.parent = parent
        self.pose = Pose(pose)
        self.move_from_parent: RobotMovement = None
        self.displacement_from_parent: np.ndarray

        self.g = 0
        self.h = 0
        self.f = 0

class Distance:
    """
        A class with implementation of distances between two 2D points
    """
    def manhattan(self, xA: int, yA: int, xB: int, yB: int) -> int:
        return abs(xA-xB) + abs(yA-yB)

    def squared_euclidean(self, xA: int, yA: int, xB: int, yB: int) -> int:
        return (xA - xB) ** 2 + (yA - yB) ** 2

class AutoPlanner():
    def __init__(self):
        self.TURNING_RADIUS = constants.TURNING_RADIUS
        # if robot node is at this distance away from obstacle, safe!
        self.safe_squared_distance = 8
        # map movement to a relative vector wrt the current direction
        self.map_move_to_relative_displacement =  {
            RobotMovement.FORWARD: [0, 1],
            RobotMovement.BACKWARD: [0, -1],
            RobotMovement.FORWARD_RIGHT: [self.TURNING_RADIUS, self.TURNING_RADIUS],
            RobotMovement.FORWARD_LEFT: [-self.TURNING_RADIUS, self.TURNING_RADIUS],
            RobotMovement.BACKWARD_RIGHT: [self.TURNING_RADIUS, -self.TURNING_RADIUS],
            RobotMovement.BACKWARD_LEFT: [-self.TURNING_RADIUS, -self.TURNING_RADIUS],
        }
        self.map_move_to_relative_direction = {
            RobotMovement.FORWARD: constants.NORTH,
            RobotMovement.BACKWARD: constants.NORTH,
            RobotMovement.FORWARD_RIGHT: constants.EAST,
            RobotMovement.FORWARD_LEFT: constants.WEST,
            RobotMovement.BACKWARD_RIGHT: constants.WEST,
            RobotMovement.BACKWARD_LEFT: constants.EAST,
        }
        self.turning_moves = {
            RobotMovement.FORWARD_RIGHT,
            RobotMovement.FORWARD_LEFT,
            RobotMovement.BACKWARD_RIGHT,
            RobotMovement.BACKWARD_LEFT,
        }

        self.collision_statuses = [CellStatus.BOUNDARY, CellStatus.OBS, CellStatus.VISITED_OBS]

        # change the current direction to rotation matrix
        self.direction_to_rotation_matrixes = {
            constants.NORTH: np.array([[1, 0],
                                       [0, 1]]),
            constants.SOUTH: np.array([[-1, 0],
                                       [0, -1]]),
            constants.EAST: np.array([[0, 1],
                                      [-1, 0]]),
            constants.WEST: np.array([[0, -1],
                                      [1, 0]]),
        }

        self.direction_to_unit_forward_vector = {
            constants.NORTH: np.array([0, 1]),
            constants.SOUTH: np.array([0, -1]),
            constants.EAST: np.array([1, 0]),
            constants.WEST: np.array([-1, 0]),
        }

        # turning cost = straight cost * turning factor
        self.turning_factor = 5 # assume perfect circle, about 4.71

        self.node_index_in_yet_to_visit = 2
        self.distance_calculator = Distance()
        self.obs_coords = []
        self.full_path = []
    def initialize_node(self, node_position: list) -> ImprovedNode:
        """f, h, g are all initialized to 0"""
        return ImprovedNode(None, tuple(node_position))

    def initialize_counters(self):
        """Initialize the counters used to halt the algorithm"""
        self.outer_iterations = 0

    def increment_counters(self):
        self.outer_iterations += 1

    def set_max_iterations(self):
        self.max_iterations = (len(self.maze) // 2) ** 10

    def does_iterations_exceed_max(self):
        return self.outer_iterations > self.max_iterations

    def initialize_yet_to_visit(self):
        # in this list we will put all node that are yet_to_visit for exploration.
        # From here we will find the lowest cost node to expand next
        self.yet_to_visit = PriorityQueue()
        # map all nodes that ever appear in yet to visit to its lowest g
        self.yet_to_visit_lowest_cost = {}

    def initialize_visited_nodes(self):
        # we will put all node those already explored so that we
        # don't explore it again
        self.visited_list = set() # set of tuples (x, y, dir)

    def add_node_to_yet_to_visit(self, node: ImprovedNode):
        self.yet_to_visit.put((node.f, self.get_id(), node))
        lowest_g = min(
            self.yet_to_visit_lowest_cost.get(
                node.pose.to_tuple(), np.infty),
            node.g)
        self.yet_to_visit_lowest_cost[node.pose.to_tuple()] = lowest_g

    def reset_id(self):
        # id for the node in the yet_to_visit_queue
        self.id = 0

    def get_id(self):
        self.id += 1
        return self.id

    def get_node_from_yet_to_visit(self) -> ImprovedNode:
        """Remove and return the node with lowest f from queue"""
        return self.yet_to_visit.get()[self.node_index_in_yet_to_visit]

    def is_yet_to_visit_empty(self):
        return self.yet_to_visit.empty()

    def set_maze(self, maze):
        self.maze = maze
        self.get_maze_sizes()
        self.set_boundary_for_nodes()

    def get_maze_sizes(self):
        self.size_x, self.size_y = np.shape(self.maze)

    def is_in_collision(self, node: ImprovedNode) -> bool:
        if self.is_robot_within_maze_at_node(node):
            return self.maze[node.pose.x][node.pose.y] in self.collision_statuses

        # outside maze, check if the buffer zone allow this
        if self.buffer_zone_size >= 0:
            return True

        # check that manhattan distance to any obstacle is
        # above a certain threshold
        if not self.obs_coords: # the obstacle information is not provided
            return True

        for obs_x, obs_y in self.obs_coords:
            distance = self.distance_calculator.squared_euclidean(
                node.pose.x, node.pose.y,
                obs_x, obs_y)
            if distance < self.safe_squared_distance:
                return True

        return False

    def is_node_unreachable_from_parent(self, node: ImprovedNode) -> bool:
        if self.is_in_collision(node):
            return True

        parent_node = node.parent
        move = node.move_from_parent
        displacement_from_current = node.displacement_from_parent

        # for turning move, also check the corner of the move
        if move in self.turning_moves:
            unit_forward_vector = self.direction_to_unit_forward_vector[parent_node.pose.direction]
            corner_displacement = np.matmul(unit_forward_vector, displacement_from_current) * unit_forward_vector
            corner_node = ImprovedNode(None, [corner_displacement[0] + parent_node.pose.x,
                                              corner_displacement[1] + parent_node.pose.y,
                                              constants.NORTH]) # the direction is not important since we only checking collision
            return self.is_in_collision(corner_node)


    def is_goal_reached(self) -> bool:
        for potential_goal_node in self.potential_goal_nodes:
            if self.current_node.pose == potential_goal_node.pose:
                return True
        return False

    def add_node_to_visited(self, node: ImprovedNode):
        self.visited_list.add(node.pose.to_tuple())

    def set_boundary_for_nodes(self):
        """The node can be slightly outside of the maze"""
        self.buffer_zone_size = constants.BOUNDARY_BUFFER
        self.right_boundary = self.size_x - 1 - self.buffer_zone_size # right most node that robot is not out of maze
        self.top_boundary = self.size_y - 1 - self.buffer_zone_size # top most node that robot is not out of maze

    def is_robot_within_maze_at_node(self, node: ImprovedNode):
        """Check if the robot will be within maze if staying in this
        node."""
        return (0 <= node.pose.x < self.size_x) and (0 <= node.pose.y < self.size_y)

    def is_robot_within_boundary_at_node(self, node: ImprovedNode):
        """Check if the robot will be within boundary if staying in this
        node. Boundary may be bigger or smaller than maze"""
        return (self.buffer_zone_size <= node.pose.x <= self.right_boundary) and (self.buffer_zone_size <= node.pose.y <= self.top_boundary)

    def get_children_of_current_node(self):
        # Generate children from all adjacent squares
        self.children_current_node = []
        i = 0

        for move in self.map_move_to_relative_displacement:
            new_node = self.get_child_node_after_move(move)

            i += 1
            # Make sure within range (check if within maze boundary)
            if not self.is_robot_within_boundary_at_node(new_node):
                continue

            # Make sure node is reachable
            if self.is_node_unreachable_from_parent(new_node):
                continue

            # Append
            self.children_current_node.append(new_node)

    def get_child_node_after_move(self, move: RobotMovement):
        relative_displacement = self.map_move_to_relative_displacement[move]
        displacement_from_current_node = self.get_absolute_vector(relative_displacement, self.current_node.pose.direction)

        relative_direction_from_current_node = self.map_move_to_relative_direction[move]
        # Get node position
        node_position = [
            self.current_node.pose.x + displacement_from_current_node[0],
            self.current_node.pose.y + displacement_from_current_node[1],
            self.get_absolute_direction(relative_direction_from_current_node, self.current_node.pose.direction)]
        child_node = ImprovedNode(self.current_node, node_position)
        child_node.move_from_parent = move
        child_node.displacement_from_parent = displacement_from_current_node
        return child_node

    def get_absolute_direction(self, relative_direction: int, current_direction: int) -> int:
        resultant_direction = relative_direction + current_direction
        if resultant_direction > 180:
            return resultant_direction - 360
        elif resultant_direction <= -180:
            return resultant_direction + 360
        return resultant_direction

    def get_absolute_vector(self, relative_vector: list, current_direction) -> list:
        rotation_matrix = self.direction_to_rotation_matrixes[current_direction]
        return np.matmul(rotation_matrix, relative_vector).astype(int)


    def is_node_already_visited(self, node: ImprovedNode):
        return node.pose.to_tuple() in self.visited_list

    def heuristics(self, node: ImprovedNode):
        """Return estimated cost to go to the end node"""
        xA, yA = node.pose.x, node.pose.y
        xB, yB = self.end_node.pose.x, self.end_node.pose.y
        return self.distance_calculator.manhattan(xA, yA, xB, yB)

    def is_node_higher_cost_than_yet_to_visit(self, node: ImprovedNode):
        """Check if node is already in yet to visit and has higher cost than
        stored in yet to visit"""
        if node.pose.to_tuple() in self.yet_to_visit_lowest_cost:
            return node.g > self.yet_to_visit_lowest_cost[node.pose.to_tuple()]
        return False

    def set_straight_cost(self, cost):
        self.straight_cost = cost

    def get_cost_current_node_to_child(self, child_node: ImprovedNode) -> int:
        move_to_child = child_node.move_from_parent
        weighted_cost = self.straight_cost

        if self.is_turning_move(move_to_child):
            weighted_cost *= self.turning_factor

        return weighted_cost

    def is_turning_move(self, move: RobotMovement):
        return move in self.turning_moves

    def set_neighbours_as_potential_goal_nodes(self):
        """Set the neighbouring nodes of the end nodes as potential targets"""
        target_x = self.end_node.pose.x
        target_y = self.end_node.pose.y
        target_direction = self.end_node.pose.direction

        # Get the coordinates of other neighbour potential target cells
        if target_direction == constants.NORTH:
            neighbour_coords = [(target_x - 1, target_y),
                                (target_x + 1, target_y)]
        elif target_direction == constants.SOUTH:
            neighbour_coords = [(target_x + 1, target_y),
                                (target_x - 1, target_y)]
        elif target_direction == constants.EAST:
            neighbour_coords = [(target_x, target_y + 1),
                                (target_x, target_y - 1)]
        elif target_direction == constants.WEST:
            neighbour_coords = [(target_x, target_y - 1),
                                (target_x, target_y + 1)]

        for neighbour_x, neighbour_y in neighbour_coords:
            neighbour_node = ImprovedNode(None, [neighbour_x, neighbour_y, target_direction])
            if self.is_robot_within_boundary_at_node(neighbour_node) and not self.is_in_collision(neighbour_node):
                self.add_potential_goal_node(neighbour_node)

    def reset_potential_goal_nodes(self):
        self.potential_goal_nodes = list()

    def add_potential_goal_node(self, node: ImprovedNode=None):
        self.potential_goal_nodes.append(node)

    def get_movements_and_path_to_goal(self, maze, cost, start, end, obs_coords: list):
        self.set_maze(maze)
        self.set_straight_cost(cost)
        # Create start and end node with initialized values for g, h and f
        self.start_node = self.initialize_node(start)
        self.end_node = self.initialize_node(end)
        self.obs_coords = obs_coords # list of coordinates of obstacle cell
        self.reset_potential_goal_nodes()
        self.add_potential_goal_node(self.end_node)
        self.initialize_yet_to_visit()
        self.initialize_visited_nodes()
        self.reset_id()
        self.add_node_to_yet_to_visit(self.start_node)

        # Adding a stop condition. This is to avoid any infinite loop and stop
        # execution after some reasonable number of steps
        self.initialize_counters()
        self.set_max_iterations()

        # Loop until you find the end

        while not self.is_yet_to_visit_empty():

            # Every time any node is referred from yet_to_visit list, counter of limit operation incremented
            self.increment_counters()

            self.current_node = self.get_node_from_yet_to_visit()

            # if we hit this point return the path such as it may be no solution or
            # computation cost is too high
            if self.does_iterations_exceed_max():
                print("Giving up on pathfinding too many iterations")
                break

            self.add_node_to_visited(self.current_node)

            # test if goal is reached or not, if yes then return the path
            if self.is_goal_reached():
                return self.reconstruct_movements_and_path(self.current_node)

            self.get_children_of_current_node()

            # Loop through children
            for child in self.children_current_node:
                # Child is on the visited list (search entire visited list)
                if self.is_node_already_visited(child):
                    continue

                # Create the f, g, and h values
                child.g = self.current_node.g + self.get_cost_current_node_to_child(child)

                # Heuristic costs calculated here, this is using MANHATTAN distance
                child.h = self.heuristics(child)

                child.f = child.g + child.h

                # Child is already in the yet_to_visit list and child has
                # higher g cost than that in yet_to_visit
                if self.is_node_higher_cost_than_yet_to_visit(child):
                    continue

                # Add the child to the yet_to_visit list
                self.add_node_to_yet_to_visit(child)
        raise Exception("no path found to goal")

    def reconstruct_movements_and_path(self, current_node: ImprovedNode) -> list:
        """Return a list of string of movements"""
        node = current_node
        movements = []
        movements_str = []
        path = []

        while node.pose != self.start_node.pose:
            # grow the path backwards and backtrack
            movements_str.append(node.move_from_parent.value)
            movements.append(node.move_from_parent)
            path.append(self.get_path_from_parent(node))
            node = node.parent

        movements.reverse() # reverse the path from start to goal
        movements_str.reverse()
        path.reverse()
        movements_str = self.process_movement_string(movements_str)
        self.full_path.append(movements_str)
        return movements, path, movements_str

    def process_movement_string(self,arr):
        if not arr:
            return []
        # Initialize variables to keep track of current tag and count
        current_tag = arr[0]
        current_count = 1

        # Initialize empty list to store tagged array
        tagged_arr = []

        # Loop through each element in the array, starting from the second element
        for i in range(1, len(arr)):
            # If the current element is the same as the previous element, increment count
            if arr[i] == current_tag:
                current_count += 1
            # If the current element is different from the previous element, add the tagged version of the previous tag and count to the tagged array
            else:
                if current_tag in ['FR','FL','BR','BL']:
                    current_count_str = str(current_count*90).zfill(3)
                else:
                    current_count_str = str(current_count*10).zfill(3)
                tagged_arr.append(current_tag + current_count_str)
                # Reset current tag and count to the new element
                current_tag = arr[i]
                current_count = 1
        if current_tag in ['FR','FL','BR','BL']:
            current_count_str = str(current_count*90).zfill(3)
        else:
            current_count_str = str(current_count*10).zfill(3)
        tagged_arr.append(current_tag + current_count_str)

        # Print the tagged array
        return tagged_arr
    
    def get_path_from_parent(self, node) -> list:
        parent_node = node.parent
        move = node.move_from_parent
        displacement_from_parent = node.displacement_from_parent
        path = []

        # for turning move, also check the corner of the move
        if move in self.turning_moves:
            unit_forward_vector = self.direction_to_unit_forward_vector[parent_node.pose.direction]
            straight_displacement = np.matmul(unit_forward_vector, displacement_from_parent) * unit_forward_vector
            unit_straight_vector = (straight_displacement/self.TURNING_RADIUS).astype(int)

            corner_x = straight_displacement[0] + parent_node.pose.x
            corner_y = straight_displacement[1] + parent_node.pose.y

            sideward_displacement = displacement_from_parent - straight_displacement
            unit_sideward_vector = (sideward_displacement/self.TURNING_RADIUS).astype(int)

            # add the path to the corner of the turn
            for i in range(1, self.TURNING_RADIUS + 1):
                path.append(
                [
                    parent_node.pose.x + i * unit_straight_vector[0],
                    parent_node.pose.y + i * unit_straight_vector[1],
                ])

            # add the path from the corner to the end of the turn
            for i in range(1, self.TURNING_RADIUS + 1):
                path.append(
                [
                    corner_x + i * unit_sideward_vector[0],
                    corner_y + i * unit_sideward_vector[1],
                ])

        else: # straight moves are straight forward
            path.append([node.pose.x, node.pose.y])
        return path


if __name__ == "__main__":
    _ = CellStatus.EMPTY
    c = CellStatus.EMPTY # current node
    s = CellStatus.EMPTY # start node
    t = CellStatus.EMPTY # target node
    o = CellStatus.OBS
    b = CellStatus.BOUNDARY
    maze = np.array([[_, _, _, _, _, _, _, _, _, _],
                     [_, s, _, _, _, _, _, _, _, _],
                     [_, _, _, _, _, _, b, b, b, _],
                     [_, _, _, _, t, _, b, o, b, _],
                     [_, _, _, _, _, _, b, b, b, _],
                     [_, _, _, _, _, _, _, _, _, _],
                     [_, c, _, _, _, _, _, _, _, _],
                     [_, _, _, _, _, _, _, _, _, _],
                     [_, _, _, _, _, _, _, _, _, _],
                     [_, _, _, _, _, _, _, _, _, _],])
    cost = 10
    start = [1, 1, constants.NORTH]
    end = [3, 4, constants.NORTH]
    auto_planner = AutoPlanner()
    auto_planner.set_maze(maze)
    auto_planner.current_node = ImprovedNode(None, [6, 1, constants.EAST])
    auto_planner.get_children_of_current_node()
    for node in auto_planner.children_current_node:
        print(f"Child: (x, y, dir) = ({node.pose.x}, {node.pose.y}, {node.pose.direction})")
    movements = auto_planner.get_movements_and_path_to_goal(maze, cost, start, end)[0]
    #assert movements == ['F', 'F', 'F', 'BR', 'B', 'B', 'FR']

    # test the transformation methods
    relative_vector = auto_planner.map_move_to_relative_displacement[RobotMovement.FORWARD]

    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.NORTH)
    assert (abs_vector == np.array([0, 1])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.SOUTH)
    assert (abs_vector == np.array([0, -1])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.WEST)
    assert (abs_vector == np.array([-1, 0])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.EAST)
    assert (abs_vector == np.array([1, 0])).all()

    relative_vector = auto_planner.map_move_to_relative_displacement[RobotMovement.BACKWARD_LEFT]

    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.NORTH)
    assert (abs_vector == np.array([-3, -3])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.SOUTH)
    assert (abs_vector == np.array([3, 3])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.WEST)
    assert (abs_vector == np.array([3, -3])).all()
    abs_vector = auto_planner.get_absolute_vector(relative_vector, constants.EAST)
    assert (abs_vector == np.array([-3, 3])).all()
