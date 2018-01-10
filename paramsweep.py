#!/usr/bin/python

import re, sys, shlex, argparse
from subprocess import Popen, PIPE
from os import listdir, makedirs, unlink
from os.path import isfile, isdir, join, getmtime, exists
from math import ceil
import numpy as np

port_start      = 8000
def_number      = 20

nice = 19
binary = "./bin/Release/evolution-1.0.1"
data_path = "../data/exp/"
settings_folder = "./settings/"
settings_file_ending = ".setting"

ansi_escape = re.compile(r'\x1b[^m]*m')


def check_binary():
	if isfile(binary):
		print("Binary is: {0}".format(binary))
	else:
		print("Could not find evolution binary {0}".format(binary))


def execute_command(command):
	args = shlex.split(command)
	proc = Popen(args, stdout=PIPE, stderr=PIPE)
	out, err = proc.communicate()
	exitcode = proc.returncode
	return exitcode, out, err


def override_settings(filename, setlist = ()):
	if setlist:
		with open(filename, "r") as f:
			data = f.read().format(*setlist)
			newfile = filename+".tmp"
			with open(newfile, "w+") as n:
				n.write(data)
			return newfile
	else:
		return filename


def conduct(robot, experiment, port, num, dry, add_settings = ()):
	setting = "{0}{1}/{2}{3}".format(settings_folder, robot, experiment, settings_file_ending)
	if not dry:
		setting = override_settings(setting, add_settings)

	expname = "{0}/{2}_{0}_{1}".format(robot, experiment, num)
	command = "nice -n {4} {0} -n {1} -s {2} -p {3} -b"\
		.format(binary, expname, setting, port, nice)

	if isdir(data_path+expname):
		print(" + {0} DONE. SKIPPED.".format(expname))
		return False
	else:
		print(" > {0}".format(expname)),

	if not exists(data_path+robot):
		makedirs(data_path+robot)

	if not dry:
		output_path = "{0}{1}/".format(data_path, expname)
		try:
			exitcode, out, err = execute_command(command)
			with open(output_path + "stdout.txt", "w") as out_file:
				out_file.write(ansi_escape.sub('', out))
			with open(output_path + "stderr.txt", "w") as err_file:
				err_file.write(ansi_escape.sub('', err))
		except:
			print("ERROR")

		if exitcode==0:
			print("OK.")
			return True
		else:
			print("FAILED. Code {0}".format(exitcode))
			return False
	else:
		print(command)
		return False


def tail(filename):
	with open(filename, "rb") as f:
		first = f.readline()      # Read the first line.
		f.seek(-2, 2)             # Jump to the second last byte.
		while f.read(1) != b"\n": # Until EOL is found...
			f.seek(-2, 1)         # ...jump back the read byte plus one more.
		last = f.readline()       # Read last line.
		return last


def main():
	global port_start

	parser = argparse.ArgumentParser()
	parser.add_argument('-r', '--robot' , required=True)
	parser.add_argument('-p', '--port'  , default=port_start)
	parser.add_argument('-d', '--dry'   , action='store_true')
	parser.add_argument('-n', '--number', default=def_number)
	parser.add_argument('-m', '--meta'  , default=0.5)
	args = parser.parse_args()

	robot           = str(args.robot)
	port_start      = int(args.port)

	check_binary()

	experiment = "31_p_0fw_e_param_sweep"
	idx = 0
	me = args.meta

	for ps in np.linspace(5, 100, num=args.number):
		for mr in [round(x,10) for x in np.logspace(-3, 0, num=args.number)]:
			print("Conducting with mutation rate {0} and popsize {1} and meta {2}".format(mr,int(ps),me))
			res = conduct(robot, experiment, port_start, idx, args.dry, add_settings=(int(ps),mr,me))
			port_start += 1 if port_start != 8089 else 2
			# get fitness
			if args.dry:
				continue
			if res:
				line = "{0} {1} {2}".format(int(ps),mr,tail(data_path+robot+"/"+str(idx)+"_"+robot+"_"+experiment+"/evolution.log"))
				with open("results.log", "a+") as fout:
					fout.write(line)
			idx += 1

	print("\n____\nDONE.\n")


if __name__ == "__main__": main()
