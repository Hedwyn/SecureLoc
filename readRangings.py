import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import sys
from Filter import Filter
import numpy as np
from jsonStructures import *
from jsonLogs import *



class Rangings:
    
    def __init__(self,filename):
        self.filename = filename
        self.logs = None
        self.anchors_dic = None
        self.measured_distances = None
        
        # reading metadata
        meta = self.get_metadata()
        if "anchors_position" in meta:
            self.anchors_pos = meta["anchors_positions"]
            print('error : empty metadata')
        if "comments" in meta:
            self.comments = meta["comments"]
    
    def get_metadata(self):
        """reads and returns as a dic the metadata in the measurements file"""
        self.logs = jsonLogs()
        log_filename = JSON_DIR + '/' + MEASUREMENTS_REPO + '/' + self.filename
        
        # keeping the first metadata read in the file
        # TODO : handling metadata changes during experiment ?
        meta = self.logs.read_metadata(log_filename)
        return(meta[0])
        
        
    def get_measured_distances(self):
        data = self.logs.read()
        distances = {}
     
        for line in data:
            rp_coord = line['reference_point']
            #rp is given as a list. Converting to a tuple
            if (rp_coord != None) and (len(rp_coord) == 3): 
                rp = (rp_coord[0],rp_coord[1],rp_coord[2])
                if not(rp in distances):
                    distances[rp] = {}
                    for anchor in self.anchors_dic:
                        distances[rp][anchor] = []                        
                anchor = self.zero_truncating(line['anchorID'])
                distances[rp][anchor].append(line['distance'])   

                
        self.measured_distances = distances   
        #return(distances)
    
    
    def get_actual_distances(self):
        distances = {}
        for rp in self.measured_distances:
            for anchor in self.anchors_dic:
                if not(rp in distances):
                    distances[rp] =  {}
                distances[rp][anchor] = self.ranging_from_rp(rp,anchor)
                
                    
        self.actual_distances = distances
       
                
                
   

    def get_anchors(self):
        """gets the anchors names & positions from metadata"""
        self.anchors_dic = {}
        meta = self.get_metadata()
        print(meta)
        lines = meta["anchors_positions"].split('|')
        for line in lines:
           
            data =  line.split()
            if (len(data) >= 4):
                anchor_name = data[3]
                # appending anchor in dictionary with its coordinates 
                self.anchors_dic[anchor_name] = (data[0], data[1], data[2])
        print(self.anchors_dic)
        
    
    def zero_truncating(self,id):
        """removes '0' before the id if any"""
        if id[0] == '0':
            return(id[1:])
        else:
            return(id)
        
    
    def ranging_from_rp(self,rp, anchor_name):
        """returns the distance between the given anchor and the given rp"""
        

        

        (str_a,str_b,str_c) = self.anchors_dic[anchor_name]
        (str_x,str_y,str_z) = rp
        
        # converting string to float
        a = float(str_a)
        b= float(str_b)
        c = float(str_c)
        x = float(str_x)
        y= float(str_y)
        z = float(str_z)
        
        
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
        
    
    
    def get_mean(self,l):
        """returns the mean of a list"""
        sum = 0
        for x in l:
            sum += x
            
        return(sum / len(l) )
        
    def display_rangings(self,anchor):
        m_distances = []
        a_distances = []
        i = 0
        index = []
        for rp in self.measured_distances:
            if anchor in self.measured_distances[rp]:        
                serie = self.measured_distances[rp][anchor]
                for value in serie:
                    a_distances.append(self.actual_distances[rp][anchor])
                    m_distances.append(value)
                    index.append(i)
                    i+=1
            else:
                print('no trace of this anchor in the ranging records')
        
        # displaying figures

        fig1= plt.figure("Actual vs Measured distance")
        ax1= fig1.add_subplot(111)
        ax1.plot(index[:],a_distances[:])
        ax2 = fig1.add_subplot(111)
        ax2.plot(index[:],m_distances[:])
        plt.show()
        
        
            
            



if __name__=="__main__":
    # Testing
    rangings = Rangings('2018-11-20__14h49m11s.json')
    rangings.get_metadata()
    rangings.get_anchors()
    rangings.get_measured_distances()
    #print(rangings.measured_distances)
    rangings.get_actual_distances()
    print(rangings.actual_distances)
    rangings.display_rangings('1')
    