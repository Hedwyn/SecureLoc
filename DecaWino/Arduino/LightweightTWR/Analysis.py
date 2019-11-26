import json


import statistics as st
import numpy

import math

distances = []
clkCycles = []
processTime = []
FILE = "LightweightTWR.json"


def mean_l(list):
    sum = 0
    for x in list:
        if (x < 0 ):
            list.remove(x)
            continue
        sum += x / len(list)

    return(sum)

def std(list):
    m = mean_l(list)

    sum = 0

    for x in list:
        if (x < 0):
            list.remove(x)
            continue
        sum += pow(x - m,2) / len(list)


    return(math.sqrt(sum))

with open(FILE,'r') as f:
    for line in f:
        json_log = json.loads(line)
        clkCycles.append(json_log['ClkCycles'])
        processTime.append(json_log['s'])
        distances.append(json_log['m'])


average = mean_l(distances)
std = std(distances) / 2




print(average,std)
