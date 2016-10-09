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

execute_commands = ["ps -e | grep 'evolution\|simloid'"]

def search_process_on_server(server, user, pswd):
    print("Connecting to: {0}".format(server)),

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=user, password=pswd, timeout=10)
        print("SUCCESS.")
        for cmd in execute_commands:        
            stdin, stdout, stderr = ssh.exec_command(cmd)
            lines = stdout.readlines() + stderr.readlines()
            if lines:
                for line in lines:
                    print(line),
                print("__")
        ssh.close()
    except:
        print("FAILED.")


def search_all(server_list, user, pswd):
    for server in server_list:
        search_process_on_server(server+host_domain, user, pswd)


def main():
    user = raw_input("Username: ")
    if user == "":
        print("Aborted.")
        return

    pswd = getpass.getpass()

    search_all(server_list, user, pswd)
    print("\n____\nDONE.")

if __name__ == "__main__": main()

