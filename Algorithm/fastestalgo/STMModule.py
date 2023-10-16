from multiprocessing import Process, Queue
from Action import *
import os
from RobotMovementError import *
import time


import serial


class STMModule:
    def __init__(self):
        # global ser
        self.port = '/dev/ttyS0'
        self.baud = 115200
        # ser = serial.Serial('/dev/ttyUSB1', 115200, timeout=3)  # Check that arduino has same baudrate of 115200
        # ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=3)  # Check that arduino has same baudrate of 115200
        self.isEstablished = False
        self.serialConn = None
        #self.serialConn.flush()
        pass

    def isConnected(self):
        return self.isEstablished

    def connect(self):
        while True:
            retry = False
            try:
                # Let's wait for connection
                print('[STM_INFO] Waiting for serial connection from STM')

                self.serialConn = serial.Serial('/dev/ttyUSB0', self.baud, timeout=0.1)
                print('[STM_ACCEPTED] Connected to STM.')
                self.isEstablished = True
                retry = False

            except Exception as e:
                print('[STM_ERROR] STM Connection Error: %s' % str(e))
                retry = True

            # When established, break the while(true)
            if not retry:
                break

            # When not yet established, keep retrying
            print('[STM_INFO] Retrying STM Establishment')
            time.sleep(1)

    def send_function_and_args_to_stm(self, string: str):
        received = False
        timeout = 5
        while not received:
            time_start = time.time()
            self.serialConn.write(str.encode(string))
            while True:
                time_passed = time.time() - time_start
                if time_passed > timeout:
                    break
                else:
                    x = self.read()
                if x == "ACK":
                    received = True
                    print(x)
                    self.serialConn.write(str.encode('X'))
                    return

    def send_movement_to_stm(self, string):
        received = False
        timeout = 5
        while not received:
            time_start = time.time()
            self.serialConn.write(str.encode(string))
            while True:
                time_passed = time.time() - time_start
                if time_passed > timeout:
                    break
                else:
                    x = self.read()
                if x == "ACK":
                    received = True
                    print(x)
                    self.serialConn.write(str.encode('X'))
                    return

    def forward_until_obs(self):
        # STM COMMAND BLOCK #
        self.serialConn.write(str.encode("o"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return



        # STM COMMAND BLOCK #


    def quick_swerve_left(self):
        # STM COMMAND BLOCK #
        self.serialConn.write(str.encode("z"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


        # STM COMMAND BLOCK #

        return forward

    def quick_swerve_right(self):
        # STM COMMAND BLOCK #
        self.serialConn.write(str.encode("x"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


        # STM COMMAND BLOCK #

    def long_swerve_left_and_return(self):
        # STM COMMAND BLOCK #
        self.serialConn.write(str.encode("c"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return

        # STM COMMAND BLOCK #

        return forward

    def long_swerve_right_and_return(self):
        # STM COMMAND BLOCK #
        self.serialConn.write(str.encode("v"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


        # STM COMMAND BLOCK #

    def backupLeft(self):
        self.serialConn.write(str.encode("l"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return

    def backupRight(self):
        self.serialConn.write(str.encode("r"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return            


    def forward(self):
        self.serialConn.write(str.encode("w"))
        while True:
            x = self.read()
            if x is not None:
                print(x)
                print(len(x))
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    def backward(self):
        self.serialConn.write(str.encode("s"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    def forwardLeft(self):
        self.serialConn.write(str.encode("a"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    def forwardRight(self):
        self.serialConn.write(str.encode("d"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    def backwardLeft(self):
        self.serialConn.write(str.encode("n"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    def backwardRight(self):
        self.serialConn.write(str.encode("m"))
        while True:
            x = self.read()
            if x == "ACK":
                print(x)
                self.serialConn.write(str.encode('X'))
                return


    # returns new robot position x and y and direction r
    def process_move(self, move: RobotAction, robot_position_x, robot_position_y, robot_direction):
        moved = False
        new_x = robot_position_x
        new_y = robot_position_y
        new_direction = robot_direction
        try:
            if move == RobotAction.FORWARD:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving forward!")
                self.forward()
                new_y = new_y + (1 - robot_direction) * (int(not (robot_direction % 2)))
                new_x = new_x + (2 - robot_direction) * (int((robot_direction % 2)))
            elif move == RobotAction.BACKWARD:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving backward!")
                self.backward()

                new_y = new_y - (1 - robot_direction) * (int(not (robot_direction % 2)))
                new_x = new_x - (2 - robot_direction) * (int((robot_direction % 2)))
            elif move == RobotAction.TURN_FORWARD_LEFT:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving forward left!")
                self.forwardLeft()
                if robot_direction == 0 or robot_direction == 1:
                    new_y = new_y + 3
                else:
                    new_y = new_y - 3

                if robot_direction == 1 or robot_direction == 2:
                    new_x = new_x + 3
                else:
                    new_x = new_x - 3
                new_direction = (new_direction - 1) % 4
            elif move == RobotAction.TURN_FORWARD_RIGHT:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving forward right!")
                self.forwardRight()
                if robot_direction == 0 or robot_direction == 3:
                    new_y = new_y + 3
                else:
                    new_y = new_y - 3

                if robot_direction == 0 or robot_direction == 1:
                    new_x = new_x + 3
                else:
                    new_x = new_x - 3
                new_direction = (new_direction + 1) % 4
            elif move == RobotAction.TURN_BACKWARD_LEFT:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving backward left!")
                self.backwardLeft()
                if robot_direction == 1 or robot_direction == 2:
                    new_y = new_y + 3
                else:
                    new_y = new_y - 3

                if robot_direction == 2 or robot_direction == 3:
                    new_x = new_x + 3
                else:
                    new_x = new_x - 3
                new_direction = (new_direction + 1) % 4
            elif move == RobotAction.TURN_BACKWARD_RIGHT:
                if self.check_for_obstacle():
                    raise RobotMovementError
                moved = True
                print("moving backward right!")
                self.backwardRight()
                if robot_direction == 1 or robot_direction == 2:
                    new_y = new_y + 3
                else:
                    new_y = new_y - 3

                if robot_direction == 0 or robot_direction == 3:
                    new_x = new_x + 3
                else:
                    new_x = new_x - 3
                new_direction = (new_direction - 1) % 4
        except RobotMovementError:
            print("obstacle detected!")
        finally:
            return new_x, new_y, new_direction, moved

    def check_for_obstacle(self):
        return False

    def disconnect(self):
        if not (self.serialConn is None):  # if (self.serialConn):
            print('[STM_CLOSE] Shutting down STM Connection')
            self.serialConn.close()
            self.isEstablished = False

    def read(self):
        try:
            readData = self.serialConn.readline()
            self.serialConn.flush()  # Clean the pipe
            readData = readData.decode('utf-8')
            if readData == '':
                return None
            #print('[STM_INFO] Received: ' + readData)
            return readData

        except Exception as e:
            print('[STM_ERROR] Receiving Error: %s' % str(e))
            if ('Input/output error' in str(e)):
                self.disconnect()
                print('[STM_INFO] Re-establishing Arduino Connection.')
                self.connect()

    # The fundamental trying to send
    def write(self, message):
        try:
            # Make sure there is a connection first before sending
            if self.isEstablished:
                print("STM", message)
                message = message.encode('utf-8')
                self.serialConn.write(message)
                return

            # There is no connections. Send what?
            else:
                print('[STM_INVALID] No STM Connections')

        except Exception as e:
            print('[STM_ERROR] Cannot send message: %s' % str(e))
