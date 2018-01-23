#!/usr/bin/python
""" weights analysis
    ----------------
    plot weights of different experiments
"""


import argparse, pylab
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tableau20 import tableau20

from common import *

def show_weights_of_population(experiments):
    fig = plt.figure()
    ax  = plt.gca()

    N = len(experiments)
    maxv = 0
    for idx,e in enumerate(experiments):
        Y = np.loadtxt(e+"/population.log")
        y = Y[0,:]
        maxv = max(maxv, max(abs(y)))
        x = range(len(y))
        val = float(idx)/(N-1) if N > 1 else 0.0
        color = [0.0 + val,0.5,1.0-val]
        ax.scatter(x,y,c=color, s=30, alpha=0.5)

    maxv = np.ceil(maxv)
    ax.set_ylim(ymin=-maxv,ymax=maxv)
    ax.set_xlim(xmin=-1,xmax=len(y)+1)
    plt.xlabel(r'$i$')
    plt.ylabel(r'$w_i$')
    plt.show()


def create_weight_names(number_of_joints, robot_id):
    names=[]
    joint_names = constants.joint_names[robot_id]
    for i in range(number_of_joints):
        names.append("p-"+joint_names[i])
        names.append("v-"+joint_names[i])
        names.append("u-"+joint_names[i])

    names += ["ax", "ay", "az", "b"]
    return names


def show_weights_as_matrix(experiment):
    fig = plt.figure()
    ax  = plt.gca()

    robot_id = get_robot_id(experiment)
    num_j = constants.num_joints[robot_id]
    w_names = create_weight_names(num_j,robot_id)
    num_w = num_j*(3*num_j+4)
    Y = np.loadtxt(experiment+"/population.log")
    y = Y[0,:]
    
    assert(len(y) == num_w or len(y) == num_w//2)
    if len(y) == num_w//2: # is symmetric
        jj = num_j//2
        newsize= (jj,num_w//num_j)
    else:
        jj = num_j
        newsize= (jj,num_w//jj)

    data = np.asmatrix(Y[0,:]).reshape(newsize)

    norm = plt.colors.Normalize(vmin=-5.,vmax=5.)
    im = ax.imshow(data, cmap=plt.cm.coolwarm, norm=norm, interpolation='none')

    for (i, j), z in np.ndenumerate(data):
        ax.text(j, i, '{:0.1f}'.format(z), ha='center', va='center',size=10)#, bbox=dict(boxstyle='round', facecolor='white', edgecolor='0.3'))

    ax.set_xticks(range(0, len(w_names)))
    ax.set_xticklabels(w_names, rotation='vertical')

    u_names = constants.sym_j_names[robot_id]
    ax.set_yticks(range(0, len(u_names)))
    ax.set_yticklabels(u_names)
    ax.get_xaxis().tick_top()
    ax.get_yaxis().tick_left()

    #TODO savefig?

    plt.xlabel(r'$w_i$')
    plt.ylabel(r'$u_j$')
    plt.show()


def show_weight_histogram(experiment):
    Y = np.loadtxt(experiment+"/population.log")
    data = Y[0,:]

    plt.figure(figsize=(8, 3))

    plt.rc('text', usetex=True)    # you might need: sudo apt-get install dvipng
    plt.rc('font', family='serif')

    w_max = int(np.ceil(max(data)))

    plt.xticks(range(-w_max,w_max,1),fontsize=10)
    plt.yticks(fontsize=10)

    plt.xlabel(r'$\mathrm{value}$', fontsize=16)
    plt.ylabel(r'$\mathrm{count}$', fontsize=16)

    plt.hist(data, color="#3F5D7D", bins=128, range=(-w_max,w_max))
    plt.title(r'$\mathrm{Histogram\ of\ weights}$')
    #plt.axis([40, 160, 0, 0.03])
    plt.grid(True)

    plt.savefig(experiment+"/weight_histogram.pdf", bbox_inches="tight")
    plt.show()



def show_evolution_of_weights(experiment):
    fig = plt.figure()
    ax  = plt.gca()

    Y = np.loadtxt(experiment+"/bestindiv.log")
    y = Y[:,:]
    plt.plot(y)

    plt.xlabel(r'$t$')
    plt.ylabel(r'$w_j$')
    plt.show()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter'   , default='')
    parser.add_argument('-p', '--path'     , default=constants.exp_dir)
    parser.add_argument('-m', '--matrix'   , action='store_true')
    parser.add_argument('-e', '--evolution', action='store_true')
    parser.add_argument('-b', '--histogram', action='store_true')
    args = parser.parse_args()

    experiments = get_all_experiments(args.path, args.filter, recorded_only=False)
    if not experiments:
        return

    first = experiments[0]

    if args.matrix:
        show_weights_as_matrix(first)
    elif args.evolution:
        show_evolution_of_weights(first)
    elif args.histogram:
        show_weight_histogram(first)
    else:
        show_weights_of_population(experiments)

    print("____\nDONE.")


if __name__ == "__main__": main()
