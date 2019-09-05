from serial import *
import keyboard

SERIALPATH = 'COM15'
LOGS = 'SnifferLogs.txt'
exit_flag = False
line = ''


with open(LOGS,'w+') as f:
    try:
        port = Serial(SERIALPATH)
    except:
        print("unable to open Serial port")
        
        
    while not(exit_flag):
        try:
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8').strip()
                f.write(line)
                f.write('\n')            
                
        except KeyboardInterrupt:
            print("Ctrl + C received, quitting...")
            exit_flag = True
            continue
        
        except:
            print("Looks like the device has been disconnected")
            exit_flag = True
            continue
        

            
            
