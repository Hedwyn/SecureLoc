# -*- coding: utf-8 -*-
import json
import os
import matplotlib.pyplot as plt

LOGS_DIR = 'logs'

logs_list = os.listdir(LOGS_DIR)
if logs_list:
    file = logs_list[0]
else:
    print("LOGS directory is empty")
    sys.exit()


mse_list = []
with open(LOGS_DIR + '/' + file) as f:
    for line in f:
        if line != '\n':
            dic = json.loads(line)
            mse_list.append(dic["MSE"])



#printing results with patplotlib

fig = plt.figure("MSE")

ax1 = fig.add_subplot(111)

plt.ylabel("RME (m²)")
plt.xlabel("Time(s)")

time = [0.33 * i for i in range(len(mse_list))]

ax1.plot(time[:],mse_list[:])
plt.show()
        