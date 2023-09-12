"""
This script has the following main functions:
1) converts target locations on grid to graph nodes and edges (node: image_id, edge: id1, id2, cost)
2) computes the A star heuristics for the edge cost
3) converts shortest path nodes back to target locations on grid
"""

import networkx as nx
from mdpalgo.algorithm.astar import AStar


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

        self.start_cell_x = start_cell_x
        self.start_cell_y = start_cell_y
        self.start_cell = (start_cell_x, start_cell_y, 0, None)
        self.start_node = Node(self.start_cell)

        self.target_grid_locations = self.grid.get_target_locations()
        self.G = nx.Graph()

        self.graph_nodes = []
        self.graph_edges = []

        self.AStar = AStar(self.grid, self.start_cell_x, self.start_cell_y)

        self.ordered_targets = []

    def convert_targets_and_start_cell_to_nodes(self, target_grid_locations, start_node):
        # convert targets to nodes and append to graph_nodes list
        for target in target_grid_locations:
            self.graph_nodes.append(Node(target))

        # convert start cell to node and append to graph_nodes list
        self.graph_nodes.append(start_node)

        # print("NODES: ", self.graph_nodes)

    def compute_edge_cost(self, node1, node2):
        """
        Computes edge cost between two nodes using AStar heuristics
        """
        # compute total cost between node1 and node2
        weight_turn = 0.5
        weight_obstacle = 0
        weight_displacement = 3

        # cost based on displacement
        displacement = weight_displacement * self.AStar.get_displacement(
            [node1.x, node1.y],
            [node2.x, node2.y])

        # cost based on the difference in the direction of the target and the robot
        cost_turn = weight_turn * self.AStar.direction_diff_to_weight(node2.cell, node1.cell)

        # cost based on the number of obstacles in the box created with the robot position and the target
        cost_obstacle = weight_obstacle * self.AStar.cost_by_obstacle(node2.x, node2.y, node1.x, node1.y)

        # total cost is sum of all costs
        total_cost = displacement + cost_turn + cost_obstacle

        return total_cost

    def create_edges(self):
        """
        Creates edges for graph
        """
        for node in self.graph_nodes:
            other_nodes = [x for x in self.graph_nodes if x != node]
            for other_node in other_nodes:
                self.graph_edges.append((node.image_id, other_node.image_id,
                                         {"weight": self.compute_edge_cost(node, other_node)}))

        # print("EDGES: ", self.graph_edges)

    def create_graph(self):
        """
        Creates graph with nodes and edges, where:
        - nodes represent starting cell + target locations on grid
        - edges represent cost between 2 cells
        """
        self.convert_targets_and_start_cell_to_nodes(self.target_grid_locations, self.start_node)
        self.create_edges()
        self.G.add_edges_from(self.graph_edges)

        return self.G

    def convert_shortest_path_to_ordered_targets(self, shortest_path):
        """
        Convert shortest path nodes to ordered target locations on grid
        """
        start = self.start_cell
        self.ordered_targets.append(self.start_cell)
        for location in shortest_path[1:]:
            curr_target = next(filter(lambda x: x[3].obstacle.obstacle_id == location, self.target_grid_locations))
            self.ordered_targets.append(curr_target)
        #self.ordered_targets.append(self.start_cell)

        return self.ordered_targets
