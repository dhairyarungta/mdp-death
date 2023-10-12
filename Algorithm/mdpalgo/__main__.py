import logging
import argparse

from constants import mdp_constants
from interface.simulator import Simulator
from image_stiching import stiching_images
import os 

# Logging
logging.basicConfig(level=logging.INFO)

# parse the arguments
def list_of_strings(args):
    return args.split(",")

parser = argparse.ArgumentParser()
parser.add_argument("--hl", help="run in headless mode", action="store_true")
parser.add_argument("--cen", help="center pathing on obstacle",
                    action="store_true")
parser.add_argument("--testwifi", help="use test wifi server on PC instead "
                                       "of real rpi",
                    action="store_true")
parser.add_argument("--il", type=list_of_strings)
parser.add_argument("-l", action="store_true")
parser.add_argument("-r", action="store_true")

def main():
    mdp_constants.HEADLESS = False
    args = parser.parse_args()
    if args.hl:

        mdp_constants.HEADLESS = True
        print("Running in headless mode")

    try:
        if args.l:
            x = Simulator(['39'])
        elif args.r:
            x = Simulator(['38'])
        elif len(args.il)>0:
            x = Simulator(args.il)
        else:
            x = Simulator()
        x.run()
    except Exception as err:
        print(err)

def remove_file_ext(directory, file_ext = '.jpg'):
    for f in os.listdir(directory):
        if f.endswith(file_ext):
            os.remove(os.path.join(directory, f))

if __name__ == '__main__':
    remove_file_ext('images', '.jpg')
    remove_file_ext('images_result', '.jpg')
    remove_file_ext('images_resized', '.jpg')
    main()
