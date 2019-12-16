# Cleans the directory, compiles anchor code and generates a different hex for each ID.
import subprocess
from subprocess import Popen, PIPE, STDOUT
import os
import fabric
import paramiko
import spur
import time
from Make import *

SHELL_ON = True
DEFAULT_NB_ANCHORS = 15
HOSTS_LIST = ['Rasp1','Rasp2','Rasp3','Rasp4']
USERNAMES = {'Rasp1':'pi','Rasp2':'pi','Rasp3':'pi','Rasp4':'pi'}
USERS_PWD = {'Rasp1':'raspberry','Rasp2':'raspberry','Rasp3':'raspberry','Rasp4':'raspberry'}
HOSTPATH = '/home/pi/Desktop'
CONFIG_PATH = 'Config'
DEFAULT_CONF = 'config.txt'

DEFAULT_PROJECT_NAME = 'Anchor'
hex_name = 'anchor'

DEFAULT_NB_ANCHORS = 1
DEFAULT_ID = '1'


PROJECTS_DIR = 'Projects'
BIN_DIR = 'bin'
ID_LENGTH = 1

class Console():
	_console = None
	@property
	def console(self):
		return Console._console
	@console.setter
	def console(self,p):
		Console._console = p

	def shell_exec(self,cmd):
		"""executes the given command in a shell.
		Can display the output into the compilation menu console if passed in argument."""
		#subprocess.run(cmd, SHELL_ON)
		if self.console == None:

			p = Popen(cmd,shell = SHELL_ON)
			p.wait()
		else:
			self.console.console_handler(cmd)
	def print(self, msg):
		"""prints the message in the current console. Defaults to the current shell"""
		if self.console == None:
			print(msg)
		else:
			self.console.console_display(msg)

console = Console()

def read_config(configname = DEFAULT_CONF):
	"""reads and extracts the data from config file, i.e. Raspberry host and user names,
	anchors names, and raspberry/anchors association"""

	hosts_list = []
	usernames = {}
	passwords = {}
	anchors_names = []
	anchors_table = {}

	filename = CONFIG_PATH + "/" + configname

	with open(filename) as f:
		for line in f:
			if line[0] == '#':
				# comment
				continue
			names = line.split()
			i = 0
			for name in names:
				if (i == 0):
					# Rasp hostname
					hostname = name
					hosts_list.append(hostname)
				elif (i == 1):
					# Rasp usernames
					usernames[hostname] = name
				elif (i  == 2):
					# Rasp passwords
					passwords[hostname] = name
				else:
					# anchor name
					anchors_names.append(name)

					# creating an entry in anchors/raspberry association table dictionary
					if not(hostname in anchors_table):
						#creating the entry
						anchors_table[hostname] = []
					anchors_table[hostname].append(name)

				i += 1
	return([hosts_list,usernames,passwords,anchors_names,anchors_table])






def gen_anchors_id(nb_anchors = DEFAULT_NB_ANCHORS):
	"""generates a list of id. The number of ids is given in args"""
	if (nb_anchors > 26):
		console.print("cannot handle " + str(nb_anchors) + "\n")
		console.print("the number of anchors should be below 26")

	else:
		anchors_name = []
		for i in range(nb_anchors):
			# generates successive letters starting from A
			anchors_name.append( str(chr(65 + i) ) )

	return (anchors_name)

def shell_exec(cmd):
	"""executes the given command in a shell.
	Can display the output into the compilation menu console if passed in argument."""
	#subprocess.run(cmd, SHELL_ON)

	p = Popen(cmd,shell = SHELL_ON)
	p.wait()

def clean(project_name):
	"""removes all previous compiled files from directory"""
	console.shell_exec("cd teensy3 && make softclean PROJECTNAME=" + project_name)

def compile_hex_file(project_name = DEFAULT_PROJECT_NAME, nb_anchors = DEFAULT_NB_ANCHORS, id = DEFAULT_ID, id_idx = DEFAULT_ID):
	# .hex files generation
	make_calls, obj_list = get_dependency_rules(project_name)

	# compiling dependencies from other projects

	for call in make_calls:
		console.shell_exec(call)

	obj_list_str = ""
	for obj in obj_list:
		obj_list_str += obj + " "
	console.shell_exec("cd teensy3 && make PROJECTNAME=" + project_name + " BINNAME=" + hex_name + id  + " NB_ANCHORS=" + str(nb_anchors) + " ANCHORID=" + str(id_idx) + " OTHER_PROJECTS_OBJS_FILES=" + obj_list_str)

def compilation(nb_anchors, project_name = DEFAULT_PROJECT_NAME):
	"""compiles main.cpp and generates one specific anchor{ID}.hex with a unique ID for each anchor"""
	anchors_id = gen_anchors_id(nb_anchors)
	id_idx = 1

	for id in anchors_id:
		compile_hex_file(project_name, nb_anchors, id, id_idx)

		id_idx += 1
		# deletes main.o such as reassembling main.o at the next iteration
		clean(project_name)


def send_hex_file(file, destination,password,path, project_name):
	"""sends hex file to raspberry with the given ip address"""
	# retrieving hex file's path
	# filename = $(PROJECTNAME)$(ID).hex
	#project_name = file.split('.')[0][:-ID_LENGTH]
	file_path = PROJECTS_DIR + '/' + project_name + '/' + BIN_DIR + '/' + file
	console.shell_exec("pscp -scp -pw " + password + " " + file_path + " " + destination + ":" + path)


def deploy_hex_files(config = DEFAULT_CONF, project_name = DEFAULT_PROJECT_NAME):
	"""triggers the compilation and deploys the hex files on the raspberry hosts"""

	# getting config
	[hosts_list,usernames,passwords,anchors_names,anchors_table] = read_config(config)
	nb_anchors = len(anchors_names)

	# cleaning previous local hex files
	clean(project_name)

	# compiling main file, generating an hex file with unique ID for each anchor
	compilation(nb_anchors, project_name)
	for host in hosts_list:
		# flushing previous hex files
		local_clean(host, usernames[host],passwords[host])



	for host in hosts_list:
		for anchor in anchors_table[host]:
			filename = hex_name + anchor + ".hex"
			destination = usernames[host] + "@" + host
			path = HOSTPATH
			pwd = passwords[host]
			send_hex_file(filename, destination,pwd,path,project_name)


def local_flash(hostname,username,password,anchors_list):
	"""triggers anchor flashing on the given rasp host"""
	#starting ssh client

	with paramiko.SSHClient() as ssh:
	#ssh.connect(hostname,username = username,password = password)
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(hostname,port =22,username = username, password = password)

		# cleaning previous hex files
		(stdin, stdout, stderr) = ssh.exec_command('ls')


		# flashing the anchors in anchor_list
		for anchor in anchors_list:
			console.print("flashing anchor " + anchor + "..." )
			(stdin, stdout, stderr) = ssh.exec_command('nohup /home/pi/Desktop/teensy_loader_cli -mmcu=mk20dx256 -s -v ' + '/home/pi/Desktop/anchor' + anchor + '.hex')
			stdout.channel.recv_exit_status()
			console.print('nohup ~/Desktop/teensy_loader_cli -mmcu=mk20dx256 -s -v ' + '~/Desktop/anchor' + anchor + '.hex')

			for line in stdout.readlines():
				console.print(line)
			console.print("flashed !")

def local_clean(hostname,username,password):
	"""triggers anchor flashing on the given rasp host"""
	#starting ssh client

	#with paramiko.SSHClient() as ssh:
	#ssh.connect(hostname,username = username,password = password)
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	console.print(hostname + " " + username)
	ssh.connect(hostname = hostname,port =22,username = username, password = password,timeout = 3)


	# cleaning previous hex files
	(stdin, stdout, stderr) = ssh.exec_command('ls')


	# flushing the anchors in anchor_list

	(stdin, stdout, stderr) = ssh.exec_command('rm  ~/Desktop/*.hex')
	stdout.channel.recv_exit_status()
	ssh.close()

def global_clean(config = DEFAULT_CONF):
	[hosts_list,usernames,passwords,anchors_names,anchors_table] = read_config(config)
	for host in hosts_list:
		local_clean(host,usernames[host],passwords[host])





def global_flash(config = DEFAULT_CONF):
	"""triggers every local flash given in the config file"""
	[hosts_list,usernames,passwords,anchors_names,anchors_table] = read_config(config)

	for host in hosts_list:
		# getting the anchors associated to the host
		anchors_list = anchors_table[host]
		console.print(anchors_list)
		console.print(host)
		console.print(usernames[host])
		console.print(passwords[host])

		# flashing the anchors given in the config file

		local_flash(host, usernames[host],passwords[host],anchors_list)











if __name__ == "__main__":
	#deploy_hex_files('config2.txt', 'Anchor_c')
	#global_flash('config2.txt')
	compilation(1, 'Anchor_c')
