"""****************************************************************************
Copyright (C) 2017-2020 LCIS Laboratory - Baptiste Pestourie

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

@file read_mes.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Extracts and process measurement from a given json log
@see https://github.com/Hedwyn/SecureLoc
"""
## subpackages
from ips.localization.filter import Filter
from ips.logs.json_logs import jsonLogs
from ips.core.parameters import *

## other libraries
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import sys
import numpy as np




ANCHOR_NAME = 'A'
anchors_pos = {'A':(0,0,0),
               'B':(0,16,0),
               'C':(6,16,0),
               'D':(6,0,0)
              }

LOGSFILE = "measurements/logs20.txt"
SQUARE_SIZE = 0.304
ALL_IN_ONE = True
CORRECTION = True
FILTER_ON = False
THRESHOLD = 0
THOLD_ON = False
DISPLAY = True
TABFILE = "res.txt"

class Measurements:
    
    def __init__(self,filename):
        self.filename = filename
        self.log = None
        
        # reading metadata
        meta = self.get_metadata()
        if "anchors_position" in meta:
            self.anchors_pos = meta["anchors_positions"]
            print('error : empty metadata')
        if "comments" in meta:
            self.comments = meta["comments"]
    
    def get_metadata(self):
        """reads and returns as a dic the metadata in the measurements file"""
        self.log = jsonLogs()
        log_filename = JSON_DIR + '/' + MEASUREMENTS_REPO + '/' + self.filename
        
        # keeping the first metadata read in the file
        # TODO : handling metadata changes during experiment ?
        meta = self.log.read_metadata(log_filename)
        return(meta[0])
        
        
    
    
    def read_mes(self,mode = 'POS'):
        """reads the target json file and returns the reference points 
        and the rangings series for each of them"""
        
    
        new_rp = False
        end_of_serie = True
        ref_points = []
        output = []
        serie = []
       
        logs_data = self.log.read()
        
        
        for json in logs_data:
            target_anchor = json['anchor']
            distance = json['distance']
       
        for line in logs_data:
            values = line.split()
            if ( (len(values) == 0) and new_rp):
                # empty line after a new RP
                new_rp = False
                
            elif(len(values) == 0):
                # empty line after the end of a measurements serie
                end_of_serie = True
    
                # adding the last serie of measurements to rangings list
                # resetting serie
                
                
            elif(end_of_serie):
                # reference point
                end_of_serie = False
                new_rp = True
                if (serie != [] ):
                # serie is empty at the first iteration
                    output.append(serie)
                    
                #print("serie :" + str(serie) )
                serie = []
    
    
                rp = (float(values[0]), float(values[1]), float(values[2]))
                
                ref_points.append(rp)
            else:
                # ranging value within a serie
    
                if (mode == 'POS'):
                    pos = (float(values[0]), float(values[1]), float(values[2]))
                    serie.append(pos)
                if (mode == 'RANGING'):
                    rangings = ( float(values[0]), float(values[1]), float(values[2]), float(values[3]) )
                    serie.append(rangings)
                
    
        # appending last serie if completed
    ##    if (len(serie) == len( output[0] ) ):
    ##        output.append(serie)
    ##    else:
    ##        ref_points.pop(len(ref_points) - 1)
    ##        #print(serie)
        output.append(serie)
    
        logs.close()
    
        return( (ref_points, output) )
    
    
    def get_anchors(self):
        """gets the anchors names & positions from metadata"""
        self.anchors_dic = {}
        meta = self.get_metadata()
        lines = meta.split("|")
        for line in lines:
            data=  line.split()
            anchor_name = data[0]
            # appending anchor in dictionary with its coordinates 
            self.anchors_dic[anchor_name] = (data[1], data[2], data[3])
        
    
    def ranging_from_rp(self,rp, anchor_name):
        """returns the distance between the given anchor and the given rp"""

        (a,b,c) = self.anchors_dic[anchor_name]
        (x,y,z) = rp
        X = (x - a) * SQUARE_SIZE
        Y = (y - b) * SQUARE_SIZE
        Z = (z - c) * SQUARE_SIZE
        
        distance = math.sqrt( pow(X,2) + pow(Y,2) + pow(Z,2) )
        return(distance)
    
    def ranging_from_pos(self,pos,anchor_name):
        """returns the distance between the given position and the given anchor"""
        (a,b,c) = self.anchors_dic[anchor_name]
        (x,y,z) = pos
        X = x - (a * SQUARE_SIZE )
        Y = y - (b * SQUARE_SIZE )
        Z = z - (c * SQUARE_SIZE)
    
        distance = math.sqrt( pow(X,2) + pow(Y,2) + pow(Z,2) )
        return(distance)
        
        
    
    
    def distance_from_rp(self,rp,pos):
        """returns the distance between the given position & the given rp"""
        (a,b,c) = rp
        xp =  a * SQUARE_SIZE
        yp =  b * SQUARE_SIZE
        zp =  c * SQUARE_SIZE
        (x,y,z) = pos
    
        dX = x - xp
        dY = y - yp
        dZ = z - zp
    
        distance = math.sqrt( pow(dX,2) + pow(dY,2) + pow(dZ,2) )
        return(distance)
    
    def get_coord(self,x,y,z):
        """returns the coordinates associated to the given pos on a tiled surface"""
        a = 0
        b = 0
        c = 0
    
        distance = 0
    
        while (distance <= x):
            distance += SQUARE_SIZE
            if ( (x - distance) > - (SQUARE_SIZE / 2) ):
                a += 1
        distance = 0
    
        while (distance <= y):
            distance += SQUARE_SIZE
            if ( (y - distance) > - (SQUARE_SIZE / 2) ):
                b += 1
        distance = 0
    
        while (distance <= z):
            distance += SQUARE_SIZE
            if ( (z - distance) > - (SQUARE_SIZE / 2) ):
                c += 1
        distance = 0
    
        return(a,b,c)
    
           
        
        
    
    def filter_rp(self,rp_list,rangings, threshold = THRESHOLD):
        """returns a list of rp excluding the ones too far away"""
        rp_out = []
        rangings_out = []
        rangings_copy = rangings
        for rp in rp_list:
            ranging = rangings_copy.pop(0)
            if ( ranging_from_rp(rp,ANCHOR_NAME) > THRESHOLD):
                rp_out.append(rp)
                rangings_out.append(ranging)
        return(rp_out,rangings_out)
    
    
    def extract_serie(self,serie,rp):
        """extracts the series of ranging from the log file"""
    
        # output data
        
     
        (a,b,c) = rp
        mean_accuracy = 0
        measured_x = 0
        measured_y = 0
        measured_z = 0
        std = 0
    
        xp =  a * SQUARE_SIZE
        yp =  b * SQUARE_SIZE
        zp =  c * SQUARE_SIZE
    
        real_position = (xp,yp,zp)
        
        
    
        for pos in serie:
            (x,y,z) = pos
           
    
            measured_x += x
            measured_y += y
            measured_z += z
            
               
    
            # calculating distance to ref point
            distance = self.distance_from_rp(pos,rp)
          
            
            
        mean_position = ( measured_x / len(serie), measured_y / len(serie), measured_z / len(serie) )
        mean_accuracy += self.distance_from_rp(rp,mean_position)
    
        return(real_position,mean_position,mean_accuracy)
    
    def extract_serie_rangings(self,serie,rp):
        """returns the mean ranging values from a serie of rangings"""
        mean_ra = 0
        mean_rb = 0
        mean_rc = 0
        mean_rd = 0
        means = [0,0,0,0]
        
        
        for ranging_list in serie:
            [Ra,Rb,Rc,Rd] = ranging_list
            for (i,ranging) in enumerate(ranging_list):
                means[i] += ranging
    
        for mean in means:
            mean = mean / len(ranging_list)
    
        return(means)
            
            
            
            
                
        
        
    def get_ranging_error(self,anchor_name,pos,rp,ranging = None):
        """computes the ranging error for the given rp"""
    
        # getting actual ranging value for anchor_name
    
        real_ranging = ranging_from_rp(rp, anchor_name)
    
        # getting measured ranging value from rp
    
        if (ranging == None):
    
            measured_ranging = ranging_from_pos(pos,anchor_name)
    
        else:
            measured_ranging = ranging
            
        
    
        abs_error = abs(real_ranging - measured_ranging)
    
        if (real_ranging > 0):
            rel_error = abs_error / real_ranging
        else:
            rel_error = 0
    
        return(abs_error,rel_error)
        
        
    
    
         
            
    
    def display(self,anchor_name = ANCHOR_NAME ,mode = '2D'):
        """displays the results using matplotlib"""
        res = self.read_mes()
        
    
    
    
        ref_points = res[0]
        positions = res[1]
    
    
    
        # print(ref_points)
        # print(rangings)
        out = [] # will be returned
        measured_positions = [] # measured ranging value for the reference point
        real_positions = [] # real ranging value for the reference point
        
        #abs_standard_deviation = []
        #relative_standard_deviation = []
    
        abs_accuracies = []
        #relative_accuracies = []
    
        #angles = angle(ref_points,anchor_name)
        
        for (i,rp) in enumerate(ref_points):
            serie = positions[i]
            
            (real_position,mean_position,mean_accuracy) = self.extract_serie(serie,rp)
    
            # getting error for anchor A
            #print(get_ranging_error('A',mean_position,rp) )
            measured_positions.append(mean_position)
            real_positions.append(real_position)
            abs_accuracies.append(mean_accuracy)
    
        global_accuracy = np.mean(abs_accuracies)
        print("average accuracy :" + str(global_accuracy) )
    
    
    
    
        # displaying averaged values
    
    
        
       
            
    
        measured_x = []
        measured_y = []
        measured_z = []
        real_x = []
        real_y = []
        real_z = []
        for pos in measured_positions:
            (x,y,z) = pos
            measured_x.append(x)
            measured_y.append(y)
            measured_z.append(z)
            
        for pos in real_positions:
            (x,y,z) = pos
            real_x.append(x)
            real_y.append(y)
            real_z.append(z)
        
    
            
    
            
            
    
        if (mode == '2D'):
    
    
     
            # plotting results
    
            # creating figures 
            fig1 = plt.figure("Accuracy")
            fig2 = plt.figure("Positions") 
    
            # creating axes 
            ax1 = fig1.add_subplot(111,projection='3d')
            ax1.view_init(elev = 45, azim = 240)
            ax1.set_title("absolute accuracy")
            ax1.plot(real_x[:],real_y[:],abs_accuracies[:])
    
            
    
    
            
            ax2 = fig2.add_subplot(111)
            ax2.set_title("Real positions")
            ax2.scatter(real_x[:],real_y[:])
    
            ax2 = fig2.add_subplot(111)
            ax2.set_title("Measured positions")
            ax2.scatter(measured_x[:],measured_y[:])
    
            
    
    
    
            
            
        if (mode == '3D'):
            # plotting results
    
            # creating figures 
            fig1 = plt.figure("Accuracy")
            fig2 = plt.figure("Positions") 
    
            # creating axes 
            ax1 = fig1.add_subplot(111,projection='3d')
            ax1.view_init(elev = 45, azim = 240)
            ax1.set_title("absolute accuracy")
            ax1.plot(real_x[:],real_y[:],abs_accuracies[:])
    
            
    
    
            
            ax2 = fig2.add_subplot(111,projection='3d')
            ax2.view_init(elev = 45, azim = 240)
            ax2.set_title("Real positions")
            ax2.scatter(real_x[:],real_y[:],real_z[:])
    
            ax2 = fig2.add_subplot(111,projection='3d')
            ax2.view_init(elev = 45, azim = 240)
            ax2.set_title("Measured positions")
            ax2.scatter(measured_x[:],measured_y[:],measured_z[:])
    
    
            
        if (DISPLAY):    
            plt.show()
    
    
        return(out)
    
    
            
                
                
    def get_results(self,start_idx,stop_idx):
        """writes the results for the logs between start_id and stop_idx
        in a tab file"""
    
        label = ["ACC","REL ACC"," A * x + B","SD","REL SD", "FINAL ACC"]
        
        # disabling results display
        
        global DISPLAY
        DISPLAY = False
    
        # creating tab file to write results
        tab = open(TABFILE,'w+')
        for idx in range(start_idx,stop_idx + 1):
            res = "measurements/logs" + str(idx) + ".txt"
            print("results from log " + str(idx) + " : ")
            out = display(anchor_name = 'C',logsfile = res,mode = None, directive = None)
            for (i,data) in enumerate(out):
                print( label[i] )
                print(data)
                if (label[i] == " A * x + B"):
                    str_data = "y = " + str( round(data[0],3) ) + "x" + " + " + str( round(data[1],3) )
                elif(label[i] == "REL ACC"):
                    
                    str_data = str(round(data, 3))
                    
                else:
                    # converting to cm or %
                    str_data = str(round(100 * data, 1)  )
                    
                tab.write(str(str_data) + ",")
            tab.write("\n")
    
            
    

    
       
       
       
        
        

if __name__ == "__main__":
    #res = read_mes("measurements/logs12.txt")
#    if (len(sys.argv) > 2):
#        logsfile = "measurements/playback/logs" + sys.argv[1] +".txt"
#    else:
#        logsfile  = "measurements/logs" + sys.argv[1] +".txt"
    mes = Measurements("2018-10-12__11h04m37s.json")
    mes.display('A','2D')
    #print(get_coord(1.9,3.15,0) )
    
    
    
    
    
            
            
