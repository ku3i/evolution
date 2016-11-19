#!/usr/bin/python

# you may need to install these packages on your machine
# sudo pip install paramiko
# sudo apt-get install libffi6, libffi-dev, python2.7-dev, libssl-dev
# sudo pip install cryptography --force-reinstall

import re, sys, shlex, argparse, getpass, paramiko, time
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join

host_domain = ".informatik.hu-berlin.de"
server_list = [ "gruenau1"
              , "gruenau2"
              , "gruenau3"
              , "gruenau4"
              , "gruenau5"
              , "gruenau6"
              , "gruenau7"
              , "gruenau8"
              ]

def get_num_processes(ssh, verbose):
    s = search_for(ssh, "simloid"  , verbose)
    e = search_for(ssh, "evolution", verbose)
    if e != 2*s:
        print("WARNING: broken process chain.")
    return s

def search_for(ssh, processname, verbose):
    cmd = "ps -e | grep '{}'".format(processname)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    lines = stdout.readlines() + stderr.readlines()

    if verbose:
        print("\n({1}) {0}".format(processname, len(lines)))
        if lines > 0:
            for line in lines:
                print(line),
    return len(lines)

def kill(ssh, processname):
    cmd = "pkill -f -9 {}".format(processname)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    lines = stdout.readlines() + stderr.readlines()


def search_process_on_server(server, user, pswd, verbose):
    print("Connecting to: {0}".format(server)),

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=user, password=pswd, timeout=10)

        num = get_num_processes(ssh, verbose)
        if not verbose:
            print(": {0}". format(num))

        ssh.close()
    except:
        print("FAILED.")

def kill_process_on_server(server, user, pswd):
    print("Connecting to: {0}".format(server)),

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=user, password=pswd, timeout=10)

        kill(ssh, "evolution.py")
        kill(ssh, "simloid")
        kill(ssh, "evolution")


        ssh.close()
        print("KILLED.")
    except:
        print("FAILED.")


def search_all(server_list, user, pswd, verbose):
    for server in server_list:
        search_process_on_server(server+host_domain, user, pswd, verbose)

def kill_all(server_list, user, pswd):
    for server in server_list:
        kill_process_on_server(server+host_domain, user, pswd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-k', '--kill'   , action='store_true')
    args = parser.parse_args()

    user = raw_input("Username: ")
    if user == "":
        print("Aborted.")
        return

    pswd = getpass.getpass()

    if args.kill:
        kill_all(server_list, user, pswd)
    else:
        search_all(server_list, user, pswd, args.verbose)
    print("\n____\nDONE.")

if __name__ == "__main__": main()
