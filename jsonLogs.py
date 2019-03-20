import json
from parameters import *
import asyncio as asc
from jsonStructures import dataset,position,metadata
from threading import Thread
from multiprocessing import Process, Pipe
import time
from time import gmtime,strftime


class jsonLogs:
    
    def __init__(self,date = '', name = '', comment = '', repo = 'mqtt'):
        
            
        self.date = date
        self.comment = comment
        self.filename = None
        self.pipe = None
        self.repo = repo
        self.lock = asc.Lock()
        self.init_filename()
        
    def init_filename(self):
        """generates the filename from the date"""
        self.filename = JSON_DIR + '/' + self.repo + '/' + self.date + '.json'
    
    def get_pipe(self,conn):
        """ gets the parent connexion for communication with the main process"""
        self.pipe = conn
        
    def logging(self):
        """ creates the pipe to get data from the main process and starts the logging process"""


        
        # parent connexion is used by the logging process
        
        logs = Thread(target = self.write)
        try:
            logs.start()
        except WindowsError:
            print('erreur windows')
            pass
        

        
    def write(self):
        if not( self.lock.locked() ):
            self.lock.acquire()
            f = open(self.filename,'w+')
            # waiting a dataset to dump from the pipe
            dataset = ''
            # checking if a termination string has been sent
            while(dataset != 'stop'):
                print('waiting for data...')
                dataset = self.pipe.recv()
                print('data received !')
                # dumping the dataset to json file
                if (dataset != 'stop'):
                    json.dump(dataset, f)
                    # jumping to the next line for next logs
                    f.write('\n')
            # closing file when termination signal is received
            f.close()
                    
                    
        else:
            print("target log already open. Cannot write")
    
    def start(self):
        """allows writing on the log file, blocks reading access"""
        if not(self.lock.locked() ):
            self.lock.acquire()
        else:
            print("target log already open. Cannot start")
        

    def close(self):
        """closes the logs file"""
        if (self.lock.locked()):
            self.lock.release()
            self.file.close()
        else:
            print("log file is already.closed")
        
    
    def read(self,filename = ''):
        """reads logs file and returns the data in an array"""
        data = []
        # changes the filename if given
        if (filename != ''):
            self.filename = filename
            
        
        if not( self.lock.locked() ):
            #uses the current filename if no name is given
            
            with open(self.filename) as f:
                for line in f:
                    json_data = json.loads(line)
                    # ignoring metadata
                    # metadata are read by read_metadata method
                    if not("metadata" in json_data):                
                        data.append(json_data)
                    
        return(data)
                
    def read_metadata(self,filename = ''):
        """reads logs file and returns the metadata"""

        # changes the filename if given
        if (filename != ''):
            self.filename = filename
            
        
        if not( self.lock.locked() ):
            #uses the current filename if no name is given
            data = []
            with open(self.filename) as f:
                for line in f:
                    json_data = json.loads(line)
                    # ignoring metadata
                    # metadata are read by read_metadata method
                    if ("metadata" in json_data):                
                        data.append(json_data)
                    
        return(data)                
   
        
        

            
            


    
if __name__ == "__main__":
    #testing
    
    
    dataset1 = dataset(100,'TWR','A','3',50,[1,5],90)
    dataset2 = dataset(101,'TWR','A','3',49,[1,4],88)
    log1 = jsonLogs( 'test.json','log_test','no comment')
    p,q = Pipe()
    log1.get_pipe(p)
    log1.logging()
    time.sleep(1)
    q.send(dataset1.export())
    time.sleep(1)
    q.send(dataset2.export())
    time.sleep(1)
    meta = metadata()
 
    q.send(meta.export())
    
    q.send('stop')
    time.sleep(1)
    
    data = log1.read_metadata()
    print(data)
 
    
    
   
    
    
    #log1.write(dataset1)
    #log1.read()
    #print(json.dumps(dataset1.export() ))
    #print(log1.read() )
#    with open('13_09.json','r') as f:
#        for line in f:
#                print(f)
        #data = json.load(f)
     
        
        
       
       
       
       
    
       
       
       
        
        
        
        