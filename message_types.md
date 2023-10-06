# Assumptions
1. The ultrasonic sensor *automatically* returns distance to obstacle after each sequence of commands (see `NAVIGATION` messages), and is not manually triggered by PC.
2. The camera is *manually* triggered by PC via `GET_IMAGE` messages.


# Overview of messages sent for each task
## Flow of messages for checklist A1 / testing
1. **AR1, RS1:** Android tells STM movement instructions 

## Flow of messages for task 1: image recognition (W8)
1. **AR2, RP1:** Android tells PC obstacle locations and task type=`EXPLORATION`
2. **PR1:** PC sends RPi sequence of movement instructions for STM after calculating path
3. **RS1:** RPi sends individual commands to STM one at a time
   1. **SR1:** STM acknowledges end of each command 
   2. **SR2, RP2:** if emergency stop is triggered by STM for collision avoidance, STM returns ultrasonic sensor output, which is relayed by RPi to PC
4. optionally repeat steps 2-3 if not at planned coordinates/distance from obstacle
5. **PR4, RA1:** pass current coordinates at end of movement sequence to Android for display
6. **PR2, RP3:** PC requests image from RPi, RPi returns image
7. **PR3, RA2:** PC returns image recognition results to Android
8.  repeat steps 2-7 until all obstacles/images identified
9.  repeat steps 2-5 to return to start

## Flow of messages for task 2: fastest car (W9)
1. **AR2, RP1:** Android tells PC obstacle locations and task type=`FASTEST_PATH`
2. **PR1:** PC sends RPi sequence of movement instructions for STM after calculating path
3. **RS1:** RPi sends individual commands to STM one at a time
   1. **SR1:** STM acknowledges end of each command 
   2. **SR2, RP2:** if emergency stop is triggered by STM for collision avoidance, STM returns ultrasonic sensor output, which is relayed by RPi to PC
4. optionally repeat steps 2-3 if not at planned coordinates/distance from obstacle
5. **PR2, RP3:** PC requests image from RPi, RPi returns image
6. **PR3, RA2:** PC returns image recognition results to Android
7. calculate path based on arrow identified in image and repeat steps 2-6 until all images identified
8. repeat steps 2-4 to return to start


# Message types
- `COORDINATES`: RA1 and PR4
- `IMAGE_RESULTS`: RA2 and PR3 
- `IMAGE_TAKEN`: RP3
- `ULTRASONIC`: RP2 (see also SR2)
- `NAVIGATION`: AR1 and PR1 (see also RS1, SR1)
- `PATH`: AR3 and PR2
- `START_TASK`: AR2 and RP1

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
    - AR1 and PR1 are consistent
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
3. path taken by robot in arena, sent by PC to Android at end of run
   ```
    {
        "type": "PATH",
        "data": {
           "path": [[0,1], [1,1], [2,1], [3,1]]
        }
    }
    ```
    - `path` is the list of cells (each a 10x10cm block) traversed by the robot
    - AR3 and PR2 are consistent

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
1. Acknowledgement of command
   ```A```
   - acknowledges that command has been received and completed
2. ultrasonic sensor info // TODO: format TBD
   ```100```
    - the distance in cm from an obstacle, measured by the ultrasonic sensor
    - this message is sent by STM after an emergency stop is triggered for collision avoidance
    - see also RP2 

## RS: RPi to STM 
1. movement instructions from PC/Android: WASD + distance
    ```SF010```
    - while RPi receives a list of commands from PC (see `NAVIGATION` messages - AR1 and PR1), it sends each 5 character command 1 at a time to STM
      - each command is a 5 character code: <L/R/S><F/B>XXX 
      - S/L/R: the first character indicates Straight / Left / Right 
      - F/B: the second character indicates Forward / Backward
      - XXX: the last 3 digits indicate distance in cm for S, or rotation angle for L/R
      - e.g. SB010 is move backwards 10cm, LF090 is turn 90 degrees to the left in the forward direction

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
    - AR1 and PR1 are consistent
2. path taken by robot in arena, sent by PC to Android at end of run
   ```
    {
        "type": "PATH",
        "data": {
           "path": [[0,1], [1,1], [2,1], [3,1]]
        }
    }
    ```
    - `path` is the list of cells (each a 10x10cm block) traversed by the robot
    - AR3 and PR2 are consistent
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
NOTE: messages sent to PC are prepended with message length
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
           "distance": 10,
            "command": "SF010"
        }
    }
    ```
    - this message is sent from RPi to PC when STM triggers an emergency stop to avoid collision
    - `distance` is the distance in cm from an obstacle, measured by the ultrasonic sensor
    - `command` is the last command sent by RPi to the STM before the emergency stop was triggered
    - SR1 and RP2 are consistent
3. raw image for image recognition
    ```
    {
        "type": "IMAGE_TAKEN",
        "data": {
            "image": "..."
        }
    }
    ```
    - `obs_id` is the unique `id` of the obstacle
    - `image` is base64 encoded string representation of the image.

