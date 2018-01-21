""" commonly used functions for 
    evaluating recorded experiments
"""
import re, shlex
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join
from time import sleep

import pandas as pd

config = "evolution.conf"
fitness_log = "fitness.log"

conf_file = "evolution.conf"

''' TODO join methods for checking the config file '''

def is_experiment(path):
    return isdir(path) \
        and isfile(path+"/"+config)

def is_completed(path):
    conf = path+"/"+config
    with open(conf) as f:
        data = f.read()
    m = re.search("STATUS = (\d+)", data)
    if m:
        return 2 == int(m.groups()[0])
    print("ERROR: Did not find status entry in {0}".format(conf))
    return False

def get_robot_id(path):
    conf = path.rstrip('/') + "/" +config
    with open(conf) as f:
        data = f.read()
    m = re.search("ROBOT = (\d+)", data)
    if m:
        id = int(m.groups()[0])
        print("Robot ID is: {}".format(id))
        return id
    else:
        print("ERROR: Did not find robot entry in {0}".format(conf))
        return 0

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
    print(args)
    proc = Popen(args, stdout=PIPE, stderr=PIPE)
    while proc.poll() is None:
        sleep(1)
        print("."),
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err
