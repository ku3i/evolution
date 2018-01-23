""" commonly used functions for 
    evaluating recorded experiments
"""
import re, shlex
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join
from time import sleep

import pandas as pd

class constants:
    config_file = "evolution.conf"
    fitness_log = "fitness.log"
    data_log    = "data.log"
    exp_dir     = "../data/exp/"

    num_joints = { 20 : 2  # crawler
                 , 10 : 4  # tadpole
                 , 31 : 12 # fourlegged
                 , 50 : 22 # humanoid
                 , 51 : 23 # humanoid
                 }

    joint_names = { 20 : [ "shoulder-pitch"
                         , "elbow-pitch"
                         ]
                  , 10 : [ "L-shoulder-roll"
                         , "R-shoulder-roll"
                         , "L-shoulder-yaw"
                         , "R-shoulder-yaw"
                         ]
                  , 31 : [ "L-shoulder-roll"
                         , "R-shoulder-roll"
                         , "L-hip-roll"
                         , "R-hip-roll"
                         , "L-shoulder-pitch"
                         , "R-shoulder-pitch"
                         , "L-elbow-pitch"
                         , "R-elbow-pitch"
                         , "L-hip-pitch"
                         , "R-hip-pitch"
                         , "L-knee-pitch"
                         , "R-knee-pitch"
                         ]
    }
    sym_j_names = { 20 : [ "shoulder-pitch"
                         , "elbow-pitch"
                         ]
                  , 10 : [ "shoulder-roll"
                         , "shoulder-yaw"
                         ]
                  , 31 : [ "shoulder-roll"
                         , "hip-roll"
                         , "shoulder-pitch"
                         , "elbow-pitch"
                         , "hip-pitch"
                         , "knee-pitch"
                         ]
    }


''' TODO join methods for checking the config file 
    consider using fnmatch or regex for filtering 
'''

def create_columns(robot_id):
    numj = constants.num_joints[robot_id]
    print("Number of joints: {0}".format(numj))
    columns = [ "cycles" ]
    for n in range(numj):
        columns += ["p"+str(n), "v"+str(n), "u"+str(n)]

    columns += [ "ax","ay","az" ]
    columns += [ "avg_rot_pos"
               , "avg_rot_vel"
               , "avg_vel_fw"
               , "avg_vel_le"
               , "norm_power"
               , "avg_pos_x"
               , "avg_pos_y"
               , "avg_pos_z"
               , "avg_vel_x"
               , "avg_vel_y"
               , "avg_vel_z"
               ]
    return columns


def is_experiment(path):
    return isdir(path) \
        and isfile(path+"/"+constants.config_file)

def is_completed(path):
    conf = path+"/"+constants.config_file
    with open(conf) as f:
        data = f.read()
    m = re.search("STATUS = (\d+)", data)
    if m:
        return 2 == int(m.groups()[0])
    print("ERROR: Did not find status entry in {0}".format(conf))
    return False

def get_robot_id(path):
    conf = path.rstrip('/') + "/" +constants.config_file
    with open(conf) as f:
        data = f.read()
    m = re.search("ROBOT = (\d+)", data)
    if m:
        id = int(m.groups()[0])
        #print("Robot ID is: {}".format(id))
        return id
    else:
        print("ERROR: Did not find robot entry in {0}".format(conf))
        return 0

#def get_experiments(target):
#    return ["{0}/{1}/".format(target.path, d) for d in sorted(listdir(target.path)) if isdir(join(target.path, d))]


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
    setting = folder+constants.config_file
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
        filename = name.format(i) + constants.fitness_log
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


def is_recorded(path):
    return isfile(path+"/"+constants.data_log)


def find_experiments(path, filt, dir_level = 0, find_recorded_only = True):
    exp_list = []
    number = 0
    try:
        dirs = [d for d in listdir(path) if isdir(path+"/"+d)]
    except:
        print("Error while scanning folders.")
        return [] # empty
    dirs.sort()
    for d in dirs:
        exp_path = path+"/"+d
        if not is_experiment(exp_path):
            print(" {1}[{0}]".format(d, " " * (3*dir_level) + "+"))
            res = find_experiments(exp_path, filt, dir_level+1, find_recorded_only)
            if res:
                exp_list += res
            continue

        if filt and filt not in d:
            continue

        result = is_completed(exp_path)
        result = (result and is_recorded(exp_path)) if find_recorded_only else result
        if result:
            exp_list.append(exp_path)
            print(" {1} {0}".format(exp_path.replace(path+"/",""), " " * (3*dir_level+1)))
        number += 1
    return exp_list


def get_all_experiments(path, filt, recorded_only = False):
    experiments = []

    path = path.rstrip("/")

    if isdir(path):
        try:
            print("Searching for experiments...")
            experiments = find_experiments(path, filt, find_recorded_only=recorded_only)
        except (KeyboardInterrupt, SystemExit):
            print("Aborted by user.")

    if len(experiments) == 0:
        print("nothing completed or recorded.")

    return experiments