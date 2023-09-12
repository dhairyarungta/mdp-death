"""
Explanation on coordinate system:
    * the display screen pixels:
        + origin: top left
        + x-axis: pointing right
        + y-axis: pointing down
    * the grid object uses a coordinate system with
        + origin: bottom left
        + x-axis: pointing right
        + y-axis: pointing up
"""


import logging

from mdpalgo import constants
import pygame
from mdpalgo.map.cell import Cell, CellStatus
import numpy as np

# This sets the margin between each Cell
MARGIN = 2

COLOR_DICT = {
    CellStatus.EMPTY: constants.WHITE,
    CellStatus.START: constants.BLUE,
    CellStatus.BOUNDARY: constants.LIGHT_RED,
    CellStatus.OBS: constants.BLACK,
    CellStatus.VISITED_OBS: constants.GREEN,
    CellStatus.PATH: constants.GRAY,
}

class Grid(object):

    def __init__(self, grid_column: int, grid_row: int, block_size: int, grid_from_screen_top_left: tuple):
        self.size_x = grid_column
        self.size_y = grid_row
        self.max_x = self.size_x - 1
        self.max_y = self.size_y - 1
        self.start_zone_size = 4
        self.block_size = block_size # size in cm of 1 square cell
        # This is the margin around the top and left of the grid on screen
        # display
        self.outer_margin_x_pixel = grid_from_screen_top_left[0] # pixel from left
        self.outer_margin_y_pixel = grid_from_screen_top_left[1] # pixel from top
        self.cells = np.empty((self.size_x, self.size_y), dtype=Cell)
        self.initialize_cells()
        self.optimized_target_locations = None
        self.obstacle_cells = {}
        self.reset_data()
        self.obstacle_statuses = [CellStatus.OBS, CellStatus.VISITED_OBS]

    def initialize_cells(self):
        for x in range(self.size_x):
            for y in range(self.size_y):
                self.cells[x][y] = Cell(x, y)

        self.set_start_zone()

    def set_start_zone(self):
        for x in range(self.start_zone_size):
            for y in range(self.start_zone_size):
                self.cells[x][y].set_starting_area_status()


    def reset_data(self):
        """Reset data in all grid cells"""
        self.obstacle_cells.clear()
        for x in range(self.size_x):
            for y in range(self.size_y):
                self.cells[x][y].remove_obstacle()
                self.cells[x][y].set_empty_status()

        self.set_start_zone()

    def get_block_size(self):
        return self.block_size

    def get_cells(self):
        return self.cells

    def get_cell_by_xycoords(self, x, y) -> Cell:
        return self.cells[x][y]

    def get_obstacle_cells(self):
        return self.obstacle_cells

    def get_obstacle_coords(self):
        return [[obstacle_cell.get_xcoord(), obstacle_cell.get_ycoord()] for obstacle_cell in self.obstacle_cells.values()]

    def get_target_locations(self):
        target_locations = []
        for obstacle_cell in self.obstacle_cells.values():
            # Get target grid positions and NSEW direction that car's centre has to reach for image rec
            target_grid_x, target_grid_y = obstacle_cell.get_xcoord(), obstacle_cell.get_ycoord()
            obstacle_direction = obstacle_cell.get_obstacle_direction()
            target_direction = constants.NORTH
            if obstacle_direction == constants.NORTH:
                target_direction = constants.SOUTH
                target_grid_x, target_grid_y = obstacle_cell.get_xcoord(), obstacle_cell.get_ycoord() + 4
            elif obstacle_direction == constants.SOUTH:
                target_direction = constants.NORTH
                target_grid_x, target_grid_y = obstacle_cell.get_xcoord(), obstacle_cell.get_ycoord() - 4
            elif obstacle_direction == constants.EAST:
                target_direction = constants.WEST
                target_grid_x, target_grid_y = obstacle_cell.get_xcoord() + 4, obstacle_cell.get_ycoord()
            elif obstacle_direction == constants.WEST:
                target_direction = constants.EAST
                target_grid_x, target_grid_y = obstacle_cell.get_xcoord() - 4, obstacle_cell.get_ycoord()

            target_loc = (target_grid_x, target_grid_y, target_direction, obstacle_cell)
            target_locations.append(target_loc)

        return target_locations

    def create_obstacle(self, arglist):
        id, grid_x, grid_y, dir = arglist[0], arglist[1], arglist[2],arglist[3]
        # Set that location to one
        cell = self.get_cell_by_xycoords(grid_x, grid_y)
        cell.create_obstacle(dir,id)

        self.add_cell_to_obstacle_list(cell)
        self.set_obstacle_boundary_cells_around(cell)

    def get_virtual_map(self):
        # Get virtual map contains just the cell status
        def get_cell_status(cell: Cell):
            return cell.get_cell_status()

        return np.vectorize(get_cell_status)(self.cells)

    def is_obstacle_status(self, cell_status: CellStatus):
        return cell_status in self.obstacle_statuses

    def get_obstacle_key_from_xy_coords(self, x, y) -> str:
        return f"{x}-{y}"

    def remove_cell_from_obstacle_list(self, cell: Cell):
        obs_key_to_remove = self.get_obstacle_key_from_xy_coords(cell.get_xcoord(), cell.get_ycoord())
        self.obstacle_cells.pop(obs_key_to_remove)

    def add_cell_to_obstacle_list(self, cell: Cell):
        self.obstacle_cells[cell.get_obstacle().get_obstacle_id()] = cell

    def grid_clicked(self, pixel_x, pixel_y):
        # Change the x/y screen coordinates to grid coordinates
        grid_x, grid_y = self.pixel_to_grid((pixel_x, pixel_y))
        selected_cell = self.get_cell_by_xycoords(grid_x, grid_y)
        previous_status = selected_cell.get_cell_status()
        selected_cell.cell_clicked()
        current_status = selected_cell.get_cell_status()

        logging.info("Clicked (x,y): (" + str(pixel_x) + "," + str(pixel_y) + "); Grid coordinates: " + str(selected_cell.get_xcoord()) + " " + str(selected_cell.get_ycoord())
                     + "; Direction: " + str(selected_cell.get_obstacle_direction()))

        if self.is_obstacle_status(previous_status) and self.is_obstacle_status(current_status):
            return

        elif self.is_obstacle_status(previous_status) and not self.is_obstacle_status(current_status):
            self.remove_cell_from_obstacle_list(selected_cell)
            self.unset_obstacle_boundary_cells(selected_cell)
            for remaining_obstacle_cell in self.obstacle_cells.values():
                self.set_obstacle_boundary_cells_around(remaining_obstacle_cell)

        elif not self.is_obstacle_status(previous_status) and self.is_obstacle_status(current_status):
            self.add_cell_to_obstacle_list(selected_cell)
            self.set_obstacle_boundary_cells_around(selected_cell)

        else:
            print("Clicked on a cell that cannot be chosen as obstacle cell.")
        
    def get_boundary_cells_coords(self, cell: Cell):
        """Return a list of coordinates [x_coord, y_coord] of the cells
        surrounding a given cell, within a 2 cell radius (1 for diagonal)."""
        x, y = cell.get_xcoord(), cell.get_ycoord()
        boundary_cells = [
            [x - 1, y + 1], [x, y + 1], [x + 1, y + 1],
            [x - 1, y    ],             [x + 1, y    ],
            [x - 1, y - 1], [x, y - 1], [x + 1, y - 1]
        ]
        return boundary_cells

    def set_obstacle_boundary_cells_around(self, obstacle_cell: Cell):
        """For an obstacle cell, set the statuses of the cells around it to
        boundary status"""
        if not self.is_obstacle_status(obstacle_cell.get_cell_status()):
            raise Exception("Attempt to set boundary around a non-obstacle cell.")

        boundary_cells = self.get_boundary_cells_coords(obstacle_cell)
        # Set status of cells around obstacle as boundary
        for x, y in boundary_cells:
            if not self.is_xy_coords_within_grid(x, y):
                continue

            boundary_cell = self.get_cell_by_xycoords(x, y)
            if not self.is_obstacle_status(boundary_cell.get_cell_status()):
                boundary_cell.set_obstacle_boundary_status()

    def is_x_coord_within_grid(self, x):
        return 0 <= x <= self.max_x
    def is_y_coord_within_grid(self, y):
        return 0 <= y <= self.max_y
    def is_xy_coords_within_grid(self, x, y):
        return self.is_x_coord_within_grid(x) and self.is_y_coord_within_grid(y)

    def unset_obstacle_boundary_cells(self, removed_obstacle_cell):
        """When an obstacle cell is removed, unset the statuses of boundary
        cells around it.

        Note that this function does not take into account if these boundary
        cells also belong to another obstacle. The best thing to do after unset
        all the boundary of removed obstacle cells is to set boundary for all
        the remaining obstacle cells."""
        if self.is_obstacle_status(removed_obstacle_cell):
            raise Exception("Attempted to remove boundary cells from an existing obstacle. Remove the obstacle before doing this!")

        boundary_cells = self.get_boundary_cells_coords(removed_obstacle_cell)
        # Unset status of cells around obstacle
        for x, y in boundary_cells:
            if not self.is_xy_coords_within_grid(x, y):
                continue

            removed_obstacle_cell = self.get_cell_by_xycoords(x, y)
            if removed_obstacle_cell.get_cell_status() == CellStatus.BOUNDARY:
                removed_obstacle_cell.set_empty_status()

    def set_obstacle_as_visited(self, obstacle_cell):
        obstacle_cell.set_obstacle_visited_status()

    def get_updated_grid_surface(self) -> pygame.Surface:
        if constants.HEADLESS:
            return
        self.grid_surface = pygame.Surface(self.get_total_pixel_size())
        self.grid_surface.fill(constants.BLACK)
        # Draw the grid
        for grid_x in range(self.size_x):
            for grid_y in range(self.size_y):
                cell = self.get_cell_by_xycoords(grid_x, grid_y)
                color = COLOR_DICT[cell.get_cell_status()]
                cell_surface = pygame.Surface((self.block_size, self.block_size))
                cell_surface.fill(color)

                if self.is_obstacle_status(cell.get_cell_status()):
                    # display obstacle direction with a red bar
                    obstacle_direction = cell.get_obstacle_direction()
                    pygame.draw.rect(
                        cell_surface,
                        constants.RED,
                        pygame.Rect(0, 0, self.block_size, 8))
                    cell_surface = pygame.transform.rotate(cell_surface, obstacle_direction)

                self.grid_surface.blit(cell_surface,
                    (
                        (MARGIN + self.block_size) * grid_x + MARGIN,
                        (MARGIN + self.block_size) * (self.max_y - grid_y) + MARGIN,
                    ))
        return self.grid_surface

    def grid_to_pixel(self, pos: tuple):
        pixel_x = (pos[0]) * (self.block_size + MARGIN) + self.outer_margin_x_pixel + (self.block_size + MARGIN) / 2
        pixel_y = (self.max_y - pos[1]) * (self.block_size + MARGIN) + self.outer_margin_y_pixel + (self.block_size + MARGIN) / 2
        return [pixel_x, pixel_y]

    def pixel_to_grid(self, pos):
        grid_x = int((pos[0] - self.outer_margin_x_pixel) // (self.block_size + MARGIN))
        grid_y = int(self.max_y - ((pos[1] - self.outer_margin_y_pixel) // (self.block_size + MARGIN)))
        return [grid_x, grid_y]

    def get_total_pixel_size(self) -> tuple:
        # there are always (num_cell + 1) margin for (num_cell) cells
        size_x_pixel = self.size_x * (self.block_size + MARGIN) + MARGIN
        size_y_pixel = self.size_y * (self.block_size + MARGIN) + MARGIN
        return (size_x_pixel, size_y_pixel)
