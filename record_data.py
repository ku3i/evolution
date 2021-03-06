#!/usr/bin/python
""" record data
    -------------
    playback all or identify the best run of an experiment.
    record the sensorimotor and simulation data.
    plot figures with:
        + world positions
        + joint sensorimotor data
        + performance measures
"""

import matplotlib.pyplot as plt
import pandas as pd
import argparse
import numpy
from os import listdir, makedirs
from os.path import isfile, isdir, exists
from tableau20 import tableau20
import subprocess
from common import *



data_path   = "../data/exp/"
output_folder  = "data"
settings_folder = "./settings/"
settings_file_ending = ".setting"
default_port = 8000
nice = 19
binary = "./bin/Release/evolution"       # TODO: use robot_watch for this, check if better suited?
ansi_escape = re.compile(r'\x1b[^m]*m')

from os import listdir
def prepare_figure():
    # create figure with aspect ratio
    plt.figure(figsize=(12, 9))
    # transparent the plot frame
    ax = plt.subplot(111)
    ax.spines["top"   ].set_alpha(0.25)
    ax.spines["bottom"].set_alpha(0.25)
    ax.spines["right" ].set_alpha(0.25)
    ax.spines["left"  ].set_alpha(0.25)
    # add tick on the left and bottom
    ax.get_yaxis().tick_left()
    ax.get_xaxis().tick_bottom()


def conduct(robot, expname, port, dry = False, log_data = False, log_video = False):
    target_dir = "{0}{1}/{2}".format(data_path, expname, output_folder)

    if (log_data or log_video):
        create_folder(target_dir)
        add_args = "--enable_logging"
        add_args += " --outfile {0}/data.log".format(target_dir) if log_data else ""
        add_args += " --include_video --no_pause --outfile {0}/video.log".format(target_dir) if log_video else " --blind"

    command = "nice -n {3} {0} --watch {1} --port {2} {4}"\
        .format(binary, expname, port, nice, add_args)

    if not dry:
        output_path = "{0}{1}/".format(data_path, expname)
        exitcode, out, err = execute_command(command)
        with open(output_path + "stdout.txt", "w") as out_file:
            out_file.write(ansi_escape.sub('', out))
        with open(output_path + "stderr.txt", "w") as err_file:
            err_file.write(ansi_escape.sub('', err))
        print "OK." if exitcode==0 else "FAILED. Code {0}".format(exitcode)
    else:
        print("\n" + command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--robot')
    parser.add_argument('-d', '--dry'      , action="store_true", default=False)
    parser.add_argument('-l', '--log_data' , action="store_true", default=False)
    parser.add_argument('-v', '--log_video', action="store_true", default=False)
    args = parser.parse_args()

    if args.robot==None:
        print("Error: no robot defined.")
        return

    if not args.log_data and not args.log_video:
        print("Neither data nor video log flag is set.")
        return

    assert isfile(binary)

    robot = str(args.robot)
    target = lambda: None
    target.path = data_path + robot
    target.robot = robot

    if not isdir(target.path):
        print("Error: no such folder: {0}".format(target.path))
        return

    target.experiments = get_experiments(target)
    target.group = group_experiments(target)
    port = default_port

    try:
        for r in target.group:
            index_list = target.group[r]
            print("{0} = {1}".format(r, index_list))

            best,_,_ = get_best_worst_median(r, index_list)
            best_exp_name = r.format(best).replace(data_path,"").rstrip("/")

            print(best_exp_name)

            conduct(robot, best_exp_name, port, dry=args.dry, log_data=args.log_data, log_video=args.log_video)

            if args.log_video:
                directory = "data/"+robot
                create_folder(directory)
                subprocess.call(['./ppm2avi.sh {0}'.format(best_exp_name)], shell=True)

            port+=1
    except (KeyboardInterrupt, SystemExit):
        print("\naborted\n")


    print("\n____\nDONE.\n")
    return


if __name__ == "__main__": main()
