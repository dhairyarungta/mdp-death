"""Given a FULL graph:
    + nodes: represent the starting pose and the poses to view the images
        The starting pose is represented as node 0 by default.
    + edges: represent the distance the car needs to move between the nodes
Compute a list of sequences of nodes for a Hamiltonian path
"""

import abc
import itertools
from enum import Enum

import networkx as nx
import numpy as np


class AbstractHamiltonianPathPlanner(metaclass=abc.ABCMeta):
    def __init__(self, graph: nx.Graph, starting_node: int = 0):
        """Initialize the path Planner

        Args:
            graph: complete graph, with edge weights
            starting_node: the node to start from"""
        self.graph = graph
        self.starting_node = starting_node

    @abc.abstractmethod
    def find_path(self):
        """Return list of nodes in Hamiltonian path and length of that path"""
        return


class GreedyHamiltonianPathPlanner(AbstractHamiltonianPathPlanner):
    def find_path(self):
        unvisited = set(self.graph.nodes)

        # the start node is already visited
        #start_node = self.starting_node
        current_node = self.starting_node
        unvisited.remove(current_node)
        path = [current_node]
        path_length = 0

        while unvisited:
            next_node = min(unvisited, key=
            lambda node: self.graph[current_node][node]["weight"])

            path_length += self.graph[current_node][next_node]["weight"]
            current_node = next_node
            unvisited.remove(current_node)
            path.append(current_node)

        return path, path_length


class ExhaustiveHamiltonianPathPlanner(AbstractHamiltonianPathPlanner):
    """Compute shortest hamiltonian path for a complete graph by exhaustive search
    """

    def find_path(self):
        num_nodes = len(self.graph.nodes)
        other_nodes = list(self.graph.adj[self.starting_node])
        shortest_length = np.infty
        shortest_path = ()

        for path in itertools.permutations(other_nodes):
            path_length = sum(
                (self.graph[path[i]][path[i + 1]]["weight"] for i in range(num_nodes - 2)),
                start=self.graph[self.starting_node][path[0]]["weight"])
            if path_length < shortest_length:
                shortest_path = path
                shortest_length = path_length
        shortest_path = [self.starting_node] + list(shortest_path)

        return shortest_path, shortest_length


class HamiltonianPathPlannerType(Enum):
    GREEDY = "greedy"
    EXHAUSTIVE = "exhaustive"


def get_graph_path_planner(planner_type: HamiltonianPathPlannerType
                           ) -> AbstractHamiltonianPathPlanner:
    if planner_type is HamiltonianPathPlannerType.GREEDY:
        return GreedyHamiltonianPathPlanner
    elif planner_type is HamiltonianPathPlannerType.EXHAUSTIVE:
        return ExhaustiveHamiltonianPathPlanner


# Unittest the algorithms on some small inputs
if __name__ == "__main__":
    G = nx.Graph()
    G.add_edges_from([
        (0, 1, {"weight": 7}),
        (0, 2, {"weight": 2}),
        (0, 3, {"weight": 10}),
        (0, 4, {"weight": 1}),
        (1, 2, {"weight": 8}),
        (1, 3, {"weight": 4}),
        (1, 4, {"weight": 5}),
        (2, 3, {"weight": 11}),
        (2, 4, {"weight": 3}),
        (3, 4, {"weight": 6}),
    ])

    greedy_planner = GreedyHamiltonianPathPlanner(G)
    path, path_length = greedy_planner.find_path()
    assert path == [0, 4, 2, 1, 3]
    assert path_length == 16

    exhaustive_planner = ExhaustiveHamiltonianPathPlanner(G)
    path, path_length = exhaustive_planner.find_path()
    assert path == [0, 2, 4, 1, 3]
    assert path_length == 14

    assert get_graph_path_planner(
        HamiltonianPathPlannerType.GREEDY) == GreedyHamiltonianPathPlanner
    assert get_graph_path_planner(
        HamiltonianPathPlannerType.EXHAUSTIVE) == ExhaustiveHamiltonianPathPlanner
