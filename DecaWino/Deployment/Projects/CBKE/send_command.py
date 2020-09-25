from serial import *
import sys


PROVER_PORT = 'COM29'
VERIFIER_PORT = 'COM18'
EVE_PORT = 'COM16'




if __name__ == "__main__":
    msg = sys.argv[1]
    # ex command: 2;2;128 to change plength
    print(msg)
    # try:
    port1 = Serial(PROVER_PORT)
    port2 = Serial(VERIFIER_PORT)
   # port3 = Serial(EVE_PORT)
    port1.write(msg.encode())
    port2.write(msg.encode())
    #port3.write(msg.encode())
    # print(port1.readline().decode('utf-8'))
    # print(port2.readline().decode('utf-8'))
        
    # except:
    #     print("One of the serial devices is missing")
