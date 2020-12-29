#!/usr/bin/python

# Evolution experiment launcher for watching
# + lists available experiments by filter arument -f
# + enumerates and asks for index number of experiment to be watched

import re, argparse, shlex
from subprocess import Popen
from os import listdir, mkdir
from os.path import isfile, isdir

exp_dir   = "../data/exp"
conf_file = "evolution.conf"
binary = "./bin/Release/evolution"
exp_list = []
port0 = 8000

what_state = [2]

def is_experiment(path):
    return isdir(path) \
        and isfile(path+"/"+conf_file)


def is_completed(path):
    conf = path+"/"+conf_file
    with open(conf) as f:
        data = f.read()
    m = re.search("STATUS = (\d+)", data)
    if m:
        return int(m.groups()[0]) in what_state
    print("ERROR: Did not find max. status entry in {0}".format(conf))
    return False


def find_experiments(path, filt, dir_level = 0):
    number = 0
    try:
        dirs = [d for d in listdir(path) if isdir(path+"/"+d)]
    except:
        print("Error while scanning folders.")
        return
    dirs.sort()
    for d in dirs:
        exp_path = path+"/"+d
        if not is_experiment(exp_path):
            print(" {1} [{0}]".format(d, " " * (3*dir_level) + " + "))
            find_experiments(exp_path, filt, dir_level+1)
            #print
            continue

        if filt and filt not in d:
            continue

        result = is_completed(exp_path)
        if result:
            exp_list.append(exp_path.replace(exp_dir+"/", ""))

        print("{2}{0:32} {1:3}".format(d, str(len(exp_list)-1) if result else "---", dir_level*"\t"))
        number += 1


def execute_command(command):
    args = shlex.split(command)
    proc = Popen(args)
    proc.wait()
    return proc.returncode


def watch(expname, port, dry = False):
    command = "{0} -w {1} -p {2}".format(binary, expname, port + port0)
    if not dry:
        exitcode = execute_command(command)
        print "OK." if exitcode==0 else "FAILED. Code {0}".format(exitcode)
    else:
        print(command)

def show_experiments():
    for idx,expname in enumerate(exp_list):
        print("{0:3} {1}".format(idx, expname))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter'     , default='')
    parser.add_argument('-p', '--path'       , default=exp_dir)
    parser.add_argument('-i', '--incomplete' , action='store_true')
    args = parser.parse_args()

    filt = str(args.filter)
    path = str(args.path)

    if args.incomplete:
        what_state.append(1)

    if isdir(path):
        try:
            find_experiments(path, filt)
        except (KeyboardInterrupt, SystemExit):
            print("Aborted by user.")

    while(True):
        inp = raw_input("(press Enter to exit)\nWhich experiment shall I show to you? : ")
        if inp.isdigit():
            idx_num = int(inp)
            if 0 <= idx_num < len(exp_list):
                watch(exp_list[idx_num], idx_num)
        if inp == "":
            break
        else:
            show_experiments()

    print("____\nDONE.")

if __name__ == "__main__": main()
