#!/usr/bin/python

# you may need to install these packages on your machine
# sudo pip install paramiko 
# sudo apt-get install libffi6, libffi-dev, python2.7-dev, libssl-dev
# sudo pip install cryptography --force-reinstall

import re, sys, shlex, argparse, getpass, paramiko, time
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join

data_path   = "../data/exp/"

# consider using 'nproc', to determine the number of usable cores
host_domain = ".informatik.hu-berlin.de"
#               servername cores
server_list = [ ("gruenau1",  16)
              , ("gruenau2",  16)
              , ("gruenau3",  32)
              , ("gruenau4",  32)
              , ("gruenau5", 120)
              , ("gruenau6", 120)
              , ("gruenau7", 120)
              , ("gruenau8", 120)
              ]

execute_commands = ["echo 'cd work/diss/evolution; nohup ./evolution.py -r {0} -n {1} -x &' > run.sh", "bash run.sh </dev/null >&/dev/null" ]

def start_experiment(server, robot, num, user, pswd, mul):
    print("Connecting to: {0}".format(server)),

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=user, password=pswd, timeout=10)
        print("SUCCESS. Starting {0} instances: ".format(mul)),
        for i in range(mul):
            for cmd in execute_commands:
                stdin, stdout, stderr = ssh.exec_command(cmd.format(robot, num))
                lines = stdout.readlines() + stderr.readlines()
                for line in lines:
                    print(line)
            print("/"),
            time.sleep(3)
        ssh.close()
        print("DONE.")
    except:
        print("FAILED.")


def start_all(server_list, robot, num, user, pswd, mul):
    server_list.sort(key=lambda tup: tup[1], reverse=True)
    for server,_ in server_list:
        start_experiment(server+host_domain, robot, num, user, pswd, mul)


def main():
    global port_start, num_conductions

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--robot'    , default = "")
    parser.add_argument('-n', '--number'   , default = 0 )
    parser.add_argument('-i', '--instances', default = 1 )
    args = parser.parse_args()

    robot = str(args.robot)
    if robot == "":
        print("No robot defined")
        return 

    num_exp = int(args.number)
    if num_exp == 0:
        print("Number of experiments not specified.")
        return

    mul = int(args.instances)
    if mul > 16:
        print("too many instances.")
        return

    print("selected robot is: {0}".format(robot))
    print("number of experiments: {0}.".format(num_exp))

    user = raw_input("Username: ")
    if user == "":
        print("Aborted.")
        return

    pswd = getpass.getpass()

    start_all(server_list, robot, num_exp, user, pswd, mul)
    print("\n____\nDONE distributing.")

if __name__ == "__main__": main()

