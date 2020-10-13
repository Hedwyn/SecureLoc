import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import matplotlib.animation as animation
from threading import Thread
from multiprocessing import Pipe
from serial import *
import random
import time

VERIFIER_PORT = 'COM23'
PROVER_PORT = 'COM31'



def serial_pool():
    global data_p
    try:
        port1 = Serial(VERIFIER_PORT)
        port2 = Serial(PROVER_PORT)
        
    except:
        print("One of the serial devices is missing")


    p1, q1 = Pipe()
    p2, q2 = Pipe()

    t1 = Thread(target = read_serial, args = (port1, '1',q1))
    t2 = Thread(target = read_serial, args = (port2,'0',q2))
    t1.setDaemon(True)
    t2.setDaemon(True)
    t1.start()
    t2.start()

    # ani = animation.FuncAnimation(
    #     fig, animate, init_func=init, interval=1000, blit=True, save_count=10)
    try:
        fig = plt.figure()
        axe = fig.add_subplot(111)
        while True:
            if (p1.poll()):
                data1 = p1.recv()
                data2 = p2.recv()
                plt.cla()
                axe.plot(data1, color = 'red', marker = '^')
                axe.plot(data2, color = 'blue', marker = '^')           
                plt.pause(0.5)
            
            
    #plt.show()
    except:
        print("ops")
        p1.send("q")
        p2.send("q")
            
    

            
    



def read_serial(port, mode, pipe):
    print(port.name)
    port.write(mode.encode())
    global data_p
    global data_v
    try:    
        while not(pipe.poll()):
            if port.in_waiting > 0:
                line = port.readline().decode('utf-8') 
                #print(line)         
                if line[0] == '!':
                    data_str = line[1:].split(';')
                    data = []
                    for val_str in data_str:
                        try:
                            val = float(val_str)
                            data.append(val)
                        except:
                            pass
                    pipe.send(data)
                    #print(data)
                if line[0] == '#':
                    return
    except:
        print("Thread stopped")


serial_pool()










