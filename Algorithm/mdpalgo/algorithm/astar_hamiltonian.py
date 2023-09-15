"""
This script has the following main functions:
1) converts target locations on grid to graph nodes and edges (node: image_id, edge: id1, id2, cost)
2) computes the A star heuristics for the edge cost
3) converts shortest path nodes back to target locations on grid
"""
import math

import networkx as nx

class Node(object):
    def __init__(self, target):
        if target[3] is None:
            self.image_id = "start"
        else:
            self.image_id = target[3].obstacle.obstacle_id
        self.cell = target
        self.x = target[0]
        self.y = target[1]


class AStarHamiltonian(object):
    def __init__(self, grid, start_cell_x, start_cell_y):
        self.grid = grid
        self.cells = grid.get_cells()

        self.start_cell = (start_cell_x, start_cell_y, 0, None)
        self.start_node = Node(self.start_cell)

        print(f"== ASTAR_HAMIL > init() | Locations to visit are {self.grid.get_target_locations()}")
        self.target_grid_locations = self.grid.get_target_locations()
        self.G = nx.Graph()

        self.graph_nodes = []
        self.graph_edges = []

        self.ordered_targets = []

    def convert_targets_and_start_cell_to_nodes(self, target_grid_locations, start_node):
        # convert targets to nodes and append to graph_nodes list
        for target in target_grid_locations:
            self.graph_nodes.append(Node(target))

        # convert start cell to node and append to graph_nodes list
        self.graph_nodes.append(start_node)

    def compute_edge_cost(self, node1, node2):
        """
        Computes edge cost between two nodes using AStar heuristics
        """
        cost_total = 0

        # cost based on displacement
        weight_displacement_multiplier = 3
        cost_displacement = weight_displacement_multiplier * self.get_straight_line_displacement(
            [node1.x, node1.y],
            [node2.x, node2.y])
        cost_total += cost_displacement

        # cost based on the difference in the direction of the target and the robot
        weight_turn_multiplier = 0.5
        cost_turn = weight_turn_multiplier * self.direction_diff_heuristic_multiplier(node2.cell, node1.cell)
        cost_total += cost_turn

        # cost based on the number of obstacles in the box created with the robot position and the target
        # weight_obstacle_multiplier = 0
        # cost_obstacle = weight_obstacle_multiplier * self.cost_by_obstacle(node2.x, node2.y, node1.x, node1.y)
        # cost_total += cost_obstacle

        return cost_total

    def create_graph(self):
        """
        Creates graph with nodes and edges, where:
        - nodes represent starting cell + target locations on grid
        - edges represent cost between 2 cells
        """
        self.convert_targets_and_start_cell_to_nodes(self.target_grid_locations, self.start_node)

        # Creates edges for graph
        for node in self.graph_nodes:
            other_nodes = [x for x in self.graph_nodes if x != node]
            for other_node in other_nodes:
                distance = self.compute_edge_cost(node, other_node)
                print(f"== ASTAR_HAMIL > create_graph() | LINKING {node.image_id} TO {other_node.image_id} WITH DISTANCE {distance}")
                self.graph_edges.append((node.image_id, other_node.image_id,
                                         {"weight": distance}))

        self.G.add_edges_from(self.graph_edges)
        return self.G

    def convert_shortest_path_to_ordered_targets(self, shortest_path):
        """
        Convert the shortest path nodes to ordered target locations on grid
        """
        self.ordered_targets.append(self.start_cell)
        for location in shortest_path[1:]:
            curr_target = next(filter(lambda x: x[3].obstacle.obstacle_id == location, self.target_grid_locations))
            self.ordered_targets.append(curr_target)
        print(f"== ASTAR_HAMIL > convert_s_p_t_o_t() | Before is {shortest_path} and after is {self.ordered_targets}")
        return self.ordered_targets

    def get_straight_line_displacement(self, pos1, pos2):
        return math.sqrt((abs(pos1[0] - pos2[0])**2 + abs(pos1[1] - pos2[1])**2))

    def direction_diff_heuristic_multiplier(self, target_direction, robot_direction):
        if min(abs(target_direction[2] - robot_direction[2]), abs(robot_direction[2] - target_direction[2])) == 0:
            if robot_direction[2] == 0:
                if target_direction[1] < robot_direction[1]:
                    return 8
            elif robot_direction[2] == 90:
                if target_direction[0] > robot_direction[0]:
                    return 8
            elif robot_direction[2] == 180:
                if target_direction[1] > robot_direction[1]:
                    return 8
            elif robot_direction[2] == -90:
                if target_direction[0] < robot_direction[0]:
                    return 8
            if robot_direction[0] == target_direction[0]:
                return 0
            return 4

        # TODO: refine further
        elif min(abs(target_direction[2] - robot_direction[2]), abs(robot_direction[2] - target_direction[2])) == 90:
            return 2

        elif min(abs(target_direction[2] - robot_direction[2]), abs(robot_direction[2] - target_direction[2])) == 180:
            return 6
        return 0

    # def cost_by_obstacle(self, x1, y1, x2, y2):
    #     small_x, big_x, small_y, big_y = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
    #     cost = 0
    #     for obstacle_id in self.grid.get_obstacle_cells().values():
    #         obstacle_x, obstacle_y = obstacle_id.get_xcoord(), obstacle_id.get_ycoord()
    #         if small_x - 2 <= obstacle_x <= big_x + 2 and small_y - 2 <= obstacle_y <= big_y + 2:
    #             cost += 3
    #     return cost ** 2
