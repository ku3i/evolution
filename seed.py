#!/usr/bin/python

#import re, sys, shlex, argparse
#from subprocess import Popen, PIPE
#from os import listdir, makedirs, unlink
#from os.path import isfile, isdir, join, getmtime, exists
#from math import ceil


'''transform weights to initial seed matrix'''

joints = [
 '00 neck_pitch'
,'01 neck_roll'
,'02 waistroll'
,'03 waistpitch'
,'04/05 shoulderpitch'
,'06/07 shoulderroll'
,'08/09 shoulderyaw'
,'10/11 elbowpitch'
,'12/13 hippitch'
,'14/15 hiproll'
,'16/17 hipyaw'
,'18/19 kneepitch'
,'20/21 anklepitch'
,'22/23 ankleroll'

]


inputnames = [  ####.####.####
               "neck pitch   "
             , "neck roll    "
             , "waist roll   "
             , "waist pitch  "
             , "L shoulder pi"
             , "R shoulder pi"
             , "L shoulder ro"
             , "R shoulder ro"
             , "L shoulder ya"
             , "R shoulder ya"
             , "L elbw pitch "
             , "R elbw pitch "
             , "L hip pitch  "
             , "R hip pitch  "
             , "L hip roll   "
             , "R hip roll   "
             , "L hip yaw    "
             , "R hip yaw    "
             , "L knee pitch "
             , "R knee pitch "
             , "L ankle pitch"
             , "R ankle pitch"
             , "L ankle roll "
             , "R ankle roll "
             , "accel x, y, z"
             , "bias"
             ]

 # arms not used
# +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 +0.0 

 # 11 lhippitch  # 12 rhippitch  # 13 lhiproll   # 14 rhiproll   # 15 lhipyaw    # 16 rhipyaw
# +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0 

 # 17 lkneepitch # 18 rkneepitch # 19 lanklepitc # 20 ranklepitc # 21 lankleroll # 22 rankleroll
# +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0  +0.0 +0.0 +0.0   

 # accel x, y, z # bias



name = 'rocking'
symmetry = "symmetric"
propagation = "original"

filename = "55_rocking.dat"


# For gretchen:
J = 4
D = 20
N = (D+J)*3+4
K = D/2 + J

assert(len(joints) == K)

params = "\t\t\t\t\t\t"

for n in inputnames:
	params += "| {0}".format(n)
params += "\n"


for j in joints:
	params += "# {0}".format(j)
	params += "\n\t\t\t\t\t\t" + N*" 0.0 " + "\n"





header = "name = \"{0}\"\nsymmetry = \"{1}\"\npropagation = \"{2}\"\nparameter = {{\n{3}\n}}\n".format(name, symmetry, propagation, params)



with open(filename, "w") as f:
	f.write(header)


