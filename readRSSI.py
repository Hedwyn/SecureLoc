import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import sys
from Filter import Filter
import numpy as np
from jsonLogs import jsonLogs
from jsonStructures import dataset,position,metadata
import os

RSSI_RES = 'rssi_results.txt'

class RSSI:
    
    def __init__(self,filename):
        self.filename = filename
        self.RSSI = {}
        self.log = jsonLogs()
        
        


    def extract_RSSI(self):
        json_data = self.log.read(self.filename)
        #print(json_data)
        
        for data in json_data:
            anchorID = data["anchorID"]
            botID = data["botID"]
            rssi = data["rssi"]
            if not(anchorID in self.RSSI) :
                
                self.RSSI[anchorID] = {}
            if not(botID in self.RSSI[anchorID]):
                self.RSSI[anchorID][botID] = []
            
            if (rssi != None):
                self.RSSI[anchorID][botID].append(rssi)
        
    
    def get_minmax(self,serie):
        min = 0
        max = -1000
        
        for rssi in serie:
        
            if (rssi < min):
                min = rssi
            if (rssi > max):
                max = rssi
                
        return(min,max)
        
    
    def get_mean(self,serie):
        
        mean = 0
        for rssi in serie:
            if (rssi != None):
                mean += rssi
            
        return(mean / len(serie) )
        
    
    def get_std(self,serie):
        
        std = 0
        mean = self.get_mean(serie)
        
        for rssi in serie:
            std += abs(rssi - mean)
        
        return(std/ len(serie) )
        
    
    def get_results(self,overwrite= 'w+'):
        
        with open(RSSI_RES,overwrite) as f:
            for anchor in mes.RSSI:
                for bot in mes.RSSI[anchor]:
                    serie = mes.RSSI[anchor][bot]
                    mean = self.get_mean(serie)
                    (min, max) = self.get_minmax(serie)
                    std = self.get_std(serie)
                    print("mean / std / min / max: \n" )
                    print(mean,std,min,max)
                    f.write("\n\nanchor: " + str(anchor) + " bot: " + str(bot) + "\n")
                    f.write("\nmean: " + str(mean) +
                            " \nstd: " + str(std) + 
                            " \nmin: " + str(min) + 
                            " \nmax: " + str(max) )
                    
            
        
        
        
    
if __name__=="__main__":
    
    
#    mes = RSSI("rssi/2018-10-18__14h52m02s.json")
#    mes.extract_RSSI()
#    print(mes.RSSI)
#    
#    mes.get_results('a')
    
    for filename in os.listdir('rssi'):
            mes = RSSI('rssi/' + filename)
            mes.extract_RSSI()
            #print(mes.RSSI)
    
            mes.get_results('a')
        

        
        
                
            

