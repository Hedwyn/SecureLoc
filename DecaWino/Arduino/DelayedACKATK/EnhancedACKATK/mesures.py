from serial import *
import time
import datetime
import keyboard
import json
import sys

SERIALPATH='COM15'
done = False
REPO = 'Mesures/'
DWM1000_TIMEBASE = 15 * pow(10, -12)
date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

distance = {}
settings = {}
mes_idx = 0

MAX_MES = 400

if (len(sys.argv) != 2):
    print('invalid arguments, quitting...')
    exit


LOGNAME = REPO + 'mes' + '_' + str(sys.argv[1])  + '.json'

serialport = Serial(SERIALPATH,baudrate = 9600, timeout =1, writeTimeout =1)

with open(LOGNAME,'w+') as f:
    
    while(not(done) and (mes_idx < MAX_MES) ):

        if(serialport.isOpen()):

            line = serialport.readline().decode('utf-8').strip()
            print(line)
            if (len(line) > 0 and line[0] == '$'): # 0 default value for jammed ranging
                mes_idx += 1

            else:
                data = line.split('|')
                
                if (len(data) > 6):
                    dist = float(data[2])
                    rssi = float(data[13][:-1])
                    distance['m'] = dist
                    distance['rssi']= rssi
                    distance['idx'] = mes_idx
                    json.dump(distance,f)
                    f.write('\n')
                else:
                    print("wrong frame format")


                
                print('distance = ' + str(distance) )
        if (keyboard.is_pressed('q') ):
            f.close()
            done = True

    
    
