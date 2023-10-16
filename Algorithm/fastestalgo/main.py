from multiprocessing import Process, Lock, Queue
from Action import *
import socket
import time

from WifiModule import *
from STMModule import STMModule
from AndroidLinkModule import *
from CameraModule import *


# from DummyAndroidLinkModule import *
# from DummyWifiModule import *
# from DummySTMModule import *
# from DummyCameraModule import DummyCameraModule as CameraModule


class Main:
    def __init__(self):
        # Initialise Variables
        self.stopped = False
        override_action = None
        map_array = None
        self.stm = STMModule()
        self.stm.connect()
        self.override_queue = Queue()
        self.wifi_stopped_queue = Queue()
        self.android_stopped_queue = Queue()
        self.wifi_command_queue = Queue()
        self.android_command_queue = Queue()
        self.action_list = Queue()
        obstacle_with_direction_list = list()
        movement_string_conv_dict = {"F": RobotAction.FORWARD,
                                     "B": RobotAction.BACKWARD,
                                     "FL": RobotAction.TURN_FORWARD_LEFT,
                                     "FR": RobotAction.TURN_FORWARD_RIGHT,
                                     "BR": RobotAction.TURN_BACKWARD_RIGHT,
                                     "BL": RobotAction.TURN_BACKWARD_LEFT
                                     }

        image = None
        robot_position_x = 0
        robot_position_y = 0
        robot_direction = 0
        obstacle_position_x = -1
        obstacle_position_y = -1
        movement_counter = 0

        # Initialise Wifi thread
        print("starting wifi module")
        wifi_thread = WifiModule(self.wifi_stopped_queue, self.wifi_command_queue, self.action_list,
                                 self.override_queue)
        wifi_thread.start()

        # Initialise android bluetooth thread
        print("starting bluetooth module")
        android_thread = AndroidLinkModule(self.android_stopped_queue, self.android_command_queue, self.action_list,
                                           self.override_queue)
        android_thread.start()
        self.android_command_queue.put(Command(AndroidBluetoothAction.ROBOT_READY, ""))
        # Main thread loop (try catch block is to intercept ctrl-c stop command so that it closes gracefully)
        try:
            while not self.stopped:
                # Check if there are any override commands for the threads
                if not self.override_queue.empty():
                    override_action = self.override_queue.get()
                    if override_action.command_type == OverrideAction.STOP:
                        print("stop command received")
                        while not self.action_list.empty():
                            self.action_list.get()
                    elif override_action.command_type == OverrideAction.QUIT:
                        self.wifi_stopped_queue.put(True)
                        self.android_stopped_queue.put(True)
                        stopped = True
                        break
                # Check and run one move per loop
                if not self.action_list.empty():
                    command = self.action_list.get()
                    print("action received")
                    print(command.command_type)
                    print(command.data)
                    # if action is a movement action
                    if command.command_type.value <= RobotAction.TURN_BACKWARD_RIGHT.value:
                        x, y, r, moved = self.stm.process_move(command.command_type, robot_position_x, robot_position_y,
                                                               robot_direction)
                        robot_position_x = x
                        robot_position_y = y
                        robot_direction = r
                        if moved:
                            movement_counter += 1

                        temp_list = [robot_position_x, robot_position_y, robot_direction]
                        self.android_command_queue.put(Command(AndroidBluetoothAction.UPDATE_DONE,
                                                               [1, obstacle_position_x, obstacle_position_y]))
                        self.wifi_command_queue.put(Command(WifiAction.UPDATE_DONE,
                                                            [1, obstacle_position_x, obstacle_position_y]))

                    elif command.command_type == RobotAction.SET_ROBOT_POSITION_DIRECTION:
                        temp_tuple = command.data
                        robot_position_x = temp_tuple[0]
                        robot_position_y = temp_tuple[1]
                        robot_direction = temp_tuple[2]
                    elif command.command_type == RobotAction.SET_OBSTACLE_POSITION:
                        obstacle_position_x = command.data[0]
                        obstacle_position_y = command.data[1]
                    elif command.command_type == RobotAction.SET_MOVEMENTS:
                        for move in command.data:
                            print(movement_string_conv_dict[move])
                            self.action_list.put(Command(movement_string_conv_dict[move], ""))
                    elif command.command_type == RobotAction.SEND_TARGET_ID:
                        self.android_command_queue.put(
                            Command(AndroidBluetoothAction.SEND_IMAGE_WITH_RESULT, command.data))
                    elif command.command_type == RobotAction.START_EXPLORE:
                        movement_counter = 0
                        self.wifi_command_queue.put(Command(WifiAction.START_MISSION, command.data))
                    elif command.command_type == RobotAction.START_PATH:
                        movement_counter = 0
                        self.run_pathing()
                        print("finish path")
                    elif command.command_type == RobotAction.SEND_MISSION_PLAN:
                        self.android_command_queue.put(Command(AndroidBluetoothAction.SEND_MISSION_PLAN, command.data))
                    elif command.command_type == RobotAction.WIFI_CONNECTED:
                        self.android_command_queue.put(Command(AndroidBluetoothAction.WIFI_CONNECTED, ""))
                    elif command.command_type == RobotAction.SEND_FINISH:
                        self.android_command_queue.put(Command(AndroidBluetoothAction.SEND_FINISH, command.data))
                    else:
                        pass
        except KeyboardInterrupt:
            self.wifi_stopped_queue.put(Command(OverrideAction.STOP, 0))
            self.android_stopped_queue.put(Command(OverrideAction.STOP, 0))
            wifi_close_module()
            android_close_module()
        except Exception as e:
            print(e)

        print("waiting for android to stop")
        android_thread.join()
        print("android thread stopped")
        wifi_thread.join()
        print("wifi thread stopped")
        if self.stm.isConnected():
            self.stm.disconnect()
        print("program shutting down")

    # TODO
    def run_pathing(self):
        UNITS_MULTIPLIER = 1
        path_robot_position_x = 0
        path_robot_position_y = 0
        path_robot_direction = 0
        x = 0
        y = 0
        r = 0
        moved = False
        forward = 0
        # STEP 1: move robot forward until detect obstacle and detect time taken
        print("1")
        self.stm.forward_until_obs()
        # STEP 2: Detect picture
        print("2")
        picture = self.get_picture()

        # STEP 3: Turn left or right around obstacle depending on picture
        print("3")
        if picture == "Left":
            self.quick_swerve_left()
        elif picture == "Right":
            self.quick_swerve_right()
        else:
            x, y, r, moved = self.stm.process_move(RobotAction.BACKWARD, path_robot_position_x,
                                                   path_robot_position_y,
                                                   path_robot_direction)
            path_robot_position_x = x
            path_robot_position_y = y
            path_robot_direction = r
            picture = self.get_picture()
            if picture == "Left":
                x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                       path_robot_position_y,
                                                       path_robot_direction)
                path_robot_position_x = x
                path_robot_position_y = y
                path_robot_direction = r
                self.quick_swerve_left()
            elif picture == "Right":
                x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                       path_robot_position_y,
                                                       path_robot_direction)
                path_robot_position_x = x
                path_robot_position_y = y
                path_robot_direction = r
                self.quick_swerve_right()
            else:
                print("Error! could not get picture!")
                self.android_command_queue.put(Command(AndroidBluetoothAction.SEND_FINISH, b"FINISH/PATH/"))
                return
        # STEP 4: move robot forward until detect obstacle
        print("4")
        self.stm.forward_until_obs()
        if picture == "Left":
            self.stm.backupLeft()
        elif picture == "Right":
            self.stm.backupRight()
        # STEP 5: Detect picture
        print("5")
        picture = self.get_picture()
        print("6")

        # STEP 6: turn left or right around obstacle depending on picture and return back to base
        if picture == "Left":
            self.long_swerve_left_and_return()
        elif picture == "Right":
            self.long_swerve_right_and_return()

        else:
            num_back = 0
            max_numback = 3
            while picture not in ["Left", "Right"] and num_back <= max_numback:
                x, y, r, moved = self.stm.process_move(RobotAction.BACKWARD, path_robot_position_x,
                                                       path_robot_position_y,
                                                       path_robot_direction)
                picture = self.get_picture()

                num_back += 1

            x, y, r, moved = self.stm.process_move(RobotAction.BACKWARD, path_robot_position_x,
                                                   path_robot_position_y,
                                                   path_robot_direction)

            self.stm.forward_until_obs()

            if picture not in ["Left", "Right"]:
                picture = self.get_picture()

            if picture == "Left":
                self.long_swerve_left_and_return()
            elif picture == "Right":
                self.long_swerve_right_and_return()

            # else:
            #     print("Error! could not get picture!")
            #     self.android_command_queue.put(Command(AndroidBluetoothAction.SEND_FINISH, b"FINISH/PATH/"))
            #     return
        print("7")
        # Send back finish
        self.android_command_queue.put(Command(AndroidBluetoothAction.SEND_FINISH, b"FINISH/PATH/"))
    # returns distance that the robot travelled forward
    def quick_swerve_left(self):
        """
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        """
        self.stm.quick_swerve_left()

    # returns distance that the robot travelled forward
    def quick_swerve_right(self):
        """
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)

        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r

        """
        self.stm.quick_swerve_right()

    # returns distance that the robot travelled forward
    def long_swerve_left_and_return(self):
        """
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        for x in range(0, 5):
            x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                   path_robot_position_y,
                                                   path_robot_direction)
            path_robot_position_x = x
            path_robot_position_y = y
            path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        for x in range(0, 10):
            x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                   path_robot_position_y,
                                                   path_robot_direction)
            path_robot_position_x = x
            path_robot_position_y = y
            path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                               path_robot_position_y,
                                               path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        """
        self.stm.long_swerve_left_and_return()

    # returns distance that the robot travelled forward
    def long_swerve_right_and_return(self):
        """
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_RIGHT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        for x in range(0, 5):
            x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                  path_robot_position_y,
                                                  path_robot_direction)
            path_robot_position_x = x
            path_robot_position_y = y
            path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        for x in range(0, 10):
                x, y, r, moved = self.stm.process_move(RobotAction.FORWARD, path_robot_position_x,
                                                  path_robot_position_y,
                                                  path_robot_direction)
            path_robot_position_x = x
            path_robot_position_y = y
            path_robot_direction = r
        x, y, r, moved = self.stm.process_move(RobotAction.TURN_FORWARD_LEFT, path_robot_position_x,
                                              path_robot_position_y,
                                              path_robot_direction)
        path_robot_position_x = x
        path_robot_position_y = y
        path_robot_direction = r
        """

        self.stm.long_swerve_right_and_return()

    def get_picture(self):
        self.wifi_command_queue.put(Command(WifiAction.SEND_PICTURE, ""))
        while True:
            if not self.override_queue.empty():
                override_action = self.override_queue.get()
                if override_action.command_type == OverrideAction.STOP:
                    print("stop command received")
                    return
                elif override_action.command_type == OverrideAction.QUIT:
                    # wifi_stopped_queue.put(True)
                    # android_stopped_queue.put(True)
                    return
            # Check and run one move per loop
            if not self.action_list.empty():
                command = self.action_list.get()
                print("action received")
                print(command.command_type)
                print(command.data)
                # wait for receive picture
                if command.command_type == RobotAction.SEND_TARGET_ID:
                    raw_string = command.data.decode("utf-8")
                    command = raw_string.split("/")
                    result = command[1]
                    return result
                else:
                    pass


if __name__ == '__main__':
    main = Main()
