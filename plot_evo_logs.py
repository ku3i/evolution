#!/usr/bin/python
""" plot_evo_logs
    -------------
    this script opens the evolution.log files per selected robot
    and plots the fitness values of the best/median/worst and -- on demand --
    creates an evoplot for each experiment in pdf format and
    puts it into the experiment's folder.
"""

import matplotlib.pyplot as plt
import pandas as pd
import argparse
import numpy

from os.path import isfile, isdir
from tableau20 import tableau20

from common import *

columns = ['fmax', 'favg', 'fmin']#, 'rmax', 'ravg', 'rmin'] TODO

data_path   = "../data/exp/"
logfile     = "evolution.log"
pdfname     = "evolog.pdf"
datafolder  = "data"

def prepare_figure():
    # create figure with aspect ratio
    plt.figure(figsize=(6, 3))
    # transparent the plot frame
    ax = plt.subplot(111)
    ax.spines["top"   ].set_alpha(0.25)
    ax.spines["bottom"].set_alpha(0.25)
    ax.spines["right" ].set_alpha(0.25)
    ax.spines["left"  ].set_alpha(0.25)
    # add tick on the left and bottom
    ax.get_yaxis().tick_left()
    ax.get_xaxis().tick_bottom()


def read_csv(filename):
    return pd.read_csv(filename, sep=' ', header=None, names=columns)


def create_evolog(target, experiment):
    print("creating {0}".format(experiment))
    try:
        evolution = read_csv(experiment+logfile)
        for i,e in enumerate(evolution):
            plt.plot( evolution[e].values
                    , color=tableau20[i]
                    , lw=0.5 )
        #plt.show()
        plt.legend(columns, loc="lower right")

        target_dir = "{0}/{1}".format(experiment,datafolder)
        create_folder(target_dir)
        plt.savefig("{0}/{1}".format(target_dir, pdfname)
                    , bbox_inches="tight")
        plt.clf()
    except:
        print("skipping " + experiment)
        return


def create_all_evologs(target):
    print("Creating all evologs.")
    prepare_figure()
    for exp in target.experiments:
        create_evolog(target, exp)


def create_summary_evologs(target, name, index_list):
	print("\t{0}={1}".format(name, index_list))

	best,median,worst = get_best_worst_median(name, index_list)

	# draw plots
	trials = get_max_trials(name.format(0))
	evodict = {}

	assert isfile(name.format(best  )+logfile)

	evodict['best'  ] = read_csv(name.format(best  )+logfile)['favg']
	evodict['median'] = read_csv(name.format(median)+logfile)['favg']
	evodict['worst' ] = read_csv(name.format(worst )+logfile)['favg']

	plt.plot(evodict['worst' ], color=tableau20[1], lw=0.5 )
	plt.plot(evodict['best'  ], color=tableau20[0], lw=0.5 )
	plt.plot(evodict['median'], color=tableau20[2], lw=0.5 )
	if target.limit is not None:
		plt.ylim(0, target.limit)
	plt.legend(['min','max','med'], loc="lower right")
	#plt.show()
	plt.savefig("{0}_{1}".format(name.format("").rstrip("/").lstrip("_"), pdfname), bbox_inches="tight")
	plt.clf()


def create_summary(target):
    print("Creating summary.")
    prepare_figure()
    group = group_experiments(target)
    for g in group.keys():
	print("_"*20)
        create_summary_evologs(target, g, group[g])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--robot')
    parser.add_argument('-a', '--evologs', action="store_true", default=False)
    parser.add_argument('-y', '--yscale_limit', default=None, type=float)
    args = parser.parse_args()

    if args.robot==None:
        print("Error: no robot defined.")
        return

    robot = str(args.robot)
    target = lambda: None
    target.path = data_path + robot
    target.robot = robot
    target.limit = args.yscale_limit

    if not isdir(target.path):
        print("Error: no such folder: {0}".format(target.path))
        return

    target.experiments = get_experiments(target)
    print(target.experiments)
    if args.evologs:
        create_all_evologs(target)
    else:
        create_summary(target)
    print("\n____\nDONE.\n")
    return


if __name__ == "__main__": main()
