from mdpalgo.map.obstacle import Obstacle
from enum import IntEnum, unique

@unique
class CellStatus(IntEnum):
    EMPTY = 0 # empty
    START = 1 # starting area
    BOUNDARY = 2 # boundary area around obstacle
    OBS = 3 # obstacle
    VISITED_OBS = 4 # obstacle visited
    PATH = 5 # 5 and above is path to take


class Cell:
    def __init__(self, x_coordinate, y_coordinate, status: CellStatus = CellStatus.EMPTY):
        # self.direction = None
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.status = status
        self.obstacle = None
        self.id = None

    def cell_clicked(self):
        if self.y_coordinate < 4 and self.x_coordinate < 4:
            return
        if self.obstacle is None:
            self.obstacle = Obstacle(self.x_coordinate, self.y_coordinate)
            self.status = CellStatus.OBS
            return
        self.obstacle.obstacle_clicked()
        if self.obstacle.get_direction() is None:
            self.obstacle = None
            self.status = CellStatus.EMPTY

    def create_obstacle(self, dir, id):
        """Create an obstacle and set the cell status accordingly.

        Args:
            dir: direction of the obstacle. If None, the default obstacle
                direction will be chosen.
        """
        self.obstacle = Obstacle(self.x_coordinate, self.y_coordinate, dir)
        self.status = CellStatus.OBS
        self.id=id

    def set_obstacle_boundary_status(self):
        self.status = CellStatus.BOUNDARY

    def set_starting_area_status(self):
        self.status = CellStatus.START

    def set_empty_status(self):
        self.status = CellStatus.EMPTY

    def set_obstacle_visited_status(self):
        self.status = CellStatus.VISITED_OBS

    def set_path_status(self):
        self.status = CellStatus.PATH

    def get_obstacle(self):
        return self.obstacle

    def remove_obstacle(self):
        self.obstacle = None

    def get_obstacle_direction(self):
        if self.obstacle is None:
            return None
        return self.obstacle.get_direction()

    def get_cell_status(self) -> CellStatus:
        return self.status

    def get_xcoord(self):
        return self.x_coordinate

    def get_ycoord(self):
        return self.y_coordinate
