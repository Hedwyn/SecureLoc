"""****************************************************************************
Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, in version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************

@file application.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Application class - handles the localization engine scheduling and main operations
@see https://github.com/Hedwyn/SecureLoc
"""

import keyboard
import time
import socket
import pickle
import math
import os
import sys
from datetime import datetime
from parameters import *
from Menu import Menu
from world import World
from Simulation import Simulator
from anchor import Anchor
from movingentity import MovingEntity
from Filter import Filter
if MEASURING:
    from sound import Melody
from jsonLogs import jsonLogs
from time import gmtime,strftime,localtime
import paho.mqtt.client as mqtt
import json
import glob
from multiprocessing import Process, Pipe
from jsonStructures import dataset,position,metadata
from RenderingInterface import Renderer
if (HEADLESS):
    from RenderingInterface import taskMgr # TODO
import numpy as np
import sympy as sp


class Application(Renderer):
    """Main application class"""
    def __init__(self, menu = None):

        self.tags = {}

        self.logs_pipe = [] # list for the children connexions of the logs pipes
        self.anchors = []
        self.pos_array = None
        self.rangings = {}
        self.ranging_counter = {} # used to iterate through the ranging list in playback mode
        self.mes_counter = 0
        self.ref_points = []
        self.rp = 0
        self.threads_pipe = {} # pipes dictionary
        self.init_render()
        self.filters = {}



        ## Simulation layer config
        self.simulator = Simulator()
        self.simulator.configure_attacks()
        self.keep_dataset = True

        ## menu configuration
        if menu:
            self.menu = menu
        else:
            self.menu = Menu()
            self.menu.setDaemon(True)
            self.menu.start()

        p,q = Pipe()
        self.menu.application_pipe = p
        self.menu_pipe = q
        self.menu.attack_list = [attack_name for attack_name in self.simulator.attacks]


        ## logs config
        self.dataset = {}
        #self.dataset = dataset()
        self.log_flag = True
        self.exit_flag = False

        # notifies that process should end
        self.done = False

        # for PLAYBACK only
        self.log2play = None

        self.playback_path = None
        self.playback_rangings =  None
        self.playback_counter = 0

        # mqtt
        self.mqttc = None
        # logs for positions
        self.logs_mqtt = None
        self.logs_pos = None

        # logs for rangings
        self.logs_rangings = None
        if (PLAYBACK):
            try:
                self.log2play = jsonLogs()
                list_of_files = glob.glob(PLAYBACK_DIR + '/*.json')
                playback_file = max(list_of_files, key=os.path.getctime)
                print("Replaying " + playback_file)



                self.playback_rangings = self.log2play.read(playback_file)

                # getting anchors position
                metadata = self.log2play.read_metadata()

                # parsing anchors positions
                with open("anchors_playback.tab",'w+') as f:
                    lines = metadata[0]["anchors_positions"].split('|')
                    for line in lines:
                        f.write(line)
                        f.write("\n")

                # anchors_playback.tab will be read by create_world
                taskMgr.doMethodLater(0,self.update_sock_task,'update sock')


                # creating directory for pos logs if there isn't already one
                # cutting json extension in the filename
                self.playback_path = PLAYBACK_REPO + '/' + playback_file.split('\\')[-1][:-5] # to be modified on Linux environment
                playback_dir = JSON_DIR + '/' + self.playback_path

                if not ( os.path.exists(playback_dir) ):
                    try:
                        os.mkdir(playback_dir)
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            raise

            except IOError:
                print("failed to read playback log file")


        # now creating the world in the 3D engine
        d_print("creating world...")
        self.create_world()

        d_print(" world created ...")
        self.create_moving_entities()
        d_print(" robots created ...")

        ## adding tags and anchors to the menu
        self.menu.anchors_list = [anchor.name for anchor in self.world.anchors]
        self.menu.tags_list = [tagID[13:16] for tagID in self.tags]
        self.menu.generate_attacks_panel()
        ## ready to start main loop
        # initializing logs
        self.init_logs()

        if not(PLAYBACK) or (EMULATE_MQTT):
            self.init_mqtt()
            if not (EMULATE_MQTT) and not(MEASURING):
                taskMgr.doMethodLater(REFRESH_PERIOD,self.update_positions_task,'update sock')

        # in playback mode, prepares the iteration through the ranging lists
        if (PLAYBACK):
            print("Anchors IDs:")
            for anchor in self.world.anchors:
                print(anchor.name)
                self.ranging_counter[anchor.name] = 0


        # in measurement mode, reads the reference points file
        if (MEASURING):
            # reads the list of reference points in rp.tab
            self.get_rp()
            # gives the starting signal
            Melody(launch_score).start()
            time.sleep(START_DELAY)

        ## User inputs task
        taskMgr.doMethodLater(UI_REFRESH_TIME,self.UI_management_task,'User Inputs Management')

        # Security task
        taskMgr.doMethodLater(SECURITY_CHECK_PERIOD,self.Security_management_task,'Security Management')

    def UI_management_task(self, task):
        """Handles user inputs; refresh rate can be set in parameters"""
        task.delay = UI_REFRESH_TIME
        self.checkInputs()
        for verifier in self.tags:
            for tag in self.tags[verifier].cooperative_distances:
                distance = self.tags[verifier].get_cooperative_distance(tag)
                #print("[Cooperative verification] Distance verified by tag " + str(verifier) + " for tag"  + str(tag) + ": " + str(distance))

        ## handling menu pipe
        if self.menu_pipe.poll():
            inputs = self.menu_pipe.recv()
            #print("positions received" + str(inputs))

            ## inputs handler
            if "anchor_position" in inputs:
                self.add_anchor(inputs["anchor_position"])

            elif "tag_position" in inputs:
                self.add_tag(inputs["tag_position"])
                print("adding tag")
            elif "Attack" and "Target" and "Offset" in inputs:
                attack_type = inputs["Attack"]
                target = inputs["Target"]
                print("Appending attack " + attack_type + " to target " + target)
                self.simulator.attacks[attack_type].targets.append(target)
                # changing anchor color to red
                matching_anchors = [anchor for anchor in self.world.anchors if anchor.name == target]

                if matching_anchors:
                    anchor = matching_anchors.pop()
                    anchor.color = 'red'
                    print(anchor.color)
                    anchor.change_color('red')
                # setting up the offset of the attack
                try:
                    self.simulator.attacks[attack_type].offset = float(inputs["Offset"])
                except:
                    print("Provided offset value is not a float")
            elif "Freeze"  in inputs:
                if inputs["Freeze"]:
                    buffer = {}
                    print("Waiting input..;")
                    while not("Freeze" in buffer and not(buffer["Freeze"])):
                        buffer = self.menu_pipe.recv()
                        print(buffer)

        if self.exit_flag:
            # quit command
            # sending termination signal to logging thread
            print("closing menu...")
            print("closing logs & pipes...")
            for key in self.threads_pipe:
                self.threads_pipe[key].send('stop')
                self.threads_pipe[key].close()


            print('done !')
            self.threads_pipe = {}
            if not(PLAYBACK) and not(EMULATE_MQTT):
                self.mqttc.loop_stop()


            print("returning...")
            if not(HEADLESS):
                self.destroy()
                # letting some time to complete...
                time.sleep(0.2)
                sys.exit()
            return(task.done)


        return(task.again)


    def Security_management_task(self, task):
        """Handles user inputs; refresh rate can be set in parameters"""
        task.delay= SECURITY_CHECK_PERIOD
        
        for tag in [self.tags[id] for id in self.tags]:
            # checking differential TWR results
            rmse = tag.get_average_rmse()
            if rmse > RMSE_MALICIOUS:
                tag.decrease_trust_indicator(rmse - RMSE_MALICIOUS)
                tag.last_suspicious_event = 0
                print("differential alarm")
            else:
                tag.increase_trust_indicator()
                tag.last_suspicious_event += 1
        
            # checking cooperative results
            cooperative_deviation = tag.get_cooperative_deviation()
            if cooperative_deviation > COOPERATIVE_DEVIATION_THOLD:
                tag.decrease_trust_indicator(cooperative_deviation - COOPERATIVE_DEVIATION_THOLD)
                print("cooperative alarm: " + str(cooperative_deviation))
                tag.last_suspicious_event = 0 
            else:
                tag.increase_trust_indicator()
                tag.last_suspicious_event += 1

            # deciding if the tag is being attacked
            attack_detected =  (tag.trust_indicator < TI_THRESHOLD)                          
            if tag.is_attacked != attack_detected:
                tag.switch_attacked_state = True
                tag.is_attacked = attack_detected



        return(task.again)


    def add_anchor(self, anchor_pos):
        """adds an anchor to the current world. Should be used to create a fictive anchor"""
        # ID generation
        if PLAYBACK:
            print("Adding anchors is not supported in playback mode")
            return
        try:
            new_anchor_name = str(int(self.world.anchors[-1].name) + 1) # incrementing the IDof the last anchor by 1
        except:
            print("Failed to generate ID")
            return

        try:
            (x,y,z) = anchor_pos
        except:
            print("pos is not a proper tuple")
            return

        # generating a new Anchor
        new_anchor = Anchor(x, y, z, new_anchor_name, ANCHOR_COLOR)

        # appending anchors to the global anchors
        self.world.anchors.append(new_anchor)
        # appending anchor to fictive anchors list of simulator
        self.simulator.fictive_anchors.append(new_anchor)

        # displaying the new anchor
        self.world.anchors[-1].show()

        # suscribing to the MQTT stream of new anchor
        for label_b in bots_labels:
            for topic in MQTT_TOPICS:
                self.mqttc.subscribe(ROOT + '0' + new_anchor.name + "/"  + label_b + topic)
                # print("suscribing to")
                # print(ROOT + '0' + new_anchor.name + "/"  + label_b + topic)

    def add_tag(self, tag_pos):
        """adds an tag to the current world. Should be used to create a fictive tag"""
        # ID generation
        try:
            previous_tag_name = [tag_name for tag_name in self.tags][-1]
            new_tag_name = previous_tag_name[:-1] + str(int(previous_tag_name[-1]) +1)
            print("Tag ID: " + new_tag_name)
        except:
            print("Failed to generate ID")
            return

        try:
            (x,y,z) = tag_pos
        except:
            print("pos is not a proper tuple")
            return

        # generating a new tag
        new_tag = MovingEntity(new_tag_name, 'magenta')

        # appending tags to the global anchors
        self.tags[new_tag_name] = new_tag

        # appending tag to fictive anchors list of simulator
        self.simulator.fictive_tags.append(new_tag)

        # displaying the new tag
        new_tag.move(tag_pos)
        new_tag.show()

        # suscribing to the MQTT stream of new anchor
        # for label_a in anchors_labels:
        #     for topic in MQTT_TOPICS:
        #         self.mqttc.subscribe(ROOT + '0' + label_a + "/"  + label_b + topic)
        #         print("suscribing to")
        #         print(ROOT + '0' + new_anchor.name + "/"  + label_b + topic)


    def create_world(self):
        """Creates the 3D world in which entities will evolve"""
        self.anchors = []
        if PLAYBACK:
            tabfile = 'anchors_playback.tab'
        else:
            tabfile = 'anchors.tab'

        ## anchor creation
        with open(tabfile) as anchors_file:
            for line in anchors_file:
                if line and line[0] == '#':
                    continue
                data = line.strip().split()
                if len(data) != 5:
                    d_print('did not understood line "{}"'.format(line.strip()))
                    continue
                (x,y,z) = (float(data[0]),float(data[1]),float(data[2]))
                name = data[3]
                color = data[4]
                self.anchors.append(Anchor(x,y,z,name,color) )
       # creating the graphic world in the 3D engine. First 2 args define the size
        self.world = World(20, 20, self.anchors)

    def get_anchor_from_id(self, anchor_id):
        """Returns the reference to the anchor associated to the given id"""
        for anchor in self.anchors:
            if anchor.name == anchor_id[-1]:
                return(anchor)
        return(None)

    def create_moving_entities(self):
        """Create moving entities"""
        v_print("creating moving entities \n:")
        #bots_id = self.world.gen_bots_id(NB_BOTS)
        for i in range(NB_BOTS):           
            self.tags[ bots_id[i] ]  = MovingEntity( bots_id[i], TAG_COLOR)
        self.processed_robot = bots_id[0]


    def init_mqtt(self):
        """creates the mqtt client and handles the subscriptions"""
        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message

        # setting mqttc for the simulator
        self.simulator.mqttc = self.mqttc

        # connecting to local host
        self.mqttc.connect("127.0.0.1", 1883, 60)


        for label_a in anchors_labels:
            for label_b in bots_labels:
                for topic in MQTT_TOPICS:
                    self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + topic)

        if (ENABLE_COOPERATIVE):
            for label_b1 in bots_labels:
                for label_b2 in [tag for tag in bots_labels if tag != label_b1]:
                    for topic in MQTT_TOPICS:
                        self.mqttc.subscribe(COOPERATIVE_ROOT + label_b1 + "/"  + label_b2 + topic)
                        print(COOPERATIVE_ROOT + label_b1 + "/"  + label_b2 + topic)

        self.mqttc.loop_start()
        print("MQTT loop succesfully started !")


    def on_message(self,mqttc,obj,msg):
        """handles data resfreshing when a mqtt message is received"""

        d_print("MQTT frame received !")

        labels = msg.topic.split("/")
        anchor_id = labels[2]
        bot_id = tag_name_to_id(labels[3])
        anchor_name = anchor_id_to_name(anchor_id)
        data_type = labels[4]

        #print(labels[1])
        if (labels[1] == COOPERATIVE_STREAM):
            # appending B to indicate that the verifier was a tag
            anchor_id = 'B' + anchor_id
            cooperative = True
        else:
            cooperative = False


        # one dataset for each anchor/bot combination

        if not (anchor_id in self.dataset):
            self.dataset[anchor_id] = {}

        if not (bot_id in self.dataset[anchor_id]):
            # creating an empty dataset
            self.dataset[anchor_id][bot_id] = dataset()

        # indicating cooperative verification in the logs

        if cooperative:
              self.dataset[anchor_id][bot_id].protocol = 'cooperative' 


        if (data_type == "distance"):
            try:
                distance = float(msg.payload)
               
            except:
                distance = 0
            self.keep_dataset = True
            self.dataset[anchor_id][bot_id].distance = distance

            # simulating the attack if attack simulation is on
            for attack in self.simulator.attacks:
                if (anchor_id_to_name(anchor_id) in self.simulator.attacks[attack].targets) or (bot_id in self.simulator.attacks[attack].targets):
                    print("Anchor " + anchor_id + " targeted by the attack" + attack)
                    self.keep_dataset = self.simulator.attacks[attack].apply(self.dataset[anchor_id][bot_id])
                    print("distance after attack: " + str(self.dataset[anchor_id][bot_id].distance))

            # updating distance
            if not(cooperative):
                self.world.update_anchor(anchor_name, self.dataset[anchor_id][bot_id].distance,bot_id,'SW')
            else:
                verifier_id = tag_name_to_id(anchor_id[1:])
                self.tags[bot_id].add_cooperative_distance_sample(distance, verifier_id)

                # calculating deviation of the cooperative distance
                pos_verifier = self.tags[verifier_id].get_current_pos()
                pos_prover = self.tags[bot_id].get_current_pos()
                cooperative_deviation = self.world.get_distance(pos_verifier, pos_prover) - distance
                self.tags[bot_id].add_cooperative_deviation_sample(cooperative_deviation)
                

            # adding rmse           
            self.dataset[anchor_id][bot_id].differential_rmse = self.tags[bot_id].get_rmse(anchor_id) 

            # adding the position
            self.dataset[anchor_id][bot_id].localization_algorithm = self.world.get_localization_algorithm()
            self.dataset[anchor_id][bot_id].position = self.tags[bot_id].get_current_pos()

            # logging the dataset
            if self.log_flag and self.keep_dataset:
                self.log_dataset(self.dataset[anchor_id][bot_id])

            # resetting the dataset
            self.dataset[anchor_id][bot_id].__init__()



            if MEASURING and (self.rp < len(self.ref_points)):
                # adding the current reference point into the dataset
                self.dataset[anchor_id][bot_id].rp = self.ref_points[self.rp]
            self.dataset[anchor_id][bot_id].distance = distance
            self.dataset[anchor_id][bot_id].anchorID = anchor_id
            self.dataset[anchor_id][bot_id].botID = bot_id

            self.processed_robot = bot_id


            #task = taskMgr.doMethodLater(0,self.update_positions_task,'Log Reading')
            if not(PLAYBACK):
                taskMgr.doMethodLater(0,self.update_sock_task,'update sock')
  
        if (data_type == "differential_distance"):           
            try:
                differential_distance = float(msg.payload)
                #print("differential distance for anchor" + anchor_id[-1] + " and tag " + bot_id[-1] + " : " +  str(differential_distance))
                self.dataset[anchor_id][bot_id].distance = differential_distance
                self.dataset[anchor_id][bot_id].protocol = 'differential'

            

                # calculating rmse
                anchor = self.get_anchor_from_id(anchor_id)
                if anchor:
                    distance = anchor.get_distance(bot_id)
                    tag = self.tags[bot_id]
                    rmse = tag.compute_rmse(distance, differential_distance)
                    tag.add_rmse_sample(rmse, anchor_id)
                    # print("rmse for anchor " + anchor_id[-1] + " and tag " + bot_id[-1] + " : " +  str(tag.get_rmse(anchor_id)))
                    # print("average rmse" + str(tag.get_average_rmse()))
                    # logging rmse
                    self.dataset[anchor_id][bot_id].differential_rmse = tag.get_rmse(anchor_id) 

            except:
                pass
            self.log_dataset(self.dataset[anchor_id][bot_id])



        if (data_type == "rssi"):
            rssi = float(msg.payload)
            d_print('rssi received:' + str(rssi))

            self.dataset[anchor_id][bot_id].rssi = rssi

        if (data_type == "skew"):
            skew = float(msg.payload)
            d_print('skew received:' + str(skew))

            self.dataset[anchor_id][bot_id].skew = skew

        if (data_type[:-1] == "ts"):
            # timestamp
            ts = float(msg.payload)
            d_print(data_type + ' received:' + str(ts))

            self.dataset[anchor_id][bot_id].timestamps[data_type] = ts

        if (data_type == "fp_power"):
            fp_power = float(msg.payload)
            d_print('fp_power received:' + str(fp_power))

            self.dataset[anchor_id][bot_id].fp_power = fp_power


        if (data_type == "fp_ampl2"):
            fp_ampl2 = float(msg.payload)
            d_print('fp_ampl2 received:' + str(fp_ampl2))

            self.dataset[anchor_id][bot_id].fp_ampl2 = fp_ampl2

        if (data_type == "std_noise"):
            std_noise = float(msg.payload)
            d_print('std_noise received:' + str(std_noise))

            self.dataset[anchor_id][bot_id].std_noise = std_noise


        if (data_type == "temperature"):
            temperature = float(msg.payload)
            d_print('temperature received:' + str(temperature))

            self.dataset[anchor_id][bot_id].temperature = temperature
        d_print("MQTT frame processed !")

        last_physical_anchor_name = self.world.anchors[-(len(self.simulator.fictive_anchors) + 1)].name
        if (anchor_id == '0' + last_physical_anchor_name) and (bot_id in self.tags):
            self.simulation_layer(self.tags[bot_id])


    def init_logs(self):
        """initializes json logs with current date & time, and creates the
        pipe for loggin thread communication"""

        # quitting if logs aren't enabled
        if (ENABLE_LOGS == 0):
            return

        # initializing mqtt data logs
        if not(PLAYBACK):

            if (MEASURING):
                repo = MEASUREMENTS_REPO
            else:
                repo = MQTT_REPO
            # mqtt is off when playback mode is used
            self.logs_mqtt = jsonLogs(strftime("%Y-%m-%d__%Hh%Mm%Ss", localtime()),
                                 'SecureLoc Logs',
                                 'Nothing to comment',
                                 repo)
            p_mqtt,q_mqtt = Pipe()
            self.logs_mqtt.get_pipe(p_mqtt)
            # starting logging process. Logging process will be waiting for data..
            self.logs_mqtt.logging()
            # getting children pipe connexion
            self.threads_pipe['mqtt'] = q_mqtt
            meta = metadata()
            self.log_dataset(meta)


        # initializing pos data logs
        if (PLAYBACK):
            # directory name is the playback log name without .json estension

            repo = self.playback_path
            print("Logging position in directory: "+ repo)

        else:
            repo = POS_REPO

        self.logs_pos = jsonLogs(strftime("%Y-%m-%d__%Hh%Mm%Ss", gmtime()),
                             'SecureLoc Logs',
                             'Nothing to comment',
                             repo)
        p_pos,q_pos = Pipe()
        self.logs_pos.get_pipe(p_pos)
        # starting logging process. Logging process will be waiting for data..
        self.logs_pos.logging()
        # getting children pipe connexion
        self.threads_pipe['pos'] = q_pos






    def log_dataset(self,dataset):
        """writes the last dataset received in logs file"""
        # sending dataset to logging process
        if ('mqtt' in self.threads_pipe):
            self.threads_pipe['mqtt'].send(dataset.export())

    def log_pos(self, pos):
        """writes the id of the robot and its last pos recorded in logs file"""
        # sending dataset to logging process
        if ('pos' in self.threads_pipe):

            self.threads_pipe['pos'].send(pos.export())


    def checkInputs(self):
        """ manages user keyboard interaction """
        if (keyboard.is_pressed('q') ):
            self.done = True
            self.exit_flag = True
        elif keyboard.is_pressed('UP'):
            base.cam.set_pos(base.cam.getX() - 0.1, base.cam.getY() - 0.1, base.cam.getZ())
        elif keyboard.is_pressed('DOWN'):
            base.cam.set_pos(base.cam.getX() + 0.1, base.cam.getY() + 0.1, base.cam.getZ())
        elif keyboard.is_pressed('LEFT'):
            base.cam.setPos(base.cam.getX() + 0.1, base.cam.getY() - 0.1, base.cam.getZ())
        elif keyboard.is_pressed('RIGHT'):
            base.cam.setPos(base.cam.getX() - 0.1 , base.cam.getY() + 0.1, base.cam.getZ())
        elif keyboard.is_pressed('d'):
            base.cam.setPos(base.cam.getX(), base.cam.getY() + 0.1, base.cam.getZ()+ 0.1)
        elif keyboard.is_pressed('c'):
            base.cam.setPos(base.cam.getX() , base.cam.getY() + 0.1, base.cam.getZ() - 0.1)


    def update_positions_task(self, task):
        """Updates moving entities positions"""
        # increments positions updates counter
        # is triggered by update_sock_task when new data is sent into the socket
        filter_type = 'SW'

        robotname = self.processed_robot
        if robotname in self.tags:
            robot = self.tags[robotname]
        else:
            # quits the task if invalid robot id is received
            d_print("invalid robot id has been received: " + str(robotname))
            self.playback_counter += 1
            data = self.playback_rangings[self.playback_counter]
            self.processed_robot = data['botID']
            return(0)

        # computes multilateration to localize the robot
        try:
            self.world.get_target(self.tags[robotname])
        except:
            pass

        if (PLAYBACK):
            # reading  data for playback
            for i in range(len(self.anchors)):
                if (self.playback_counter >= len(self.playback_rangings)):
                    # quitting
                    print("playback file finished !")


                    self.done = True
                    return(task.done)
                data = self.playback_rangings[self.playback_counter]
                if data['protocol'] != 'differential':
                    if not(EMULATE_MQTT):
                        self.world.update_anchor(anchor_id_to_name(data['anchorID']),
                                                data['distance'],
                                                data['botID'],
                                                'SAT')
                    else: # emulating MQTT frames
                        self.simulator.send_log_as_MQTT_frame(data)
                        # last_physical_anchor_name = self.world.anchors[-(len(self.simulator.fictive_anchors) + 1)].name
                        # if (anchor_id_to_name(data['anchorID']) == last_physical_anchor_name) and (data['botID'] in self.tags):
                        #     self.simulation_layer(self.tags[data['botID']])




                    self.processed_robot = data['botID']
                self.playback_counter += 1



        (pos,mse,anchors_mse) = self.world.localize(robotname)
        self.menu.update_mse(mse)

        # moving the tag to its new position
        robot.move(pos)

        # computing tag speed and acceleration
        robot.compute_speed()
        robot.compute_acc()


        # writing position in logs
        pos = robot.get_position()
        (x,y,z) = pos
        self.log_pos(position(robotname,x,y,z,mse,anchors_mse))
        # computes the robot speed based on position variation
        robot.compute_speed()


        if not(PLAYBACK) and (TRANSMIT_POSITION):
            ## sending position to master anchor
            self.mqttc.publish(ROOT +  '01/' + TOPIC_SERIAL, '1' + robotname[-1] +';' + str(x)[:4] + ';' + str(y)[:4] + ';' + str(z)[:4] + '\n')
        
        # computes the robot acceleration based on speed variation
        robot.compute_acc()



        if not robot.shown:
            robot.show()


        if self.exit_flag or PLAYBACK:
            return(task.done)
        else:
            task.delayTime = REFRESH_PERIOD
            return(task.again)

    def simulation_layer(self, tag):
        """handles all the tasks related to the simulator"""
        # checking if the dataset if from the last (i.e. highest ID) physical anchor
        try:
            # simulating fictive anchors
            if tag:
                self.simulator.emulate_all_fictive_anchors(tag)
        except:
            print("Failed to simulate fictive anchors")

    def get_rp(self,tabfile = "rp.tab"):
        """For measurements mode only. Gets the reference points in the configuration file"""
        rp_file = open(tabfile)
        for line in rp_file:
            coord = line.split()
            self.ref_points.append(coord)

    def update_sock_task(self,task):
        """Asks server newest positions of entities"""
        """In playback mode the socket is bypassed and ranging resultd are obtained directly from the log file"""
        global ACCELERATION
        filter_type = 'SW' # uses the raw ranging values by default

        if self.done:
            # quitting if measuring protocol is over
            self.exit_flag = True




        if not(MEASURING):
            if (PLAYBACK):
                taskMgr.doMethodLater(0,self.update_positions_task,'update positions')
                task.delayTime = REFRESH_TIME / self.menu.getAccel()

                return(task.again)

            else:
                return(task.done)
        else: # measurements mode
            self.manage_measurements()

        return(task.done)

    def manage_measurements(self):
        """handles the pace of measurements. Measurements modes consist of series of measures separated by short rests.
        The duration can be set by the user"""
        if (self.mes_counter == 0):
            Melody(start_score).start()


            if (self.rp > len(self.ref_points) - 1):
                #self.logs.close()
                self.done = True
                print("done !")
                return
            (rp_x, rp_y, rp_z) = self.ref_points[self.rp]
            v_print("New reference point: " + str( (rp_x,rp_y,rp_z) ) )

            # displaying ref point pos
            if (self.rp == len(self.ref_points) ):
                return

            rp = self.ref_points[self.rp]
            (rp_x,rp_y,rp_z) = rp
            pos_x = float(rp_x) * SQUARE_SIZE
            pos_y = float(rp_y) * SQUARE_SIZE
            pos_z = float(rp_z) * SQUARE_SIZE
            pos = (pos_x,pos_y,pos_z)

            taskMgr.doMethodLater(0,self.update_positions_task,'update positions')
            self.mes_counter += 1


        elif (self.mes_counter < NB_MES):
            # measurement phase - recoding position into json log
            self.mes_counter += 1
            taskMgr.doMethodLater(0,self.update_positions_task,'update positions')
        elif (self.mes_counter == NB_MES):
            Melody(end_score).start()
            # disabling logging
            self.log_flag = False
            self.mes_counter += 1

        elif (self.mes_counter < NB_MES + NB_REST):
            # rest phase for robot displacement
            print("rest..")
            self.mes_counter += 1

        else:
            # mes_counter == NB_MES + NB_REST
            # resetting
            self.mes_counter = 0
            self.rp += 1
            # enabling logging
            self.log_flag = True
