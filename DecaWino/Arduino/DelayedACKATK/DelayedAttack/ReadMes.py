import json
import sys
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm
import statistics as st

NB_BINS = 20
SPEED_OF_LIGHT = 300000000 #m/s
DISTANCE_MIN = 50
DISTANCE_MAX = 55 


DIR = 'Mesures/'
CUMUL = False

def read_json(filename):
    settings = {}
    distances = []
    rssi_list = []
    index = []
    filetag = filename.split('_')[1:]

  

    # reading logs
    with open(DIR + filename,'r') as f:
      
        for line in f:
            json_log = json.loads(line)
            
            rssi_list.append(json_log['rssi'])
            distances.append(json_log['m'])
            index.append(json_log['idx'])
    return(filetag,rssi_list,distances,index)


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
            for i in range(nb_bins -1 - bin_idx):
                bins[nb_bins - 1 - i]['occurences'] += 1               
                
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
            

def filter_successful_enlargements(distances):
    filtered_distances = []
    fail = 0
    success = 0
    for distance in distances:
        distance = abs(distance)
        if (distance < DISTANCE_MIN) or (distance > DISTANCE_MAX):
            fail+=1
        else:
            filtered_distances.append(distance)
            success += 1
            print(distance)
    print(success)
    print(fail)
    print('Success rate :' + str(success/ (fail + success)) )
    return(filtered_distances)
    
            
        

def analyze_data(filename):
    (filetag,rssi_list,distances,index) = read_json(filename)
    nb_mes = int(index[-1])
    ranging_rate = len(distances) / nb_mes

    success = 0

    average = 0
    std = 0
    
   
    for distance in distances:

        if (distance > DISTANCE_MIN) and (distance < DISTANCE_MAX):
            success += 1
            average += distance

    average /= success
    for distance in distances:
        if (distance > DISTANCE_MIN) and (distance < DISTANCE_MAX):
                
            std += pow((distance - average),2)
    std = math.sqrt(std / success)
            

    success_rate = success / nb_mes
 
     
    print("nb_mes = " + str(nb_mes))
    print("success_rate = " + str(success_rate))
    print("average, std= ")
    print(average,std)
    
                
def plot_data(filename):
    (filetag,rssi_list,distances,index) = read_json(filename)
    fig1= plt.figure("Distances repartition(m)")
    ax1= fig1.add_subplot(111)
    
    (bin_centers,occurences) = process_data(filter_successful_enlargements(distances))
    print(bin_centers,occurences)
    plt.xlabel('Distance repartition(m)')
    plt.ylabel('Probability')
    
    ax1.plot(bin_centers[:],occurences[:])
    plt.show()

  


    





plot_data('mes_2_400_50m.json')
#analyze_data('mes_4_400_-10m.json')





    
