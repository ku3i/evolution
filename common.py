""" commonly used functions for 
    evaluating recorded experiments
"""
import re, shlex
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join

import pandas as pd

config = "evolution.conf"
fitness_log = "fitness.log"

def get_experiments(target):
    return ["{0}/{1}/".format(target.path, d) for d in sorted(listdir(target.path)) if isdir(join(target.path, d))]


# returns dictionary
def group_experiments(target):
    d = {}
    for exp in target.experiments:
        key = re.sub(r"/\d+_", "/{0}_", exp)
        m = re.search('/(\d+)_', exp)
        if m is None:
            continue
        if key in d:
            d[key].append(int(m.groups()[0]))
        else:
            d[key] = [int(m.groups()[0])]
    return d


def get_max_trials(folder):
	setting = folder+config
	with open(setting, 'r') as f:
		for line in f.readlines():
			m = re.search("^MAX_TRIALS = (\d+)$", line)
			if m:
				return int(m.groups()[0])
	print("WARNING: No max trials defined in file: {}".format(setting))
	return 0


def get_best_worst_median(name, index_list):
    # get max, med, min
    fitlist = []
    for i in index_list:
        print("reading "+name.format(i)),
        filename = name.format(i) + fitness_log
        fitness = pd.read_csv(filename, sep=' ', header=None)
        sumfit = sum(fitness[0])
        fitlist.append((sumfit,i))
        print(" fitness: {0}".format(sumfit))

    fitlist.sort(key=lambda tup: tup[0], reverse=True)

    best   = fitlist[0][1]
    median = fitlist[len(fitlist)/2-1][1]
    worst  = fitlist[-1][1]

    return (best, median, worst)


def execute_command(command):
    args = shlex.split(command)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err
