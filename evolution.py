#!/usr/bin/python

import re, sys, shlex, argparse
from subprocess import Popen, PIPE
from os import listdir, makedirs, unlink
from os.path import isfile, isdir, join, getmtime, exists
from math import ceil

passphr         = "start"
port_start      = 8000
do_quit         = 0
num_conductions = 1

nice = 19
binary = "./bin/Release/evolution"
data_path = "../data/exp/"
settings_folder = "./settings/"
settings_file_ending = ".setting"
tournament_prefix = "tournament/tmt_"
ansi_escape = re.compile(r'\x1b[^m]*m')

def get_available_experiments(robot):
	settings_path = settings_folder + robot
	if not isdir(settings_path):
		print("ERROR: No such settings directory: {0}".format(settings_path))
		exit(-1)
	print("Setting directory is: {0}".format(settings_path))
	settings_files = [f for f in listdir(settings_path) if isfile(join(settings_path, f))]
	settings_files.sort()
	return [s.replace(".setting","") for s in settings_files]

def check_binary():
	if isfile(binary):
		print("Binary is: {0}".format(binary))
	else:
		print("Could not find evolution binary {0}".format(binary))

def is_up_to_date(tournament, expfolderlist):
	for e in expfolderlist:
		if getmtime(data_path+e) > getmtime(data_path+tournament):
			return False
	return True

def get_popsize(setting):
	with open(setting, 'r') as f:
		for line in f.readlines():
			m = re.search("^POPULATION_SIZE = (\d+)$", line)
			if m:
				#print("\tPOPSIZE = {}".format(m.groups()[0]))
				return int(m.groups()[0])
	print("WARNING: No popsize defined in file: {}".format(setting))
	return 0

def create_population_from(expfolderlist, popsize):
	#print("\tCreate tournament population from {} experiments.".format(len(expfolderlist)))
	assert popsize > len(expfolderlist), "Error: Popsize too small."
	lines_per_file = int(ceil(float(popsize) / len(expfolderlist)))
	poplist = []
	for e in expfolderlist:
		with open(data_path+e+"/population.log", 'r') as f:
			for i in range(lines_per_file):
				poplist.append(f.readline())
	assert len(poplist) >= popsize, "poplist {0} {1}".format(len(poplist), popsize)
	return poplist[0:popsize]

def execute_command(command):
	args = shlex.split(command)
	proc = Popen(args, stdout=PIPE, stderr=PIPE)
	out, err = proc.communicate()
	exitcode = proc.returncode
	return exitcode, out, err

def clean_folder(folder):
	print("\tCleaning folder: {}".format(folder))
	for f in listdir(folder):
		file_path = join(folder, f)
		if isfile(file_path):
			print("\t + removing file: {}".format(file_path))
			unlink(file_path)
		#elif isdir(file_path): shutil.rmtree(file_path)

def conduct(robot, experiment, port, num, dry):
	setting = "{0}{1}/{2}{3}".format(settings_folder, robot, experiment, settings_file_ending)
	expname = "{0}/{2}_{0}_{1}".format(robot, experiment, num)
	command = "nice -n {4} {0} -n {1} -s {2} -p {3} -b"\
		.format(binary, expname, setting, port, nice)

	if isdir(data_path+expname):
		print(" + {0} DONE. SKIPPED.".format(expname))
		return
	else:
		print(" > {0}".format(expname)),

	if not exists(data_path+robot):
		makedirs(data_path+robot)

	if not dry:
		output_path = "{0}{1}/".format(data_path, expname)
		exitcode, out, err = execute_command(command)
		with open(output_path + "stdout.txt", "w") as out_file:
			out_file.write(ansi_escape.sub('', out))
		with open(output_path + "stderr.txt", "w") as err_file:
			err_file.write(ansi_escape.sub('', err))
		print "OK." if exitcode==0 else "FAILED. Code {0}".format(exitcode)
	else:
		print(command)

def conduct_all(robot, experiments, port, num, dry):
	for e in experiments:
		conduct(robot, e, port, num, dry)
		port += 1
	return port


def start_tournament(robot, experiment, port, num, dry):
	setting = "{0}{1}/{4}{2}{3}".format(settings_folder, robot, experiment, settings_file_ending, tournament_prefix)
	tournament = "{0}/T_{0}_{1}".format(robot, experiment)
	command = "nice -n {4} {0} -n {1} -s {2} -p {3} -b"\
		.format(binary, tournament, setting, port, nice)

	expfolderlist = ["{0}/{2}_{0}_{1}".format(robot, experiment, n) for n in range(num)]


	if not isfile(setting):
		print(" ! {0} NOT AVAILABLE -> SKIPPED.".format(setting))
		return

	if isdir(data_path+tournament):
		if is_up_to_date(tournament, expfolderlist):
			print(" + {0} DONE. SKIPPED.".format(tournament))
			return
		else:
			print(" + {0} OUTDATED -> REFRESHING.".format(tournament))
			clean_folder(data_path+tournament)
	else:
		print(" > {0}".format(tournament)),

	if not exists(data_path+robot+"/tournament"):
		makedirs(data_path+robot+"/tournament")

	if not dry:
		popsize = get_popsize(setting)
		poplist = create_population_from(expfolderlist, popsize)
		with open(data_path+robot+"/tournament/{0}.log".format(experiment), "w") as f:
			for line in poplist:
				f.write(line)

		output_path = "{0}{1}/".format(data_path, tournament)
		exitcode, out, err = execute_command(command)
		with open(output_path + "stdout.txt", "w") as out_file:
			out_file.write(ansi_escape.sub('', out))
		with open(output_path + "stderr.txt", "w") as err_file:
			err_file.write(ansi_escape.sub('', err))
		print "OK." if exitcode==0 else "FAILED: Code {0}".format(exitcode)
	else:
		print(command)


def start_all_tournaments(robot, experiments, port, num, dry_run):
	print("\nTournaments:")
	for e in experiments:
		start_tournament(robot, e, port, num, dry_run)

def main():
	global port_start, num_conductions

	parser = argparse.ArgumentParser()
	parser.add_argument('-r', '--robot' , default='_scrtst')
	parser.add_argument('-n', '--number', default=num_conductions)
	parser.add_argument('-p', '--port'  , default=port_start)
	parser.add_argument('-x', '--nopass', action='store_true')
	args = parser.parse_args()

	robot           = str(args.robot)
	num_conductions = int(args.number)
	port_start      = int(args.port)

	check_binary()
	experiments_available = get_available_experiments(robot)

	print("The following experiments will be conducted:")
	for i in experiments_available: print("\t{0}/{1}".format(robot,i))

	if (num_conductions > 1):
		print("Every experiment will be repeated {0} times.".format(num_conductions))
	else:
		print("Every experiment will be executed once.")

	dry_run = False
	if not args.nopass:
		var = raw_input("Enter '{0}' to proceed: ".format(passphr))
		dry_run = (var != passphr)

	port = port_start
	for num in range(num_conductions):
		port = conduct_all(robot, experiments_available, port, num, dry_run)

	start_all_tournaments(robot, experiments_available, port, num_conductions, dry_run)

	print("\n____\nDONE.\n")


if __name__ == "__main__": main()
