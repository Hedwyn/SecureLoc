import json
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm
import statistics as st
import numpy

NB_BINS = 100
SPEED_OF_LIGHT = 300000000 #m/s
DISTANCE_MAX = 10 #m
CUMUL = False

def read_json(filename):
    settings = {}
    processTime = []
    clkCycles = []
    filedata = filename.split('_')

    # getting the settings in the filename
    if (len(filedata)!= 4):
        print('improper filename format')
    else:
        settings['SPISpeed'] = filedata[1]
        settings['PFrequency'] = filedata[2]
        settings['PLength'] = filedata[3].split('.')[0] # removing .json

    # reading logs
    with open(filename,'r') as f:
      
        for line in f:
            json_log = json.loads(line)
            
            clkCycles.append(json_log['ClkCycles'])
            processTime.append(json_log['s'])
    return(settings,clkCycles,processTime)

def process_data(data,nb_bins = NB_BINS):


    
    bins = []
    bin = {}
    
    for val in data:
        if (val < 0):
            data.remove(val)

    min_val = min(data)
    max_val = max(data)

    bin_size = (max_val - min_val) / nb_bins



    for i in range(nb_bins):
        bin['center'] = min_val + bin_size /2 + i * bin_size
        bin['occurences'] = 0
        bins.append(bin.copy())

    # sorting data

    for val in data:
        bin_idx = int( (val - min_val) // bin_size )
       
        if (bin_idx == nb_bins) :
            # max value
            bin_idx = bin_idx - 1
        if CUMUL:
            for i in range(bin_idx + 1):
                bins[i]['occurences'] += 1               
                
        else:
            bins[bin_idx]['occurences'] += 1
        
   

    occurences= []
    bin_centers= []

    for b in bins:
        bin_centers.append(b['center'])
        occurences.append( b['occurences'] /len(data))

    print('variability = ' + str(max_val - min_val))
    print('bin size= ' + str(bin_size))
    print('Mean process time= ' + str(st.mean(data)) )
    print('Standard deviation= ' + str (st.stdev(data)) )
    

    return(bin_centers,occurences)
                           
        
        
def get_proba(processTime):
    timesA= processTime.copy()
    timesA.sort()
    timesB = timesA.copy()
    timespan = 2 * DISTANCE_MAX / SPEED_OF_LIGHT
    proba = 0
    for i,ta in enumerate(timesA):
        j = i
        k = i
        while (j < len(timesA)) and (abs(timesA[j] - timesA[i]) < timespan):
            j+=1
            proba += 1
        while (k >= 0) and (abs(timesA[k] - timesA[i]) < timespan):
            k-=1
            proba += 1
    proba = proba / pow(len(timesA), 2)
    print("proba : " + str(proba))
    
            
def get_proba_2(processTime):       
    times = []

    for time in processTime:
        if time > 0:
            times.append(time)
    
    timespan = 2 * DISTANCE_MAX / SPEED_OF_LIGHT
    print("timespan = " + str(timespan) )
    #mean = numpy.mean(times)
    times.sort()
    median = times[int(len(times) /2)]
    print("median :" + str(median))
    success = 0
    for time in processTime:
        if abs((time - median)) < timespan:
            success += 1

    success_rate = success / len(times)
            
     
    print("proba : " + str(success_rate))

    
def compute_proba(bin_centers,occurences):
    timespan = 2 *DISTANCE_MAX / SPEED_OF_LIGHT
    proba = 0
    for i,center in enumerate(bin_centers):
        j = i
        k = i
        while (j >= 0) and (center - bin_centers[j] <= timespan):
            proba += occurences[i] * occurences[j]
            j -= 1
        
        while (k < len(bin_centers)) and (bin_centers[k] - center <= timespan):
            proba += occurences[i] * occurences[j]
            k += 1
            

    
    print('proba : ' + str(proba))

        
            
        
    
    
def get_success_probability(processTime,distance_max = DISTANCE_MAX):
    """returns the probability to get a distance variation < 10 m when using an ack attack"""
    timespan = distance_max / SPEED_OF_LIGHT

    for val in processTime:
        if (val < 0):
            processTime.remove(val)
    min_val = min(processTime)
    max_val = max(processTime)

    nb_bins = 4 *  int(( (max_val - min_val) // timespan)) 

    (bin_centers,occurences) = process_data(processTime,nb_bins)
    proba = 0


 
       
    compute_proba(bin_centers,occurences)
    
    for i in range(1,len(occurences) - 1):
        proba += (occurences[i] * (occurences[i-1] + occurences[i] + occurences[i+1]))

    print('proba: ' + str(proba) )
        

    return((bin_centers,occurences))
    
    
    
            
        

    
        

def plot_data(filename,unit ='s'):
    (settings,clkCycles,processTime) = read_json(filename)

    (bin_centers,occurences) = process_data(processTime)


    # converting to the right unit
    #default: s
    if (unit == 's'):
        factor = 1
    if (unit == 'ms'):
        factor = pow(10,3)
    if (unit == 'us'):
        factor = pow(10,6)
    if (unit == 'ns'):
        factor = pow(10,9)
    if (unit == 'ps'):
        factor = pow(10,12)

    for i in range (len(bin_centers)):
        bin_centers[i] = bin_centers[i] * factor

    
    fig1 = plt.figure('SPI Speed: ' + str(settings['SPISpeed']) + ' Hz; Pulse Frequency: ' + str(settings['PFrequency']) + ' MHz; Preamble Length: ' + str(settings['PLength']) )
    ax1 = fig1.add_subplot(111)
    ax1.set_title('SPI Speed: ' + str(settings['SPISpeed']) + ' Hz\n Pulse Frequency: ' + str(settings['PFrequency']) + ' MHz\n Preamble Length: ' + str(settings['PLength']) )
    ax1.plot(bin_centers[:],occurences[:])

    
    plt.xlabel('Processing Time(' + unit + ')')
    plt.ylabel('Probability')
    plt.show()


def show_success_probability(filename):
    (settings,clkCycles,processTime) = read_json(filename)

    (bin_centers,occurences) = get_success_probability(processTime)

    
    fig1 = plt.figure('SPI Speed: ' + str(settings['SPISpeed']) + ' Hz; Pulse Frequency: ' + str(settings['PFrequency']) + ' MHz; Preamble Length: ' + str(settings['PLength']) )
    ax1 = fig1.add_subplot(111)
    ax1.set_title('SPI Speed: ' + str(settings['SPISpeed']) + ' Hz\n Pulse Frequency: ' + str(settings['PFrequency']) + ' MHz\n Preamble Length: ' + str(settings['PLength']) )
    ax1.plot(bin_centers[:],occurences[:])
    plt.xlabel('Processing Time(s)')
    plt.ylabel('Probability')
    plt.show()
    



#plot_data('Papier\processTime_20000000_16_64.json','us')

#show_success_probability('processTime_20000000_16_64.json')

(settings,clkCycles,processTime) = read_json('96Mhz\processTime_20000000_64_64.json')
(settings,clkCycles,processTime) = read_json('Papier\processTime_20000000_16_64.json')

get_proba_2(processTime)




    
