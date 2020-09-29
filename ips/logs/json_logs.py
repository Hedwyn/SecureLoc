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

@file jsonLogs.py
@author Baptiste Pestourie
@date 2018 November 1st
@brief Json log class - contains the json operations methods
@see https://github.com/Hedwyn/SecureLoc
"""

## subpackages
from ips.logs.json_structures import dataset,position,metadata
from ips.core.parameters import *

## other libraries
import json
import asyncio as asc
from threading import Thread
from multiprocessing import Process, Pipe
import time
from time import gmtime,strftime


class jsonLogs:
    """ Json log class - contains the json operations methods"""
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
        self.filename = self.repo + '/' + self.date + '.json'

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
                d_print('[JSON THREAD] waiting for data...')
                dataset = self.pipe.recv()
                d_print('[JSON THREAD] data received !')
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
                    if line == '\n':
                        continue
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
                    if line =='\n':
                        continue
                    json_data = json.loads(line)
                    # reading only metadata

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
