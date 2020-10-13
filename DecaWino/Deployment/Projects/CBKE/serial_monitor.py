from serial import *
import sys
from threading import Thread
import time

PROVER_PORT = 'COM23'
VERIFIER_PORT = 'COM31'
NB_DATA = 7
out_file = 'CBKE_log_'
parameters = ['#', '^', '*', '$', '_', '&', '/']
b_parameters = [char.encode() for char in parameters]

def read_serial(port, f, mode):
    sig_counter = 0
    print(port.name)
    port.write(mode.encode())
    while (sig_counter != NB_DATA):
        while (port.in_waiting > 0):
            # char = port.read().decode('utf-8')
            # if char in parameters:
            #     sig_counter += 1
            #     print("signature received")
            # f.write(char)
            line = port.readline().decode('utf-8') 
            print(line)         
            if line[0] in parameters:
                print("Signature incoming")
                print(port.name)
                sig_counter += 1
                f.write(line)

def serial_pool():
    print("Number of signatures expected:" + str(NB_DATA))
    try:
        port1 = Serial(VERIFIER_PORT)
        port2 = Serial(PROVER_PORT)
        
    except:
        print("One of the serial devices is missing")


    f1 = open(out_file + port1.name + '.txt', 'w+')
    f2 = open(out_file + port2.name + '.txt', 'w+')
    # msg = '1'
    # port2.write(msg.encode())
    # read_serial(port1, f2, '0') 
    t1 = Thread(target = read_serial, args = (port1, f1,'1',))
    t2 = Thread(target = read_serial, args = (port2, f2,'0',))
    t1.start()
    t2.start()
    t1.join()
    
    t2.join()

    f1.close()
    f2.close()
    blend_files(out_file + port1.name + '.txt', out_file + port2.name + '.txt', out_file + 'final.txt')
    port1.close()
    port2.close()


def blend_files(path1, path2, path_out):
    f1 = open(path1)
    f2 = open(path2)
    f_out = open(path_out, 'w+')

    for line in f1:
        f_out.write(line)
    for line in f2:
        f_out.write(line)
    f_out.close()
    f1.close()
    f2.close()

if __name__ == "__main__":
    serial_pool()
    

