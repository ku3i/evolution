#!/usr/bin/python

import sys, socket, subprocess, time, random, re, shlex
from os import listdir, makedirs
from os.path import isfile, isdir, join, exists

# globals
sim_path = "./bin/Release/simloid"
address  = "127.0.0.1"
port     = random.randint(7000, 9000)
bufsize  = 4096
scene_id = 3
robot_ids = [ [32,  0, 0.00 ] # normal hannah
            , [37,  0, 0.10 ] # random hannah
            , [37, 42, 1.00 ]
            , [37, 43, 1.00 ]
            , [37, 44, 1.00 ]
            , [37, 45, 1.00 ]
            , [37, 46, 1.00 ]
            , [37, 23, 0.10 ]
            , [37, 23, 0.25 ]
            , [37, 23, 0.50 ]
            , [37, 23, 1.00 ]
            , [31,  0, 0.00 ] # other robots
            , [11,  0, 0.00 ]
            , [20,  0, 0.00 ]
            , [40,  0, 0.00 ]
            , [50,  0, 0.00 ]
            , [60,  0, 0.00 ]
            , [80,  0, 0.00 ]
            , [90,  0, 0.00 ]
            ]


param_list = [ "weight_body"
             , "weight_leg_upper"
             , "weight_leg_lower"
             , "length_body"
             , "length_leg_upper"
             , "length_leg_lower"
             , "leg_ratio"
             , "knee_y_offset"				
             , "torque"           
             , "ground_friction"  
             , "bristle_displ_max"
             , "bristle_stiffness"
             , "sticking_friction"
             , "coulomb_friction" 
             , "fluid_friction"   
             , "stiction_range"   
             , "V_in"             
             , "kB"               
             , "kM"               
             , "R_i_inv"
             ] 

MSG = '\033[93m' #orange terminal color

class constants:
	config_file = "evolution.conf"
	fitness_log = "fitness.log"
	data_log    = "data.log"
	exp_dir     = "../data/exp/"


def is_experiment(path):
    return isdir(path) \
        and isfile(path+"/"+constants.config_file)


def is_completed(path):
    conf = path+"/"+constants.config_file
    with open(conf) as f:
        data = f.read()
    m = re.search("STATUS = (\d+)", data)
    if m:
        return 2 == int(m.groups()[0])
    print("ERROR: Did not find status entry in {0}".format(conf))
    return False


def get_robot_rand_init(path):
    conf = path.rstrip('/') + "/" +constants.config_file
    with open(conf) as f:
        data = f.read()
    m = re.search("RANDOM_INIT = (\d+)", data)
    if m:
        id = int(m.groups()[0])
        #print("Robot ID is: {}".format(id))
        return id
    else:
        print("ERROR: Did not find random init entry in {0}".format(conf))
        return 0


def get_int_from_str(msg, item):
    m = re.search("{0}=(\d+)".format(item), msg)
    return int(m.groups()[0]) if m else None


def get_float_from_str(msg, item):
    m = re.search("{0}=([+-]?([0-9]*[.])?[0-9]+)".format(item), msg)
    return float(m.groups()[0]) if m else None


def get_experiments(path):
    return ["{0}/{1}/".format(path, d) for d in sorted(listdir(path)) if isdir(join(path, d))]


def get_avg_fitness(path):
    if not isfile(path+"/"+constants.fitness_log):
        return (0.0,0.0)
    with open(path+"/"+constants.fitness_log) as f:
        lines = [float(x) for x in f.readlines()]
    return (sum(lines)/len(lines), max(lines)) if len(lines) > 0 else (0.0,0.0)



def get_random_seeds():
	path = "../../data_dump/hannah_randomized"
	exp_list = get_experiments(path)
	ret_list = []
	for e in exp_list: 
		if is_experiment(e) and is_completed(e):		
			rnd_init = get_robot_rand_init(e)
			(favg,fmax) = get_avg_fitness(e)
			ret_list.append( (rnd_init,favg,fmax) )
	return ret_list

		

class Joint:
	def __init__(self, params):
		#traits
		self.id       =   int(params[0])
		self.type     =       params[1]
		self.sym      =       params[2]
		self.stop_lo  = float(params[3])
		self.stop_hi  = float(params[4])
		self.def_pos  = float(params[5])
		self.name     =       params[6]

		#state
		self.position = 0.0
		self.velocity = 0.0
		self.voltage  = random.uniform(-0.01, +0.01)

	def printf(self):
		print("\t{0} = {1} (def: {2}".format(self.id, self.name, self.def_pos))


class Simloid:
	def __init__(self, address, port):
		self.sock = socket.socket()
		self.sock.connect((address, port))
		self.recv_robot_info()


	def recv_robot_info(self):
		msg = self.sock.recv(bufsize)
		robot_info = msg.split()
		
		self.num_bodies = int(robot_info.pop(0))
		self.num_joints = int(robot_info.pop(0))
		self.num_accels = int(robot_info.pop(0))
		self.joints = []		

		for i in range(self.num_joints):
			j = Joint(robot_info[0:7])
			self.joints.append(j)
			robot_info = robot_info[7:]

		print(MSG + "Robot has {0} joints:".format(self.num_joints))
		for j in self.joints: j.printf()

		print(MSG + "and {0} bodies and {1} acceleration sensors".format(self.num_bodies, self.num_accels))
		self.sock.send("ACK\n")
		self.recv_sensor_status()
		self.sock.send("UA 0\nGRAVITY ON\nDONE\n")
		self.recv_sensor_status()

		print(MSG + "Robot initialized.\n\n")
		self.sock.send("DESCRIPTION\n")
		return self.sock.recv(bufsize)


	def send_motor_controls(self):
		cmd = "UX " + " ".join(str(j.voltage) for j in self.joints) + "\nDONE\n"
		self.sock.send(cmd)
		return self.sock


	def recv_sensor_status(self):
		msg = self.sock.recv(bufsize)
		result = self.sock and (len(msg) > 0)
		if (result):
			status = msg.split()
			#print status
			time = float(status.pop(0))
			for j in self.joints: j.position = float(status.pop(0))
			for j in self.joints: j.velocity = float(status.pop(0))

		return result


	def loop(self, record = False):
		if record:
			self.sock.send("RECORD\n")
		return self.send_motor_controls() and self.recv_sensor_status()


	def change_model(self, model_id):
		cmd = "MODEL {0}\nDONE\n".format(model_id)
		self.sock.send(cmd)
		self.recv_robot_info()

	def change_to_random_model(self, model_id, instance, amplitude):
		cmd = "MODEL {0} 2 {1} {2}\nDONE\n".format(model_id, instance, amplitude)
		print(cmd)
		self.sock.send(cmd)
		return self.recv_robot_info()

	def toggle_fixate(self):
		self.sock.send("FIXED 0\n")


def control_loop(joints):
	# simple p-ctrl holding the default position
	for j in joints:
		j.voltage = 5.0 * (j.def_pos - j.position)
	

def save_to_file(target_list, filename):
	with open(filename, "w") as f:
		f.write("rnd_init favg fmax "+" ".join(param_list)+"\n")
		for t in target_list:
			msg = "{0} {1:+e} {2:+e}".format(t.rnd_init, t.favg, t.fmax)
			for p in param_list:
				msg += " {0:+e}".format(t.params[p])
			f.write(msg+"\n")

def main(argv):

	random.seed()
	i = 0
	subprocess.Popen([sim_path, "--port", str(port), "--robot", "38", "--scene", str(scene_id)])
	time.sleep(0.5)
	simloid = Simloid(address, port)
	result = True

	cycles = 0

	exp_list = get_random_seeds()

	target_list = []

	while (result):
			try:
				target = lambda: None
				cycles += 1

				if cycles==1: 
					simloid.toggle_fixate()

				if cycles==100:
					simloid.toggle_fixate()

				result = simloid.loop(record = (cycles == 15))
				control_loop(simloid.joints)

				if cycles == 300:
					cycles = 0
					i += 1
					if i == len(exp_list):
						break;
					(target.rnd_init,target.favg,target.fmax) = exp_list[i] 
					descr = simloid.change_to_random_model(38, target.rnd_init, 1.0)
					print("robot description: {0}".format(descr))
					target.params = {}
					for p in param_list:
						target.params[p] = get_float_from_str(descr, p)
					target_list.append(target)

			except KeyboardInterrupt: # press CTRL + C to exit
				save_to_file(target_list,"foo.txt")
				print(MSG + "Bye___")
				sys.exit()

	save_to_file(target_list,"foo.txt")
				
	


if __name__ == "__main__": main(sys.argv)

