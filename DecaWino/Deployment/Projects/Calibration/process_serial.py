from serial import *
import sys

PROVER_PORT = 'COM18'
VERIFIER_PORT = 'COM29'

out_file = 'CBKE_log_'
counter = 0



if __name__ == "__main__":
    if len(sys.argv) == 3:
        print("Setting custom parameters...")
        cbke_length = sys.argv[1]
        pp_delay = sys.argv[2]

    else:
        cbke_length = "200"
        pp_delay = "1"

    try:
        port1 = Serial(PROVER_PORT, 115200)
        port2 = Serial(VERIFIER_PORT, 115200)
        
    except:
        print("One of the serial devices is missing")

    parameters = ['#', '^', '*', '$']
    ports = [port1, port2]
    # for port in ports:
    #     # msg = "2;1;" + pp_delay + " "
    #     # port.write(msg.encode())
    #     msg = "2;0;" + cbke_length + " "
    #     port.write(msg.encode())



    msg = "1"
    port1.write(msg.encode())
    msg = "0"
    port2.write(msg.encode())




    exit_flag = False
    writing_on = {}
    
    writing_on[port1.name] = False
    writing_on[port2.name] = False
    f = {}
    f[port1.name] = open(out_file + port1.name + '.txt','w+')
    f[port2.name]  = open(out_file + port2.name + '.txt','w+')
 
    try:
        print("Starting")
        while not(exit_flag):
            for idx,port in enumerate(ports):
                    while (port.in_waiting > 0):
                        
                        #line = port.readline().decode('utf_8')
                        
                        char = port.read().decode('utf-8')
                        #print(char)
                        if char in parameters:
                            print("Signature incoming...")
                            writing_on[port.name] = True
                            counter += 1
                        if writing_on[port.name] and ((char == '\r') or (char == '\n')):
                            print("End of signature")
                            writing_on[port.name] = False
                            f[port.name].write("\n")
                        if writing_on[port.name]:
                            f[port.name].write(char)

                        if (counter == 8):
                            exit_flag = True

                        
                        # if line[0] in parameters:
                        #     counter += 1
                        #     print(counter)
                        #     f[port.name].write(line)
                        #     if (counter == 8):
                        #         exit_flag = True
                                
    except KeyboardInterrupt:
        print("Ctrl + C receveid, quitting")

        exit_flag = True
    
    # blending files
    f_out = open(out_file + '.txt','w+')
    for line in f[port1.name]:
        f_out.write(line)
    
    for line in f[port2.name]:
        f_out.write(line)

    for key in f:
        f[key].close()

    port1.close()
    port2.close()

