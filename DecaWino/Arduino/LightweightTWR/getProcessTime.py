from serial import *
import time
import datetime
import keyboard
import json
import sys

SERIALPATH='COM24'
done = False
DWM1000_TIMEBASE = 15 * pow(10, -12)
c = 3E8
date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

process_time = {}
settings = {}
nb_mes = 0

MAX_MES = 500

if (len(sys.argv) != 4):
    print('invalid arguments, quitting...')
    exit

##settings['SPISpeed'] = sys.argv[1]
##settings['PulseFrequency']= sys.argv[2]
##settings['PLength'] = sys.argv[3]

#LOGNAME = 'processTime' + '_' + str(sys.argv[1]) + '_' + str(sys.argv[2]) + '_' + str(sys.argv[3]) + '.json'
LOGNAME = 'LightweightTWR.json'
serialport = Serial(SERIALPATH,baudrate = 9600, timeout =1, writeTimeout =1)

with open(LOGNAME,'w+') as f:

    while(not(done) and (nb_mes < MAX_MES) ):

        if(serialport.isOpen()):

            line = serialport.readline().decode('utf-8').strip()
            print(line)
            data = line.split('|')

            if (len(data) > 6):
                t2 = data[4]
                t3 = data[5]
                process_time['ClkCycles'] = int(t3) -int(t2)
                process_time['s']= process_time['ClkCycles'] * DWM1000_TIMEBASE
                process_time['m'] = process_time['s'] * c

                json.dump(process_time,f)
                f.write('\n')
                nb_mes += 1
                print('process_time = ' + str(process_time) )
        if (keyboard.is_pressed('q') ):
            f.close()
            done = True
