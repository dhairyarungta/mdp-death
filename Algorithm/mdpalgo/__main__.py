import logging
import argparse
import constants

from interface.simulator import Simulator

# Logging
logging.basicConfig(level=logging.INFO)

# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--hl", help="run in headless mode", action="store_true")
parser.add_argument("--cen", help="center pathing on obstacle",
                    action="store_true")
parser.add_argument("--testwifi", help="use test wifi server on PC instead "
                                       "of real rpi",
                    action="store_true")


def main():
    constants.HEADLESS = False
    args = parser.parse_args()
    if args.hl:
        constants.HEADLESS = True
        print("Running in headless mode")
    if args.testwifi:
        constants.WIFI_IP = constants.TEST_IP
        print("Use local IP address for integration testing without RPi")

    x = Simulator()
    x.run()


if __name__ == '__main__':
    main()
