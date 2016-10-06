#!/usr/bin/python

import re, sys, shlex, argparse
from subprocess import Popen, PIPE
from os import listdir
from os.path import isfile, isdir, join

robot_list      = ["crawler", "tadpole", "fourlegged", "humanoid", "_scrtst"]
passphr         = "start"
port_start      = 8000
do_quit         = 0
num_conductions = 1

binary = "./bin/Release/evolution"
data_path = "../data/exp/"
settings_folder = "./settings/"
settings_file_ending = ".setting"
ansi_escape = re.compile(r'\x1b[^m]*m')


def get_available_experiments(robot):
	settings_path = settings_folder + robot
	settings_files = [f for f in listdir(settings_path) if isfile(join(settings_path, f))]
	settings_files.sort()
	return [s.replace(".setting","") for s in settings_files]

def check_binary():
	if isfile(binary): 
		print("Binary is {0}".format(binary))
	else: 
		print("Could not find evolution binary {0}".format(binary))

def execute_command(command):
	args = shlex.split(command)
	proc = Popen(args, stdout=PIPE, stderr=PIPE)
	out, err = proc.communicate()
	exitcode = proc.returncode
	return exitcode, out, err

def conduct(robot, experiment, port, num, dry):
	setting = "{0}{1}/{2}{3}".format(settings_folder, robot, experiment, settings_file_ending)
	expname = "{2}_{0}_{1}".format(robot, experiment, str(num))
	command = "{0} -n {1} -s {2} -p {3} -b"\
		.format(binary, expname, setting, port)
	print(command)

	if isdir(data_path+expname):
		print("\nWARNING: Experiment {0} has already been conducted. Skipping.\n".format(expname))
		return

	if not dry:		
		output_path = "{0}{1}/".format(data_path, expname)
		exitcode, out, err = execute_command(command)
		with open(output_path + "stdout.txt", "w") as out_file:
			out_file.write(ansi_escape.sub('', out))
		with open(output_path + "stderr.txt", "w") as err_file:
			err_file.write(ansi_escape.sub('', err))
		print "returned {0}".format(exitcode)


def conduct_all(robot, experiments, port, num, dry):
	for e in experiments:
		conduct(robot, e, port, num, dry)
		port += 1


def main():
	global port_start, num_conductions
	
	parser = argparse.ArgumentParser()
	parser.add_argument('-r', '--robot' , default='fourlegged')
	parser.add_argument('-n', '--number', default=num_conductions)
	parser.add_argument('-p', '--port'  , default=port_start)
	args = parser.parse_args()

	robot           = str(args.robot)
	num_conductions = int(args.number)
	port_start      = int(args.port)

	print("selected robot is: {0}".format(robot))

	check_binary()
	experiments_available = get_available_experiments(robot)

	print("The following experiments will be conducted:")
	for i in experiments_available: print("\t{0}/{1}".format(robot,i))

	if (num_conductions > 1):
		print("Every experiment will be repeated {0} times.".format(num_conductions))
	else:
		print("Every experiment will be executed once.")

	var = raw_input("Enter '{0}' to proceed: ".format(passphr))
	dry_run = (var != passphr)

	for num in range(num_conductions):
		conduct_all(robot, experiments_available, port_start, num, dry_run)

	print("\nSimulations done.\n___\n")


if __name__ == "__main__": main()







