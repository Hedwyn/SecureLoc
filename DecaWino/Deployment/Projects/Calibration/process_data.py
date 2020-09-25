import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys
import math
import random
import scipy.stats
import scipy.fftpack
import scipy.signal
from scipy.stats.stats import pearsonr 

plt.style.use('C:/Users/pestourb/Documents/Plateforme src/matplotlib-master/lib/matplotlib/mpl-data/stylelib/custom.mplstyle')
font = {'fontname':'Century Gothic', 'size' : 16}

parameters = ['#', '^', '*', '$']
colors = ['black', 'green']

in_file = 'CBKE_log_final.txt'
THOLD_RATIO = 0.67448 # for a normal distribution
THOLD_RATIO = 0.5
GUARD_RATIO = 0.16
frequency_unit = 120


## frequency filtering
HPF = False
LC = 15 # low pass filter cut frequency
HC = 500 # high pass filter cut frequency

SLICE_LENGTH = 1000
DISABLE_MATPLOT = 0
cbke_vectors = {}
Z = 1.96 # constant for confidence interval 5%
for p in parameters:
    cbke_vectors[p] = []



def parseFile():
    with open(in_file) as f:
        for line in f:
            p = line[0]
            if p in parameters:
                cbke_vector = cbke_vectors[p]
                data_str = [val for val in line[1:].split(';')]
                data = []
                for str_val in data_str:
                    try:                   
                        val = float(str_val)
                        data.append(val)
                    except:
                        pass
                cbke_vector.append(data)
            
def mean_filter(data):
    counter = 0
    acc = 0
    filtered_data = []
    mean_val = np.mean(data)
    for val in data:
        acc += val
        counter += 1
        if (counter == mean_length):
            filtered_data.append(acc / counter - mean_val)
            counter = 0
            acc = 0
    return(filtered_data)


def mean_median_filter(data):
    idx = 0
    processed_data = []
    while (idx < len(data)):
        chunk= data[idx:idx+mean_length]
        sorted_chunk = np.sort(chunk)
        decile_idx = mean_length // 10
        average = np.mean(sorted_chunk[decile_idx:-decile_idx])
        processed_data.append(average)
        idx += mean_length
    return(processed_data)


def compute_kurtosis(nu, sigma):
    kurtosis = pow(nu, 4) / pow(sigma, 4)
    return(kurtosis)

def auto_correlation(data):
    a = (data - np.mean(data)) / (np.std(data) * len(data))
    b = (data - np.mean(data)) / (np.std(data))
    autocor = np.correlate(a, b, 'full')
    return(autocor)

def custom_auto_correlation(data):
    N = len(data)
    ref_var = np.var(data)
    shifted_data = data.copy()
    var_array = []
    autocov = []
    for shift in range(N):        
        var_array = []
        for idx,val in enumerate(data[shift:]):
            var_array.append(val - shifted_data[idx])
        variance = np.var(var_array)
        autocov.append(variance/ref_var)
    return(autocov)

    

def sliding_mean_filter(data):
    counter = 0
    acc = []
    filtered_data = []
    mean_val = np.mean(data)
    for val in data:
        acc.append(val)
        if (len(acc) == mean_length):
            mean_val = np.mean(acc)
            del acc[0]
            filtered_data.append(mean_val)
    return(filtered_data)


def get_bit_balance(data):
    counter_1 = 0
    counter_0 = 0
    for char in data:
        if char == '1':
            counter_1 += 1
        elif char == '0':
            counter_0 += 1 
    if (counter_1 + counter_0) > 0 :
        return(counter_1 / (counter_1 + counter_0) )
    else:
        return(0)

def median_filter(data):
    sorted_data = []
    sorted_idx = []
    filtered_data = []
    for i,val in enumerate(data):
        idx = 0
        while (idx < len(sorted_data)) and (sorted_data[idx] < val):
            idx += 1
        sorted_data.insert(idx, val)
        sorted_idx.insert(idx,i)
    decile_idx = int(len(sorted_data) / 10)
    k = 0
    idx_to_remove = []
    while (k <= decile_idx):
        idx_to_remove.append(sorted_idx[k])
        k += 1

    k = 0
    while (k <= decile_idx):
        k += 1
        idx_to_remove.append(sorted_idx[len(data) - k])
    
    for i,val in enumerate(data):
        if not(i in idx_to_remove):
            filtered_data.append(val)
    return(filtered_data)
        

def center(data):
    center = np.mean(data)
    return([val - center for val in data])


def compute_pdf(data):
    sigma = np.mean(data)
    nu = np.std(data)
    bin_size = nu / 40
    sorted_data = np.sort(data)

    bins = []
    bins_stats = []
    bin_ctr = 0

    min_val = sorted_data[0]
    bin_edge = min_val + bin_size
    for val in sorted_data:
        if val > bin_edge:
            bin_edge += bin_size
            bins.append(bin_edge)
            bins_stats.append(bin_ctr / len(data))
            bin_ctr = 0
        else:
            bin_ctr += 1
    return(bins, bins_stats)
    

def compute_fft(data):
    transfo = scipy.fftpack.rfft(data)
    N = len(transfo)
    ## different scling conventions exist:
    # do nothing / scale by 1/N; scale by 1 / sqrt (N); etc
    transfo = [val / math.sqrt(N) for val in transfo]

    #transfo = scipy.fftpack.ifft(transfo)
    frequencies = [n * (frequency_unit/(2 * N)) for n in range(N)]
    return(frequencies, transfo)


def apply_hpf(data):
    hpf = scipy.signal.butter(2, LC, 'hp', fs=1600, output='sos')
    lpf = scipy.signal.butter(10, HC, 'lp', fs=1600, output='sos')
    filtered = scipy.signal.sosfilt(hpf, data)
    filtered = scipy.signal.sosfilt(lpf, filtered)
    return(filtered)

def compute_confidence_interval(data):
    N = len(data)
    intervals = []
    intervals_opposite = []
    for d in range(N - 4):
        threshold = Z / math.sqrt(N - d)
        intervals.append(threshold)
        intervals_opposite.append(-threshold)
    print("*** Confidence interval 5% at lag 10: " + str(intervals[9]))
    return(intervals, intervals_opposite)



def plot(param):
    ## figures
    fig_raw = plt.figure()
    fig_channel = plt.figure()
    fig_autocor = plt.figure()
    fig_fft = plt.figure()
    fig_pdf = plt.figure()
    #fig_deriv = plt.figure()

    ## axes
    axe_1 = fig_raw.add_subplot(111)
    axe_2 = fig_channel.add_subplot(111)
    axe_3 = fig_autocor.add_subplot(111)
    axe_4 = fig_fft.add_subplot(111)
    axe_5 = fig_pdf.add_subplot(111)

    ## labels
    axe_1.set_xlabel('Sample #', **font)
    axe_1.set_ylabel('First path power variations(dB)', **font)
    axe_2.set_xlabel('Sample #', **font)
    axe_2.set_ylabel('First path power variations(dB)', **font)
    axe_3.set_xlabel('Lag', **font)
    axe_3.set_ylabel('Normalized Autocorrelation', **font)
    axe_4.set_xlabel('Frequency (Hz)', **font)
    axe_4.set_ylabel('Normalized first path power (dB)', **font)

    #axe_4 =  fig_deriv.add_subplot(111)
    keys = []
    curated_data = []
    for i,data in enumerate(cbke_vectors[param]):      
        #processed_data = center(sliding_mean_filter(median_filter(data)))
        processed_data = process_data(data)
        
        curated_data.append(processed_data)
        #curated_data.append(filtered_data)
        axe_1.plot(data[:], color = colors[i])        
        axe_2.plot(processed_data[:], color = colors[i])

        autocor = auto_correlation(processed_data)
        autocor = autocor[(len(autocor) // 2):]
        #autocor = auto_correlation(data)
        randomness = np.mean(autocor[20:])
        print("*** Autocorrelation: " + str(randomness))
        axe_3.plot(autocor, color = colors[i])
        #axe_4.plot(np.diff(autocor), color = colors[i])
        #axe_4.plot(filtered_data[:], color = colors[i])
        bins, pdf = compute_pdf(data)
        key = quantize_2(processed_data)
        keys.append(key)
        print("*** Bit balance key " + str(i) + ": " + str(get_bit_balance(key))   ) 

    
    freq, transfo = compute_fft(processed_data)    
    #freq_filtered, transfo_filtered = compute_fft(filtered_data)     
    low_cut = 10
    axe_4.plot(freq[low_cut:], transfo[low_cut:], color = 'blue')
    bins, pdf = compute_pdf(data)
    axe_5.plot(bins[:], pdf[:], color = 'blue')
    #axe_4.plot(freq_filtered[low_cut:], transfo_filtered[low_cut:], color = colors[1])

    intervals, intervals_opposite = compute_confidence_interval(processed_data)
    axe_3.plot(intervals, color = 'red')
    axe_3.plot(intervals_opposite, color = 'red')
        
        #axe.plot(bins[:], pdf[:])
    #pearson, collision_proba = pearsonr(cbke_vectors[param][0],cbke_vectors[param][1])
    pearson, collision_proba = pearsonr(curated_data[0],curated_data[1])
    print(np.cov(curated_data[0],curated_data[1]))
    print("*** Pearson correlation coefficient: " + str(pearson))
    print("*** Collision probability: " + str(collision_proba))
    print("*** BER: " + str(compute_ber(keys[0], keys[1])))
    
    if not(DISABLE_MATPLOT):
        plt.show()


def compute_ber(key1, key2):
    ber = 0
    doubt_counter = 0
    bit_counter = 0
    for i, bit in enumerate(key1):
        if bit == '?' or key2[i] == '?':
            doubt_counter += 1
        else:
            bit_counter += 1
            if bit != key2[i]:
                ber += 1
            
    print('*** Unknown bit rate: ' + str(doubt_counter / len(key1)))
            
    return(100 * (ber / bit_counter))

def quantize_slice(data):
    key = ""
    random.seed(42)
    #random.shuffle(data)
    sigma = np.mean(data)
    nu = np.std(data)
    thold = THOLD_RATIO * nu
    centered_data = [x - sigma for x in data]
    for idx,val in enumerate(centered_data):
        nu = np.std(centered_data[idx:])
        thold = THOLD_RATIO * nu
        # if val < 0:
        #     key += "0"
        # else:
        #     key += "1"
        # if abs(val) < thold:
        #     key += "0"
        # else:
        #     key += "1"
        if val > thold:
            key += '1'
        elif val < -thold:
            key += '0'
        else:
            key += '?'
    return(key)

def quantize(data):
    idx_start = 0
    idx_end = SLICE_LENGTH
    key = ""

    while idx_start < len(data):
        if idx_end > len(data):
            idx_end = len(data)
        key_chunk = quantize_slice(data[idx_start:idx_end])
        idx_start += SLICE_LENGTH
        idx_end += SLICE_LENGTH
        key_chunk += " \ "
        key += key_chunk
    return(key)

def quantize_2(data):
    key = ""
    random.seed(42)
    #random.shuffle(data)
    sigma = np.mean(data)
    nu = np.std(data)
    thold = THOLD_RATIO * nu
    centered_data = [x - sigma for x in data]
    for idx,val in enumerate(centered_data):
        nu = np.std(centered_data[idx:])
        thold = THOLD_RATIO * nu
        guard = GUARD_RATIO * nu
        if val > (thold + guard):
            key += '11'
        elif val < -(thold + guard):
            key += '00'
        elif (val > guard) and (val < thold - guard ):
            key += '10'
        elif (val < - guard) and (val > - (thold - guard)):
            key += '01'
        else:
            key += '??'
    return(key)


def process_data(data):
    print("*** Vector length: " + str(len(data)))
    sigma = np.mean(data)
    nu = np.std(data)
    print("*** Standard deviation:" + str(nu))
    kurtosis = compute_kurtosis(nu,sigma)
    print("*** Kurtosis: " + str(kurtosis))
    
    # 1- median
    #processed_data = median_filter(data)
    processed_data = data
    
    # 2 - center
    processed_data = [val - sigma for val in processed_data]
        

    # 3 - sliding window
    #processed_data = sliding_mean_filter(processed_data)
    processed_data = mean_median_filter(processed_data)

    # 4 - HPF
    if HPF:
        processed_data = apply_hpf(processed_data)



    return(processed_data)

    




if __name__ == "__main__":
    mean_length = 10
    parseFile()
    
    print("*** LoS indicator:" + str(np.mean(cbke_vectors["$"][0])))
    #print(compute_pdf(cbke_vectors["#"][0]))
    if len(sys.argv) > 1:
        if len(sys.argv) == 3:
            arg = sys.argv[1]
            if arg == 'fp':
                arg = '^'
            mean_length = int(sys.argv[2])
        plot(arg)

    else:
        plot("^")


