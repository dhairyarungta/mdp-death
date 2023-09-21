# Collection of colours
from enum import Enum

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (192, 192, 192)
BLUE = (50, 100, 150)
LIGHT_BLUE = (100, 255, 255)
LIGHT_RED = (255, 144, 144)
LIGHT_GREEN = (154, 247, 182)
SIMULATOR_BG = (93, 177, 222)

# Collection of robot constants
NORTH = 0
SOUTH = 180
EAST = -90
WEST = 90
ROBOT_W = 30
ROBOT_H = 30

# Starting grid positions of car
ROBOT_STARTING_X = 1
ROBOT_STARTING_Y = 1
ROBOT_STARTING_ANGLE = NORTH
TURNING_RADIUS = 3

# this is the buffer from the boundary of the grid
# negative values mean the cell representing the robot can move outside of the grid
BOUNDARY_BUFFER = 1

FPS = 60

# RPI Connection
RPI_CONNECTED = False

# Headless execution
# Imagine a NSWE "+" sign hovering above the robot.
# if Headless = True, this NSWE "+" sign will stay the same throughout the bot's operation, fixed when the robot starts. Even if the bot turns left/right or changes direction, it will stay in the same orientation.
# if Headless = False, this NSWE "+" sign will rotate together with the front of the bot when it turns left/right or changes direction.
HEADLESS = False

GRP_14 = "192.168.14.1"
PORT = 8888
