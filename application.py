from direct.showbase.ShowBase import ShowBase
from direct.filter.CommonFilters import CommonFilters
from panda3d.core import *
import keyboard
import time
import socket
import pickle
import math
import os
from datetime import datetime
from parameters import *
from Menu import Menu
from world import World
from anchor import Anchor
from movingentity import MovingEntity
from Filter import Filter
from sound import Melody
from jsonLogs import jsonLogs
from time import gmtime,strftime,localtime
import paho.mqtt.client as mqtt
import json
import glob
from multiprocessing import Process, Pipe
from jsonStructures import dataset,position,metadata
import numpy as np
import sympy as sp






class Application(ShowBase):
    """Main application class"""
    def __init__(self):
        ShowBase.__init__(self)
        self.robots = {}
        
        self.logs_pipe = [] # list for the children connexions of the logs pipes
        self.anchors = []
        self.pos_array = None
        self.rangings = {}
        self.ranging_counter = {} # used to iterate through the ranging list in playback mode
        self.mes_counter = 0
        self.ref_points = []
        self.rp = 0
        self.pipe = {} # pipes dictionary 
        self.init_render()
        self.filters = {}
        #self.menu = Menu()
        self.menu = Menu()
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
                print(playback_file)
               
               
                
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
                print(playback_dir)
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
        
          
        if not(PLAYBACK):
            self.init_mqtt()
            taskMgr.doMethodLater(0,self.update_positions_task,'update sock')
        # initializing logs
        self.init_logs()

        

        # in playback mode, prepares the iteration through the ranging lists
        if (PLAYBACK):
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
      

     
        
      
    
    def init_render(self):
        """Initialize the renderer's properties"""
        self.win_props = WindowProperties.get_default()
        self.win_props.set_fullscreen(False)
        self.win_props.set_fixed_size(True)
        self.win_props.set_size(640, 480)
        self.win_props.set_title("SecureLoC")
        base.win.request_properties(self.win_props)

        render.set_shader_auto()
        render.set_antialias(AntialiasAttrib.MAuto)
        """Set the overview parameters"""
        base.cam.set_pos(5, 9, 3)
        base.cam.look_at(0, 0, 0)

    def create_world(self):
        """Creates the 3D world in which entities will evolve"""
        self.anchors = []
        if PLAYBACK:
            tabfile = 'anchors_playback.tab'
        else:
            tabfile = 'anchors.tab'
        with open(tabfile) as anchors_file:
            for line in anchors_file:
                data = line.strip().split()
                if len(data) != 5:
                    d_print('did not understood line "{}"'.format(line.strip()))
                    continue
                (x,y,z) = (float(data[0]),float(data[1]),float(data[2]))
                name = data[3]
                
                color = data[4]
              
                self.anchors.append( Anchor(x,y,z,name,color) )
       # creating the graphic world in the 3D engine. First 2 args define the size
        self.world = World(8, 8, self.anchors)


            

    def create_moving_entities(self):
        """Create moving entities"""
        v_print("creating moving entities \n:")
        #bots_id = self.world.gen_bots_id(NB_BOTS)
        for i in range(NB_BOTS):
            colors = ['blue','orange']
            self.robots[ bots_id[i] ]  = MovingEntity( bots_id[i], colors[i] )
        self.processed_robot = bots_id[0]


    def init_mqtt(self):
        """creates the mqtt client and handles the subscriptions"""
        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message
        
        # connecting to local host
        self.mqttc.connect("127.0.0.1", 1883, 60)

        
        for label_a in anchors_labels:
            for label_b in bots_labels:
           
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/distance")           
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/ts1")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/ts2")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/ts3")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/ts4")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/rssi")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/fp_power")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/fp_ampl2")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/std_noise")
                self.mqttc.subscribe(ROOT + label_a + "/"  + label_b + "/temperature")
                print(ROOT + label_a + "/"  + label_b + "/temperature")
        self.mqttc.loop_start()
        print("MQTT loop succesfully started !")


    def on_message(self,mqttc,obj,msg):
        """handles data resfreshing when a mqtt message is received"""

        d_print("MQTT frame received !")
        
        labels = msg.topic.split("/")
        anchor_id = labels[2]
        bot_id = name_to_id(labels[3])
        anchor_name = id_to_name(anchor_id)
        data_type = labels[4]
        
        # one dataset for each anchor/bot combination
        
        if not (anchor_id in self.dataset):
            self.dataset[anchor_id] = {}
        
        if not (bot_id in self.dataset[anchor_id]):
            # creating an empty dataset
            self.dataset[anchor_id][bot_id] = dataset()
        
        
        
        if (data_type == "distance"):
            # publishing the dataset
            if self.log_flag:
                self.log_dataset(self.dataset[anchor_id][bot_id])
            # resetting the dataset
            self.dataset[anchor_id][bot_id].__init__()
            
            
            distance = float(msg.payload)
            d_print('distance received:' + str(distance))
            if MEASURING and (self.rp < len(self.ref_points)):
                # adding the current reference point into the dataset
                self.dataset[anchor_id][bot_id].rp = self.ref_points[self.rp]
            self.dataset[anchor_id][bot_id].distance = distance
            self.dataset[anchor_id][bot_id].anchorID = anchor_id
            self.dataset[anchor_id][bot_id].botID = bot_id

            self.processed_robot = bot_id
            self.world.update_anchor(anchor_name, distance,bot_id,'SW')
            #task = taskMgr.doMethodLater(0,self.update_positions_task,'Log Reading')
            taskMgr.doMethodLater(0,self.update_sock_task,'update sock')
        
        if (data_type == "rssi"):
            rssi = float(msg.payload)
            d_print('rssi received:' + str(rssi))

            self.dataset[anchor_id][bot_id].rssi = rssi
                
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
            self.pipe['mqtt'] = q_mqtt
            meta = metadata()
            self.log_dataset(meta)
        
        
        # initializing pos data logs
        if (PLAYBACK):
            # directory name is the playback log name without .json estension
            
            repo = self.playback_path
            print("pos repo: "+ repo)
            
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
        self.pipe['pos'] = q_pos
        
        
        
        

        
    def log_dataset(self,dataset):
        """writes the last dataset received in logs file"""
        # sending dataset to logging process
        if ('mqtt' in self.pipe):
            self.pipe['mqtt'].send(dataset.export())
            
    def log_pos(self, pos):
        """writes the id of the robot and its last pos recorded in logs file"""
        # sending dataset to logging process
        if ('pos' in self.pipe):
              
            self.pipe['pos'].send(pos.export())        
            

       
  



                
    def checkInputs(self):
        """ manages user keyboard interaction """
        inputs = []

        if (keyboard.is_pressed('q') ):
            inputs.append('q')
        elif (keyboard.is_pressed('w') ):
            inputs.append('sw')
        elif keyboard.is_pressed('UP'):
            inputs.append('UP')
        elif keyboard.is_pressed('DOWN'):
            inputs.append('DOWN')
        elif keyboard.is_pressed('LEFT'):
            inputs.append('LEFT')
        elif keyboard.is_pressed('RIGHT'):
            inputs.append('RIGHT')
        elif keyboard.is_pressed('d'):
            inputs.append('d')
        elif keyboard.is_pressed('c'):
            inputs.append('c')

        return(inputs)

    def update_positions_task(self,task):        
        """Updates moving entities positions"""
        # increments positions updates counter
        # is triggered by update_sock_task when new data is sent into the socket
        filter_type = 'SW'
          
        robotname = self.processed_robot
        if robotname in self.robots:
            robot = self.robots[robotname]
        else:
            # quits the task if invalid robot id is received
            print("invalid robot id has been received: " + str(robotname))
            self.playback_counter += 1
            data = self.playback_rangings[self.playback_counter] 
            self.processed_robot = data['botID']
            return(0)
        
        # computes multilateration to localize the robot
        self.world.get_target(self.robots[robotname])
        
        if (PLAYBACK):
            # reading  data for playback
            for i in range(len(self.anchors)):
                if (self.playback_counter >= len(self.playback_rangings)):
                    # quitting
                    print("playback file finished !")
                
   
                    self.done = True
                    return(task.done)
                data = self.playback_rangings[self.playback_counter] 
                self.world.update_anchor(id_to_name(data['anchorID']), 
                                         data['distance'],
                                         data['botID'],
                                         'SAT')
                self.processed_robot = data['botID']
                
             
    
                self.playback_counter += 1
                
                
         
        (pos,mse,anchors_mse) = self.world.localize(robotname)
        self.menu.update_mse(mse)
       
       

        # applying saturation filter
        robot.set_pos(pos)
        robot.compute_speed()
        robot.compute_acc()
        

        if (filter_type == 'SAT'):
            
            pre_pos = robot.get_pre_pos()
            
            if not('SAT' in self.filters):
                self.filters['SAT'] = Filter('SAT')

            
            
            filtered_pos = self.filters['SAT'].apply( [pre_pos, pos, robot.get_speed_vector(), robot.get_abs_acc(), STEP] )[0]
            # replaces the raw values with the filtered results
            robot.set_pos(filtered_pos,replace_last = True)
            robot.compute_speed(replace_mode = True)
            robot.compute_acc(replace_mode = True)
        
          

        robot.display_pos()

        # writing position in logs

        
        pos = robot.get_pos()
        (x,y,z) = pos
        self.log_pos(position(robotname,x,y,z,mse,anchors_mse))
        



        # computes the robot speed based on position variation
        robot.compute_speed()

        # computes the robot acceleration based on speed variation
        robot.compute_acc()

          
            
        if not robot.shown:
            robot.show()


        if self.exit_flag or PLAYBACK:
            return(task.done)
        else:
            task.delayTime = 0.33
            return(task.again)


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
        
        

        ##  managing user inputs
        
        pressed_keys = self.checkInputs()
        if self.done:
            # adding quit input if measuring protocol is over
            pressed_keys.append('q')
        for key in pressed_keys:

            if (key == 'q'):
                # quit command
                self.exit_flag = True
                

                    
                # sending termination signal to logging thread
                print("closing logs & pipes...")
                for key in self.pipe:  
                    self.pipe[key].send('stop')
                    self.pipe[key].close()

                
                print('done !')
                self.pipe = {}
                if not(PLAYBACK):
                    self.mqttc.loop_stop()

                self.menu.callback()
                print("returning...")
                return(task.done)

           
            if (key == 'sw'):
                # enables sliding windows
                filter_type = 'SW'
            if key == 'UP':
                base.cam.set_pos(base.cam.getX() - 0.1, base.cam.getY() - 0.1, base.cam.getZ())
            if key == 'DOWN':
                base.cam.set_pos(base.cam.getX() + 0.1, base.cam.getY() + 0.1, base.cam.getZ())
            if key == 'LEFT':
                base.cam.setPos(base.cam.getX() + 0.1, base.cam.getY() - 0.1, base.cam.getZ())
            if key == 'RIGHT':
                base.cam.setPos(base.cam.getX() - 0.1 , base.cam.getY() + 0.1, base.cam.getZ())
            if key == 'd':
                base.cam.setPos(base.cam.getX(), base.cam.getY() + 0.1, base.cam.getZ()+ 0.1)
            if key == 'c':
                base.cam.setPos(base.cam.getX() , base.cam.getY() + 0.1, base.cam.getZ() - 0.1)

        if not(MEASURING): 
            if (PLAYBACK):
                taskMgr.doMethodLater(0,self.update_positions_task,'update positions')
                task.delayTime = REFRESH_TIME / self.menu.getAccel()
                return(task.again)
            else:
                #taskMgr.doMethodLater(0,self.update_positions_task,'update positions')
                return(task.done)
    

       
        else:

            if (self.mes_counter == 0):
                Melody(start_score).start()

                
                if (self.rp > len(self.ref_points) - 1):
                    #self.logs.close()
                    self.done = True
                    print("done !")
                    return(task.done)
                (rp_x, rp_y, rp_z) = self.ref_points[self.rp]
                v_print("New reference point: " + str( (rp_x,rp_y,rp_z) ) )

                # displaying ref point pos
                if (self.rp == len(self.ref_points) ):
                    return(task.done)
                
                rp = self.ref_points[self.rp]
                (rp_x,rp_y,rp_z) = rp
                pos_x = float(rp_x) * SQUARE_SIZE
                pos_y = float(rp_y) * SQUARE_SIZE
                pos_z = float(rp_z) * SQUARE_SIZE
                pos = (pos_x,pos_y,pos_z)
                

                
                
                #self.logs.write(str(rp_x) + " " + str(rp_y) + " " + str(rp_z) + "\n\n")
                #self.logs_rangings.write(str(rp_x) + " " + str(rp_y) + " " + str(rp_z) + "\n\n")
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
                
                

                

            
                
            #self.update_positions_task(task)
        
       
        # FPS will be dependant of 1/delayTime. Choose a value close to the delay between rangings
       

        
        return (task.done)


            
