# Cleans the directory, compiles anchor code and generates a different hex for each ID.
import subprocess
import os
import sys
import fabric
import paramiko
import spur
import time

SHELL_ON = True
DEFAULT_NB_ANCHORS = 15
HOSTS_LIST = ['Rasp1','Rasp2','Rasp3','Rasp4']
USERNAMES = {'Rasp1':'pi','Rasp2':'pi','Rasp3':'pi','Rasp4':'pi'}
USERS_PWD = {'Rasp1':'raspberry','Rasp2':'raspberry','Rasp3':'raspberry','Rasp4':'raspberry'}
HOSTPATH = '/home/pi/Desktop'
CONFIG_PATH = 'Config'
DEFAULT_CONF = 'config.txt'

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
			names = line.split()
			i = 0
			if (line[0] == '#'):
                                # the line is commented
                                continue
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
		print("cannot handle " + str(nb_anchors) + "\n")
		print("the number of anchors should be below 26")

	else:
		anchors_name = []
		for i in range(nb_anchors):
			# generates successive letters starting from A
			anchors_name.append( str(chr(65 + i) ) )

	return (anchors_name)





def clean():
	"""removes all previous compiled files from directory"""
	subprocess.run("make clean",shell = SHELL_ON)


def compilation(nb_anchors):
	"""compiles main.cpp and generates one specific anchor{ID}.hex with a unique ID for each anchor"""

	anchors_id = gen_anchors_id(nb_anchors);
	id_idx = 1
	for id in anchors_id:
		# .elf files generation
		# dependencies will be compiled only the first time
		subprocess.run("make anchor" + id + ".elf " + "TARGET=" + "anchor" + id + " NB_ANCHORS=" + str(nb_anchors) + " ANCHORID=" + str(id_idx) , shell = SHELL_ON )

		# .hex files generation
		subprocess.run("make anchor" + id + ".hex " + "TARGET=" + "anchor" + id + " NB_ANCHORS=" + str(nb_anchors) + " ANCHORID=" + str(id_idx), shell = SHELL_ON)

		id_idx += 1
		# deletes main.o such as reassembling main.o at the next iteration
		subprocess.run("make softclean", shell = SHELL_ON)


def send_hex_file(file, destination,password,path):
	"""sends hex file to raspberry with the given ip address"""
	p = subprocess.Popen("pscp -scp -pw " + password + " " + file + " " + destination + ":" + path)
	out, err = p.communicate()
	errcode = p.returncode


def deploy_hex_files(config = DEFAULT_CONF):
	"""triggers the compilation and deploys the hex files on the raspberry hosts"""

	# getting config
	[hosts_list,usernames,passwords,anchors_names,anchors_table] = read_config(config)
	nb_anchors = len(anchors_names)

	# cleaning previous local hex files
	clean()

	# compiling main file, generating an hex file with unique ID for each anchor
	compilation(nb_anchors)
	for host in hosts_list:
		# flushing previous hex files
		local_clean(host, usernames[host],passwords[host])



	for host in hosts_list:

		for anchor in anchors_table[host]:
			filename = "anchor" + anchor + ".hex"
			destination = usernames[host] + "@" + host
			path = HOSTPATH
			pwd = passwords[host]
			send_hex_file(filename, destination,pwd,path)


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
			print("flashing anchor " + anchor + "..." )
			(stdin, stdout, stderr) = ssh.exec_command('nohup /home/pi/Desktop/teensy_loader_cli -mmcu=mk20dx256 -s -v ' + '/home/pi/Desktop/anchor' + anchor + '.hex')
			stdout.channel.recv_exit_status()


			for line in stdout.readlines():
				print(line)
			print("flashed !")

def local_clean(hostname,username,password):
	"""cleans the local hex files on the target hostname"""
	#starting ssh client

	#with paramiko.SSHClient() as ssh:
	#ssh.connect(hostname,username = username,password = password)
	ssh = paramiko.SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	print(hostname,username,password)
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
		print(anchors_list)
		print(host)
		print(usernames[host])
		print(passwords[host])

		# flashing the anchors given in the config file

		local_flash(host, usernames[host],passwords[host],anchors_list)











if __name__ == "__main__":


	#


	#send_hex_file('anchorA.hex','pi@Rasp1','raspberry',HOSTPATH)
	#local_flash('Rasp1','pi','raspberry',['A'])

	#global_clean('config.txt')


	if len(sys.argv) == 1:
		# Default behaviour: flashing remotely all the anchors
		deploy_hex_files('config.txt')
		global_flash('config.txt')
	else:
		if (sys.argv[-1] == "-clean"):
			clean()
		# compiling only 1 file
		compilation(1)


    #clean()
    #compilation(1)
