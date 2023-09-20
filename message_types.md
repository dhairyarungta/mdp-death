# Assumptions
1. The ultrasonic sensor *automatically* returns distance to obstacle after each sequence of commands (see `NAVIGATION` messages), and is not manually triggered by PC.
2. The camera is *manually* triggered by PC via `GET_IMAGE` messages.


# Overview of messages sent for each task
## Flow of messages for checklist A1 / testing
1. **AR1, RS1:** Android tells STM movement instructions 

## Flow of messages for task 1: image recognition (W8)
1. **AR2, RP1:** Android tells PC obstacle locations and task type=`EXPLORATION`
2. **PR1, RS1:** PC tells STM movement instructions after calculating path
3. **SR1, RP2:** STM acknowledges end of movement sequence by sending ultrasonic sensor feedback
4. optionally repeat steps 2-3 if not at planned coordinates/distance from obstacle
5. **PR4, RA1:** pass current coordinates at end of movement sequence to Android for display
6. **PR2, RP3:** PC requests image from RPi, RPi returns image
7. **PR3, RA2:** PC returns image recognition results to Android
8. repeat steps 2-7 until all obstacles/images identified
9. repeat steps 2-5 to return to start

## Flow of messages for task 2: fastest car (W9)
1. **AR2, RP1:** Android tells PC obstacle locations and task type=`FASTEST_PATH`
2. **PR1, RS1:** PC tells STM movement instructions after calculating path
3. **SR1, RP2:** STM acknowledges end of movement sequence by sending ultrasonic sensor feedback
4. optionally repeat steps 2-3 if not at planned coordinates/distance from obstacle
5. **PR2, RP3:** PC requests image from RPi, RPi returns image
6. **PR3, RA2:** PC returns image recognition results to Android
7. calculate path based on arrow identified in image and repeat steps 2-6 until all images identified
8. repeat steps 2-4 to return to start


# Message types
- `NAVIGATION`: AR1, RS1, and PR1
- `START_TASK`: AR2 and RP1
- `COORDINATES`: RA1 and PR4
- `GET_IMAGE`: PR2
- `IMAGE_RESULTS`: RA2 and PR3 
- `ULTRASONIC`: SR1 and RP2
- `IMAGE`: RP3

## AR: Android to RPi
1. directions to directly control STM 
    ```
    {
        "type": "NAVIGATION",
        "data": {
           "commands": ["SF010", "RF090", "SB050", "LB090"]
        }
    }
    ```
    - `commands` is a list of directions (WASD) followed by distance 
      - each command is a 5 character code: <L/R/S><F/B>XXX 
      - S/L/R: the first character indicates Straight / Left / Right 
      - F/B: the second character indicates Forward / Backward
      - XXX: the last 3 digits indicate distance in cm for S, or rotation angle for L/R
      - e.g. SB010 is move backwards 10cm, LF090 is turn 90 degrees to the left in the forward direction
    - AR1, RS1, and PR1 are consistent
2. begin exploration: task type, start, obstacles (unique IDs)
   ```
    {
        "type": "START_TASK",
        "data": {
           "task": "EXPLORATION",
           "robot": {"id": "R", "x": 1, "y": 1, "dir": N},
           "obstacles": [
                {"id": "00", "x": 4, "y": 15, "dir": S},
                {"id": "01", "x": 16, "y": 17, "dir": W}
           ]
        }
    }
    ```
    - `task` is either `EXPLORATION` (task 1, W8), or `FASTEST_PATH` (task 2, W9)
    - `robot` is the location of the robot (`id` = `R`), including `x` and `y` coordinates, and orientation (`dir`)
    - `obstacles` is a list of obstacle locations, each with unique `id` starting from 0, including `x` and `y` coordinates, and orientation (`dir`)
    - AR2 and RP1 are consistent 

## RA: RPi to Android
1. current coordinates of robot from PC
    ```
    {
        "type": "COORDINATES",
        "data": {
           "robot": {"id": "R", "x": 1, "y": 1, "dir": N}
        }
    }
    ```
    - `robot` is the location of the robot (`id` = `R`), including `x` and `y` coordinates, and orientation (`dir`)
    - RA1 and PR4 are consistent
2. image recognition results from PC: obstacle image ID and coordinates/direction
    ```
    {
        "type": "IMAGE_RESULTS",
        "data": {
           "obs_id": "00", 
           "img_id": "36", 
        }
    }
    ```
    - `obs_id` is the unique `id` of the obstacle
    - `img_id` is the image ID identified by the image recognition algorithms running on PC
    - RA2 and PR3 are consistent

## SR: STM to RPi
1. ultrasonic sensor info // TODO: this might not be feasible
   ```
    {
        "type": "ULTRASONIC",
        "data": {
           "distance": 10
        }
    }
    ```
    - `distance` is the distance in cm from an obstacle, measured by the ultrasonic sensor
    - SR1 and RP2 are consistent
2. Acknowledgement of command
   ```A```
   - acknowledges that command has been received and completed
   - TODO: do we need a way to show WHICH command was received and completed, like should it echo?

## RS: RPi to STM 
1. movement instructions from PC/Android: WASD + distance
    ```
    {
        "type": "NAVIGATION",
        "data": {
           "commands": ["SF010", "RF090", "SB050", "LB090"]
        }
    }
    ```
    - `commands` is a list of directions (WASD) followed by distance 
      - each command is a 5 character code: <L/R/S><F/B>XXX 
      - S/L/R: the first character indicates Straight / Left / Right 
      - F/B: the second character indicates Forward / Backward
      - XXX: the last 3 digits indicate distance in cm for S, or rotation angle for L/R
      - e.g. SB010 is move backwards 10cm, LF090 is turn 90 degrees to the left in the forward direction
    - AR1, RS1, and PR1 are consistent
2. trigger ultrasonic sensor

## PR: PC to RPi
1. movement instructions for STM
    ```
    {
        "type": "NAVIGATION",
        "data": {
           "commands": ["SF010", "RF090", "SB050", "LB090"]
        }
    }
    ```
    - `commands` is a list of directions (WASD) followed by distance 
      - each command is a 5 character code: <L/R/S><F/B>XXX 
      - S/L/R: the first character indicates Straight / Left / Right 
      - F/B: the second character indicates Forward / Backward
      - XXX: the last 3 digits indicate distance in cm for S, or rotation angle for L/R
      - e.g. SB010 is move backwards 10cm, LF090 is turn 90 degrees to the left in the forward direction
    - AR1, RS1, and PR1 are consistent
2. trigger camera to take a picture and return it to PC for image recognition
    ```
    {
        "type": "GET_IMAGE",
        "data": {
            "obs_id_": "00", 
        }
    }
    ```
    - `obs_id` is the unique `id` of the obstacle
3. image recognition results
    ```
    {
        "type": "IMAGE_RESULTS",
        "data": {
           "obs_id": "00", 
           "img_id": "36"
        }
    }
    ```
    - `obs_id` is the unique `id` of the obstacle
    - `img_id` is the image ID identified by the image recognition algorithms running on PC
    - RA2 and PR3 are consistent
4. current coordinates of robot
    ```
    {
        "type": "COORDINATES",
        "data": {
           "robot": {"id": "R", "x": 1, "y": 1, "dir": N}
        }
    }
    ```
    - `robot` is the location of the robot (`id` = `R`), including `x` and `y` coordinates, and orientation (`dir`)
    - RA1 and PR4 are consistent

## RP: RPi to PC
1. start task (exploration / fastest path)
    ```
    {
        "type": "START_TASK",
        "data": {
           "task": "EXPLORATION",
           "robot": {"id": "R", "x": 1, "y": 1, "dir": N},
           "obstacles": [
                {"id": "00", "x": 4, "y": 15, "dir": S},
                {"id": "01", "x": 16, "y": 17, "dir": W}
           ]
        }
    }
    ```
    - `task` is either `EXPLORATION` (task 1, W8), or `FASTEST_PATH` (task 2, W9)
    - `robot` is the location of the robot (`id` = `R`), including `x` and `y` coordinates, and orientation (`dir`)
    - `obstacles` is a list of obstacle locations, each with unique `id` starting from 0, including `x` and `y` coordinates, and orientation (`dir`)
    - AR2 and RP1 are consistent 
2. ultrasonic sensor info from STM
    ```
    {
        "type": "ULTRASONIC",
        "data": {
           "distance": 10
        }
    }
    ```
    - `distance` is the distance in cm from an obstacle, measured by the ultrasonic sensor
    - SR1 and RP2 are consistent
3. raw image for image recognition
    ```
    {
        "type": "IMAGE",
        "data": {
            "obs_id": "00", 
            "img_bytes": b'...'
        }
    }
    ```
    - `obs_id` is the unique `id` of the obstacle
    - `img_bytes` is the encoded image of the obstacle, to be identified by image recognition algorithms running on PC


