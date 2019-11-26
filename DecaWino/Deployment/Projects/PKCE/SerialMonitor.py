from serial import *
import json

PORT1 = 'COM17'
PORT2 = 'COM19'
PORT3 = 'COM21'

out_file = 'skew.json'
out_txt = 'skew_'
sample = {}


try:
    port1 = Serial(PORT1)
    #port2 = Serial(PORT2)
    port3 = Serial(PORT3)

except:
    print("One of the serial devices is missing")

exit_flag = False

#ports = [port1, port2, port3]
ports = [port1, port3]
f_txt = {}
for port in ports:
    f_txt[port.name] = open(out_txt + port.name + '.txt', 'w+')


with open(out_file,'w+') as f:
    ctr = {}
    skew = {}
    temperature = {}
    last_temp = {}
    sk = 0

    for port in ports:
        last_temp[port] = 24

    for port in ports:
        temperature[port] = 0
        skew[port] = 0
        ctr[port] = 0

    while not(exit_flag):
        try:
            for port in ports:
                if (port.in_waiting > 0):
                    line = port.readline().decode('utf_8')
                    if (line[0] != '$'):
                        print(line)
                        data = line.split('|')
                        if (len(data) == 3):
                            try:
                                temp = float(data[1])
                            except:
                                temp = last_temp[port]
                            ctr[port] += 1
                            #print(port.name + " " + str(ctr[port]) + " " + str(temperature[port]) )
                            if (temp > 15) and (temp < 60):
                                temperature[port] += temp

                                try:
                                    sk = float(data[0])
                                    skew[port] += sk
                                except:
                                    skew[port] = sk
                                last_temp[port] = temp

                            else:
                                temperature[port] += last_temp[port]
                                try:
                                    skew[port] += float(data[0])
                                except:
                                    skew[port] = sk



                            if (ctr[port] == 100):
                                #print("final temp :" + port.name + " " + str(temperature[port]))
                                temperature[port] = temperature[port] / ctr[port]

                                skew[port] = skew[port] / ctr[port]
                                ctr[port] = 0
                                sample['port'] = port.name
                                sample['skew'] = skew[port]
                                sample['temperature'] = temperature[port]
                                json.dump(sample,f)
                                f_txt[port.name].write(str(temperature[port]))
                                f_txt[port.name].write(' ')
                                f_txt[port.name].write(str(skew[port]))
                                f.write('\n')
                                f_txt[port.name].write('\n')
        except KeyboardInterrupt:
            print("Ctrl + C receveid, quitting")
            exit_flag = True
            for port in ports:
                f_txt[port.name].close()

        # except:
        #     print("Serial port disconnected")
        #     exit_flag = True
