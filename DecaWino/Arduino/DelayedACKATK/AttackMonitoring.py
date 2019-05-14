from serial import *
import math
import keyboard
import time
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt
import threading



SERIALPATH = 'COM18'
line = ''
ANCHORS_TABFILE = 'C:/Users/pestourb/Documents/GitHub/SecureLoc/anchors.tab'
DWM1000_TIMEBASE = 15.65E-12
SPEED_OF_LIGHT = 2.5E8
exit_flag = False
STEP = 0.25 #m
START_POS = (0.9,2.4,0.)
buffer = []


def serial_handler(port):
    global exit_flag
    global buffer
    target = START_POS
    
    if not(port.is_open):
        print("ERROR: serial port is closed.")
        return
    while not(exit_flag):
        
        
        # writing to serial port
        while buffer:
            timeshifts = buffer.pop()
            print(timeshifts)
            for anchor in timeshifts:
                port.write( ('0' + anchor + str(timeshifts[anchor]) + '\r\n').encode() ) 
            
        
        try:
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8').strip()
                print(line)
           
                
        except KeyboardInterrupt:
            print("Ctrl + C received, quitting...")
            exit_flag = True
            continue
        
        except:
            print("Looks like the device has been disconnected")
            exit_flag = True
            continue


    


def parse_anchors(tabfile = ANCHORS_TABFILE):
    anchors_dic = {}
    with open(tabfile) as f:
        for line in f:
            
            if len(line) > 3 and line[0] != '#':
                parsed_line = line.split()
                anchor_id = parsed_line[3]
                anchors_dic[anchor_id] = (float(parsed_line[0]),float(parsed_line[1]),float(parsed_line[2]))
    return(anchors_dic)
                


def compute_rangings(pos,anchors_dic):
    rangings = {}
    for anchor in anchors_dic:
        coord = anchors_dic[anchor]
        ranging = math.sqrt( sum([ (x - y)**2 for x,y in zip(pos,coord)]) )
        rangings[anchor] = ranging
    return(rangings)


        

def compute_timeshifts(rogue_pos,target_pos,anchors_dic):
    rangings_rogue = compute_rangings(rogue_pos,anchors_dic)
    rangings_target = compute_rangings(target_pos,anchors_dic)

    timeshifts = {}
    
    for anchor in rangings_rogue:
        r1 = rangings_rogue[anchor]
        r2 = rangings_target[anchor]
        # rounding the timeshift to a integer value
        timeshift = int( 2 * (r2 - r1)  / (DWM1000_TIMEBASE * SPEED_OF_LIGHT) )
        timeshifts[anchor] = timeshift
    return(timeshifts)
    

def check_keyboard(target):
    global exit_flag
    (x,y,z) = target
    if (keyboard.is_pressed('q') ):
        exit_flag = True

    elif keyboard.is_pressed('UP'):
        y += STEP
        
    elif keyboard.is_pressed('DOWN'):
        y -= STEP
        
    elif keyboard.is_pressed('LEFT'):
        x -= STEP
        
    elif keyboard.is_pressed('RIGHT'):
        x += STEP
        
    elif keyboard.is_pressed('d'):
        z += STEP
        
    elif keyboard.is_pressed('c'):
        z -= STEP
    else:
        time.sleep(0.1)
        return(False)
        
    print("target: "+ str( (x,y,z) ) )
    time.sleep(0.3)
    
    return(x,y,z)
    

def update_line(hl, new_data):
	xdata, ydata, zdata = hl._verts3d
	hl.set_xdata(list(np.append(xdata, new_data[0])))
	hl.set_ydata(list(np.append(ydata, new_data[1])))
	hl.set_3d_properties(list(np.append(zdata, new_data[2])))
	plt.draw()
    
# 3D display  
    
## Testing the timeshifts computation

#anchors_dic = parse_anchors()
#print(compute_rangings( (2.,2.,0.), anchors_dic))
#print(compute_timeshifts( (2.,2.,0.), (2.5,2.5,0.), anchors_dic))
def run():
    global buffer # quick and dirty coding
    target = START_POS
    anchors_dic = parse_anchors()
    map = plt.figure()
    map_ax = Axes3D(map)
    map_ax.autoscale(enable=True, axis='both', tight=True)
     
    # # # Setting the axes properties
    map_ax.set_xlim3d([0.0, 2.0])
    map_ax.set_ylim3d([0.0, 5.0])
    map_ax.set_zlim3d([0.0, 2.0])
     
    hl, = map_ax.plot3D([0], [0], [0])
    
    update_line(hl, target)    
    plt.show(block=False)
    plt.pause(0.01)
    
    while not(exit_flag):

        #old_target = tuple(target)
        #keyboard.wait('UP','DOWN')
      
        out = check_keyboard(target)
        
        if out:
            target = out
            
            # calculating the timeshifts
            timeshifts = compute_timeshifts(START_POS,target,anchors_dic)
            
            
            # sending updated timeshifts to teensyduino
            buffer.append(timeshifts)
            
            
            update_line(hl, target)
            plt.show(block=False)
            plt.pause(0.01)



port = Serial(SERIALPATH)
t = threading.Thread(target = serial_handler, args = (port,) )
t.start()

#t2 = threading.Thread(target = run)
#t2.start()
run()

#port = Serial(SERIALPATH)
#read_serial(port)
    
        

            
            
