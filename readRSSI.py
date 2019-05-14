import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import sys
from Filter import Filter
import numpy as np
from jsonLogs import jsonLogs
from jsonStructures import dataset,position,metadata
import os
import json
import time


RX_LOG_DIR = 'RX_quality/'
TABFILE = 'RSSI_results.tab'
MES_DIR = 'MesuresRSSI/'
reference_points = ["P1","P2","P3"]

class RSSI:
    """Contains the methods for RX quality data extraction"""
    
    def __init__(self,filename):
        self.filename = filename
        self.rx_data = {}
        self.rssi = {}
        self.fp_power = {}
        self.std_noise = {}
        self.temperature = {}
        self.log = jsonLogs()
        self.rp = {}
        
        


    def extract_rx_phy_data(self):
        """Loads RX data from json file"""
        json_data = self.log.read(self.filename)
        #print(json_data)
     
        rp_idx = -1
        for data in json_data:
            anchorID = data["anchorID"]
            botID = data["botID"]
            
            # getting data on RX quality
            rssi = data["rssi"]
            fp_power = data["fp_power"]
            std_noise = data["std_noise"]
            temperature = data["temperature"]
            rp = data["reference_point"]
            
            
            if rp != None and not(str(rp) in self.rp):
                rp_idx += 1
                self.rp[str(rp)] = rp_idx
                
                
            
            
            if not(anchorID in self.rssi) :
                
                self.rssi[anchorID] = {}
                self.fp_power[anchorID] = {}
                self.std_noise[anchorID] = {}
                self.temperature[anchorID] = {}
                self.rx_data[anchorID] = {}
            if not(botID in self.rssi[anchorID]):
                # creating an empty array to store RSSI measurements
                self.rssi[anchorID][botID] = []
                self.fp_power[anchorID][botID] = []
                self.std_noise[anchorID][botID] = []
                self.temperature[anchorID][botID] = []
                self.rx_data[anchorID][botID] = []
            
            if (rssi != None):
                self.rssi[anchorID][botID].append(rssi)

            if (rssi != None):
                self.fp_power[anchorID][botID].append(fp_power)
            if (rssi != None):
                self.std_noise[anchorID][botID].append(std_noise)               
            if (rssi != None):
                self.temperature[anchorID][botID].append(temperature) 

            self.rx_data[anchorID][botID].append([rssi, fp_power,std_noise,temperature,rp_idx])
    
    
    def filter_rp(self,serie,rp_idx):
        """filters the data in serie to keep only the measurements related to the given reference point"""
        rp_data = [x for x in serie if x[-1] == rp_idx]
        #print(rp_data)
        return(rp_data)
 
    
    
    def split_json(self,cleaning = True):
        """creates a json log for each bot/anchor combination with the related RX data"""
        # creating the buffers for each anchor/bot combination
        buffers = {}
        # extracting the json logs for each bot/anchor combination
        json_data = self.log.read(self.filename)
        

        


        for log in json_data:
      
            if log["anchorID"] != None and log["botID"]  != None:
                anchorID = log.pop("anchorID")
                botID = log.pop("botID") 
                
                
                if not(anchorID) in buffers:
                    buffers[anchorID]= {}
                    
                if not(botID in buffers[anchorID]):
                
                    buffers[anchorID][botID] = []
                    
                # appending the log in the right buffer   
                buffers[anchorID][botID].append(log)
                
                
        #creating the directories for json logs        
        for anchorID in buffers:

            if not(os.path.exists(RX_LOG_DIR + anchorID)):
                os.mkdir(RX_LOG_DIR + anchorID)
                
            for botID in buffers[anchorID]:
                if cleaning:
                    print("cleaning up directory..." + anchorID)
                    for filename in os.listdir(RX_LOG_DIR + anchorID):
                        os.remove(RX_LOG_DIR + anchorID + '/' + filename)
         
        # writing the data stored in the buffers in the json files
        for anchorID in buffers:
            fileroot = RX_LOG_DIR + anchorID
        
            for botID in buffers[anchorID]:
                #filename += '/' + self.filename.split("/")[-1] 
                p = buffers[anchorID][botID][0]["reference_point"]
                idx = 0
                file_idx = 1
                while (file_idx < 4):
                    filename = fileroot +  "/" +  "P" + str(file_idx) + "_" + self.filename.split("/")[-1] 
                    file_idx += 1
                    with open(filename, 'w+') as f:
                        print(f)
                        
                        for log in buffers[anchorID][botID][idx:]:
                            if log["reference_point"] != p:
                                p = log["reference_point"] 
                                break;
                            json.dump(log,f)
                            f.write('\n')
                            idx += 1 

        
                
            
        
        
        

                    
                
        
    
    def get_minmax(self,serie):
        """returns the minimum and maximum values of a list"""

        
        
        if len(serie) > 0:
            min = serie[0]
            max = serie[0]
        
            for val in serie:
            
                if (val < min):
                    min = val
                if (val > max):
                    max = val
            return(min,max)
        else:          
            raise Exception("The serie is empty !")
                
        
        
    
    def get_mean(self,serie):
        """returns the mean of an array"""
        
        mean = 0
        for rssi in serie:
            if (rssi != None):
                mean += rssi
            
        return(mean / len(serie) )
      

        
    
    def get_std(self,serie):
        """returns the standard deviation of an array"""
        
        std = 0
        mean = self.get_mean(serie)
        
        for rssi in serie:
            std += abs(rssi - mean)
        
        return(std/ len(serie) )
        
    
    def get_results(self,overwrite= 'w+'):
        """computes RX analysis of the json log"""
        
        with open(OUTPUT_FILE,overwrite) as f:
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
                    
            
    def export_results(self):
        """exports the log analysis results to the ouput tab file"""
        
        data2display = ["rssi","fp_power"]
        
        # opening the output tab file
#        try:
#            f = open(TABFILE,'w')
#        except:
#            sys.exit()
        
        with open(TABFILE, 'a') as f:
            f.write(self.filename + "\n")
            
            for rp_idx,rp in enumerate(reference_points):
                f.write(rp)
                
                for idx,data in enumerate(data2display):
                    f.write("\n" + data)
                    
                    for anchorID in sorted([ID for ID in self.rx_data if ID != None]):
                        print("Anchor  " + anchorID + " results:\n")
                        f.write("\n" + anchorID)
                        for botID in sorted([ID for ID in self.rx_data[anchorID] if ID != None]):   
                            rp_data = self.filter_rp(self.rx_data[anchorID][botID], rp_idx)
       
                            serie = np.array(rp_data)[:,idx]
                          
                            mean = self.get_mean(serie)
                            std = self.get_std(serie)
                            
                            (mn, mx) = self.get_minmax(serie)
                            print("Robot  " + botID + ":\n")
                            print(data + " mean:" + str(mean) + " dB")
                            print(data + " std:" + str(std) + " dB")
                            print(data + " min:" + str(mn) + " dB")
                            print(data + " max:" + str(mx) + " dB")
                            
                            # writing the data into tabfile
                            #f.write("\t" + botID + "\t" + str(mean) + "\t" + str(std) + "\t" + str(mn) + "\t" + str(mx))
                            f.write("\t" + str(mean) + "\t" + str(std) + "\t" + str(mn) + "\t" + str(mx))
                f.write("\n\n")
            f.write('\r')

if __name__=="__main__":
    default_mode = 'ALL'
    
    # cleaning the tabfile
    if os.path.exists(TABFILE):
        os.remove(TABFILE)  
    
    if len(sys.argv) >= 2:
        # a mode has been specifed
        if sys.argv[1] == 'all':
            # processing all the json in the MES_DIR directory
            mode = 'ALL'
            
        elif sys.argv[1] != 'last':
            mode = 'LAST'
        else:
            print("unrecognized mode")
    
    else:    
        mode = default_mode
        
    
    if mode == 'ALL':
        cleaning = True
        for filename in os.listdir(MES_DIR):
            mes = RSSI(MES_DIR + filename)           
            mes.extract_rx_phy_data()
            #mes.split_json()
            mes.export_results()
            mes.split_json(cleaning)
            cleaning = False            
    
    
    else:
        filename = os.listdir(MES_DIR).pop()
        mes = RSSI(MES_DIR + filename)
        
        mes.extract_rx_phy_data()
        mes.export_results()

