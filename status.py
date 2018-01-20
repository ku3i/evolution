#!/usr/bin/python

import re, argparse
from os import listdir, mkdir
from os.path import isfile, isdir

exp_dir   = "../data/exp"
lib_dir   = "../data/lib"
conf_file = "evolution.conf"
log_file  = "evolution.log"
fit_log   = "fitness.log"
pop_file  = "population.log"
seed_fend = ".dat"

behaviors = { "0fw" : "forwards"
            , "1bw" : "backwards"
            , "2tu" : "turning"
            , "3si" : "sidewards"
            , "4ro" : "rolling"
            }

fitness = { "e" : "efficient"
          , "f" : "fast"     }


def decode_shortname(filename):
    #e.g. 4_tadpole_10_p_0fw_e
    m = re.search("(\d+)_([a-zA-Z]+)_(\d+)_([a-zA-Z])_(\w+)_(e|f)([shr]*).dat", filename) #TODO decode stop, rocks, hurdles etc.
    if m:
        name = "{0} {1} {2} no.{3}".format( m.groups()[1]            \
                                          , behaviors[m.groups()[4]] \
                                          , fitness[m.groups()[5]]   \
                                          , int(m.groups()[0])       )
        return name
    print("Name did not match conventions: {0}".format(filename))
    return filename


def create_seed(path, filename, params):
    print (" >> lib")
    with open(lib_dir+"/"+filename, "w") as f:
        f.write("name = \"{0}\"\n".format(decode_shortname(filename)))
        f.write("symmetry = \"{0}\"\n".format("symmetric" if is_symmetric_controller(path) else "asymmetric"))
        f.write("propagation = \"original\"\n")
        f.write("parameter = {{{0}}}\n".format(params.rstrip()))


def get_best_individual(path):
    filename = path+"/"+pop_file
    if not isfile(filename):
        print("Error: No population file: {0}".format(filename))
        return None
    with open(filename, "rb") as f:
        first = f.readline()
        return first


def get_number_of_cur_trials(path):
    log = path+"/"+log_file
    if not isfile(log):
        return 0
    return sum(1 for line in open(log))


def is_experiment(path):
    return isdir(path) \
        and isfile(path+"/"+conf_file) \
        and isfile(path+"/"+log_file)


def is_symmetric_controller(path):
    conf = path+"/"+conf_file
    with open(conf) as f:
        data = f.read()
    m = re.search("SYMMETRIC_CONTROLLER = (YES|NO)", data)
    if m:
        return True if m.groups()[0]=="YES" else False
    print("ERROR: Did not find symmetric controller entry in {0}".format(conf))
    return False


def get_number_of_max_trials(path):
    conf = path+"/"+conf_file
    with open(conf) as f:
        data = f.read()
    m = re.search("MAX_TRIALS = (\d+)", data)
    if m:
        return int(m.groups()[0])
    print("ERROR: Did not find max. trials entry in {0}".format(conf))
    return 1 # avoid devision by zero


def find_experiments(path, filt, getseed, dir_level = 0):
    total = 0
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
            find_experiments(exp_path, filt, getseed, dir_level+1)
            #print
            continue

        if filt and filt not in d:
            continue

        max_trials = get_number_of_max_trials(exp_path)
        cur_trials = get_number_of_cur_trials(exp_path)
        result = int(cur_trials*100.0/max_trials)
        avgf,maxf = get_avg_fitness(exp_path)
        print("{5}{0:32} {1:3d}% ({2:6d}/{3:6d}) {4} f:{6: 7.3f} ({7: 7.3f})".format(d, result, cur_trials, max_trials, "OK." if result==100 else "", dir_level*"\t", avgf,maxf)),
        number += 1
        total += result

        # get best individual and copy to lib_dir
        if getseed and result==100:
            best = get_best_individual(exp_path)
            if best:
                create_seed(exp_path, d+seed_fend, best)
        else:
            print

    if number > 0:
        print("{1}{0}".format("-"*37, dir_level*"\t"))
        print("{3}{0:32} {1:3d}% {2}".format("Total: ", total/number, "COMPLETE." if int(total/number)==100 else "", dir_level*"\t"))


def get_avg_fitness(path):
    if not isfile(path+"/"+fit_log):
        return 0.0
    with open(path+"/"+fit_log) as f:
        lines = [float(x) for x in f.readlines()]
    return (sum(lines)/len(lines), max(lines)) if len(lines) > 0 else (0.0,0.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter' , default='')
    parser.add_argument('-p', '--path'   , default=exp_dir)
    parser.add_argument('-g', '--getseed', action='store_true')
    args = parser.parse_args()

    filt = str(args.filter)
    path = str(args.path)

    # create library dir, if it is not already there
    if args.getseed and not isdir(lib_dir):
        mkdir(lib_dir)

    if isdir(path):
        try:
            find_experiments(path, filt, getseed = args.getseed)
        except (KeyboardInterrupt, SystemExit):
            print("Aborted by user.")
    else:
        print("ERROR: Wrong path.")
        exit(-1)

    print("____\nDONE.")

if __name__ == "__main__": main()
