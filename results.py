#!/usr/bin/python

'''
    Finds recorded experiments, filtered by robot name.
    Check and open data.log for each available experiment.
    Plots columns of interest
    + absolute velocity forwards, backwards, fast and efficiently
    + for each joint, plots phi_dot vs. phi
    + phi, phi_dot and u per joint vs. time
'''

import re, argparse, shlex
from subprocess import Popen
from os import listdir, mkdir
from os.path import isfile, isdir

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tableau20 import tableau20

from common import *




def plot_joints(jp,jv,ju, save = False):
    #plt.figure(figsize=(3, 2)) # create figure with aspect ratio
    num_j = len(jp)

    rows = int(np.ceil(np.sqrt(num_j)))
    cols = int(np.ceil(num_j/rows))
    print("rows:{0}, cols:{1}".format(rows,cols))
    fig = plt.figure()
    #TODO share axis

    for i in range(num_j):
        ax = fig.add_subplot(rows, cols, i+1)
        ax.plot(jv[i], color=tableau20[0], lw = 1.0, alpha= 0.5, marker='.')
        ax.plot(ju[i], color=tableau20[1], lw = 1.0, alpha= 0.5, marker='.')
        ax.plot(jp[i], color=tableau20[2], lw = 1.0, alpha= 0.5, marker='.')

    if save:
        plt.savefig("{0}{1}".format(experiment, pdfname), bbox_inches="tight")


def plot_phase_space(jp,jv,ju, save = False):
    #plt.figure(figsize=(3, 2)) # create figure with aspect ratio
    num_j = len(jp)

    rows = 1
    cols = num_j//2
    fig = plt.figure()

    for i in range(0,num_j,2):
        ax = fig.add_subplot(rows, cols, i//2+1)
        ax.plot(jp[i+1], jv[i+1], color=tableau20[2], lw = 1.0, alpha= 0.5)#, marker='.')
        ax.plot(jp[i  ], jv[i  ], color=tableau20[0], lw = 1.0, alpha= 0.5)#, marker='.')

    if save:
        plt.savefig("{0}{1}".format(experiment, pdfname), bbox_inches="tight")


def read_data_log(filename, columns):
    print("reading: {0}".format(filename))
    return pd.read_csv(filename, sep=' ', header=None, names=columns)


def get_time(data, tmin = None, tmax = None):
    timesteps = np.array(data["cycles"])
    ii = np.where(timesteps == 0)[0]
    ts = max(tmin, ii[0]) if tmin else ii[0] # start
    te = min(tmax, ii[1]) if tmax else ii[1] # end
    return ts, te

def read_and_plot_single_experiment(expname):
    print("Plotting: {0}".format(expname))
    rid = get_robot_id(expname)
    columns = create_columns(rid)
    data = read_data_log(expname+"/data/"+constants.data_log, columns)
    data.ename = expname

    ts, te = get_time(data, 200,400)
    print("plotting from timestep {0} to {1}".format(ts,te))

    # prepare data
    jp = []
    jv = []
    ju = []
    for j in range(constants.num_joints[rid]):
        jp.append(data["p"+str(j) ].values[ts:te])
        jv.append(data["v"+str(j) ].values[ts:te])
        ju.append(data["u"+str(j) ].values[ts:te])

    avg_pos_y  = data["avg_pos_y" ].values[ts:te]
    avg_vel_fw = data["avg_vel_fw"].values[ts:te]

    #plot_joints(jp,jv,ju)
    plot_phase_space(jp,jv,ju)
    #plot_walked_distance(avg_pos_y,avg_vel_fw)
    return data


def plot_all_experiment(data_all):
    print("Plotting graphs for all {0} experiments.".format(len(data_all)))
    
    names = []
    fig, (ax1,ax2) = plt.subplots(2, 1, sharex=True)
    for i, data in enumerate(data_all):
        ts, te = get_time(data)

        avg_pos_y  = np.abs(data["avg_pos_y" ].values[ts:te])
        ax1.plot(avg_pos_y , color=tableau20[i], lw = 1.0, alpha= 0.5, marker='.')
        
        avg_vel_fw = np.abs(data["avg_vel_y"].values[ts:te])
        ax2.plot(avg_vel_fw, color=tableau20[i], lw = 1.0, alpha= 0.5, marker='.')
        names.append(data.ename)

    plt.legend(names, loc="lower right")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter' , default='')
    parser.add_argument('-p', '--path'   , default=constants.exp_dir)
    args = parser.parse_args()

    experiments = get_all_experiments(args.path, args.filter, recorded_only=True)

    print("Processing experiments:")
    data_all = []
    for e in experiments:
        data_all.append(read_and_plot_single_experiment(e))
        #exit() #remove
    if len(data_all) > 0:
        plot_all_experiment(data_all)
        plt.show()

    print("____\nDONE.")

if __name__ == "__main__": main()

