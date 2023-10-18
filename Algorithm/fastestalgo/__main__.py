import os
import sys

cwd = os.getcwd()
pardir = os.path.dirname(cwd)
mdp_algo_dir = os.path.join(pardir, 'mdpalgo')
sys.path.insert(1, mdp_algo_dir)

from week9task import Week9Task
from mdpalgo import constants

import argparse
# parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--testwifi", help="use test wifi server on PC instead of real rpi",
                action="store_true")
args = parser.parse_args()

if args.testwifi:
    constants.WIFI_IP = constants.TEST_IP
    print("Use local IP address for integration testing without RPi")

if __name__ == "__main__":
    x = Week9Task()
    x.run()
