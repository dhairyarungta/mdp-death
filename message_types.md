# Assumptions
1. The ultrasonic sensor *automatically* returns distance to obstacle after each sequence of commands (see `NAVIGATION` messages), and is not manually triggered by PC.
2. The camera is *manually* triggered by PC via `GET_IMAGE` messages.


# Overview of messages sent for each task
## Flow of messages for checklist A1 / testing
1. **AR1, RS1:** Android tells STM movement instructions 

## Flow of messages for task 1: image recognition (W8)
1. **AR2, RP1:** Android tells PC obstacle locations and task type=`EXPLORATION`
2. **PR1:** PC sends RPi sequence of movement instructions for STM after calculating path
3. **RA3**: RPi sends Android list of cells traversed by robot on the way to this obstacle
4. **RS1:** RPi sends individual commands to STM one at a time
   1. **SR1:** STM acknowledges end of each command 
   2. **SR2, RP2:** if emergency stop is triggered by STM for collision avoidance, STM returns ultrasonic sensor output, which is relayed by RPi to PC
5. optionally repeat steps 2-3 if not at planned coordinates/distance from obstacle
6. **PR4, RA1:** pass current coordinates at end of movement sequence to Android for display
7. **PR2, RP3:** PC requests image from RPi, RPi returns image
8. **PR3, RA2:** PC returns image recognition results to Android
9.  repeat steps 2-8 until all obstacles/images identified

## Flow of messages for task 2: fastest car (W9)
1. **AR2, RP1:** Android sends START_TASK message to PC
2. **PR1:** PC sends NAVIGATION message with commands `[OF150]` no path to RPi
3. **RS1/2, SR1:** RPi forwards commands to STM and waits for ACK, STM moves to directly in front of obstacle 1
4. **RP3:** RPi gets image, sends to PC
5. **PR1:** PC sends NAVIGATION message with commands `[firstLeft/firstRight, OF150, SB010]` no path to RPi
6. **RS1/2, SR1:** RPi forwards commands to STM and waits for ACK, STM moves around obstacle 1, then forward, to just in front of the image on obstacle 2
7. **RP3:** RPi gets image, sends to PC
8. **PR1:** PC sends NAVIGATION message with commands `[secondLeft/secondRight]` no path to RPi
   - RPi records `second_arrow`, required for returning to carpark later
9. **RS1/2, SR1:** RPi forwards commands to STM and waits for ACK, STM moves around obstacle 2, ending up on side of obstacle 2 in opposite direction than `second_arrow` 
10. **RS3/4**: RPi gets `XDIST` and `YDIST` from STM, required for returning to carpark 
11. **RS1/2, SR1:** RPi calls `return_to_carpark(xdist, ydist)`, sending STM commands to return home


# Message types
- `COORDINATES`: RA1 and PR4
- `IMAGE_RESULTS`: RA2 and PR3 
- `IMAGE_TAKEN`: RP3
- `ULTRASONIC`: RP2 (see also SR2)
- `NAVIGATION`: AR1 and PR1 (see also RS1+SR1, PR1)
- `PATH`: RA3 (see also PR1)
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
3. path taken by robot in arena
   ```
    {
        "type": "PATH",
        "data": {
           "path": [[0,1], [1,1], [2,1], [3,1]]
        }
    }
    ```
    - `path` is the list of cells (each a 10x10cm block) traversed by the robot
    - this message is sent from RPi to Android before beginning the movement sequence towards an obstacle as specified in the `NAVIGATION` message from PC (see PR1)

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
2. movement until ultrasonic sensor output indicates imminent obstacle
    ```OF100```
    - O: the first character indicates to end the movement based on the ultrasonic sensor
    - F: the second character indicates Forward (this is the only valid direction since our ultrasonic sensor is front mounted)
    - XXX: the last 3 digits indicate distance in cm which is the upper limit of how far to move if the ultrasonic sensor is not triggered
    - e.g. OF100 is to move foward 100cm, or until the ultrasonic sensor indicates that an obstacle is ahead
3. get displacement in horizontal direction (perpendicular to initial facing of car) - task 2
   ```XDIST```
    - STM should return the horizontal distance in cm moved across the back of obstacle 2
4. get displacement in vertical direction (parallel to initial facing of car) - task 2
   ```YDIST```
    - STM should return the vertical distance in cm moved between obstacle 1 and 2

## PR: PC to RPi
1. movement instructions for STM
    ```
    {
        "type": "NAVIGATION",
        "data": {
           "commands": ["SF010", "RF090", "SB050", "LB090"],
           "path": [[0,1], [1,1], [2,1], [3,1]]
        }
    }
    ```
    - `commands` is a list of directions (WASD) followed by distance 
      - each command is a 5 character code: <L/R/S><F/B>XXX 
      - S/L/R: the first character indicates Straight / Left / Right 
      - F/B: the second character indicates Forward / Backward
      - XXX: the last 3 digits indicate distance in cm for S, or rotation angle for L/R
      - e.g. SB010 is move backwards 10cm, LF090 is turn 90 degrees to the left in the forward direction
      - note: for task 2, commands may also include specially defined commands in `STM_OBS_ROUTING_MAP` found in `rpi/mdp-rpi/rpi_config.py`
    - `path` is the list of cells (each a 10x10cm block) to be traversed by the robot
      - RPi reformats this into a `PATH` message to be forwarded to Android (see RA3)
    - AR1 and PR1 are consistent

2. image recognition results
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
3. current coordinates of robot
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

