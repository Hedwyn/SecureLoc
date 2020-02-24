from serial import *
import json

PORT1 = 'COM17'
PORT2 = 'COM21'


out_file = 'skew.json'
out_txt = 'skew_'
sample = {}


try:
    port1 = Serial(PORT1)
    port2 = Serial(PORT2)

except:
    print("One of the serial devices is missing")

exit_flag = False

#ports = [port1, port2, port3]
ports = [port1, port2]
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

    # for port in ports:
    #     msg = "11"
    #     port.write(msg.encode())
    while not(exit_flag):
        try:
            for port in ports:
                if (port.in_waiting > 0):
                    line = port.readline().decode('utf_8')
                    if (line[0] != '$'):

                        data = line.split('|')
                        if (len(data) == 2):
                            try:
                                temp = float(data[1])
                                skew = float(data[0])

                                sample['port'] = port.name
                                sample['skew'] = skew
                                sample['temperature'] = temp
                                if (temp > 12) and (temp < 65):
                                    if skew < 100:
                                        print(line)
                                        json.dump(sample,f)
                                        f.write('\n')
                                        f_txt[port.name].write(str(temp))
                                        f_txt[port.name].write(' ')
                                        f_txt[port.name].write(str(skew))
                                        f_txt[port.name].write('\n')
                            except:
                                print("Malformed serial frame")
        except KeyboardInterrupt:
            print("Ctrl + C receveid, quitting")
            exit_flag = True
            for port in ports:
                f_txt[port.name].close()

        # except:
        #     print("Serial port disconnected")
        #     exit_flag = True
