import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys
import math
import random
import scipy.stats
import scipy.fftpack
from scipy.signal import butter, lfilter, freqz
from scipy import ndimage
from scipy.stats.stats import pearsonr
from scipy.stats import chi2_contingency
from sklearn.metrics import mutual_info_score
from sklearn.feature_selection import mutual_info_classif
import mutual_information as mi


plt.style.use('C:/Users/pestourb/Documents/Plateforme src/matplotlib-master/lib/matplotlib/mpl-data/stylelib/custom.mplstyle')
font = {'fontname':'Century Gothic', 'size' : 16}

parameters = ['#', '^', '*', '$']
parameters_pulse = ['_', '&']
colors = ['black', 'green']

in_file = 'CBKE_log_final.txt'
THOLD_RATIO = 0.67448 # for a normal distribution
THOLD_RATIO = 0.5
GUARD_RATIO = 0.16


EPS = np.finfo(float).eps

## frequency filtering
HPF = True
LC = 10 # low pass filter cut frequency
HC = 500 # high pass filter cut frequency
FS = 800
FREQ_UNIT = FS / 2

SLICE_LENGTH = 1000
DISABLE_MATPLOT = 0
cbke_vectors = {}
Z = 1.96 # constant for confidence interval 5%
key = []


for p in parameters:
    cbke_vectors[p] = []
for p in parameters_pulse:
    cbke_vectors[p] = []



def parseFile():
    global key
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
            
            elif p in parameters_pulse:
                cbke_vector = cbke_vectors[p]
                pulses = line[1:].split('|')
                data = []
                for pulse in pulses:
                    sample_str = pulse.split(';')
                    sample = []
                    for str_val in sample_str:
                        try:                   
                            val = float(str_val)
                            sample.append(val)
                        except:
                            pass
                    data.append(sample)
                cbke_vector.append(data)
            elif p == '/':
                key.append(line[1:])


def compute_msd(v1, v2):
    v_diff = []
    for i, val in enumerate(v1):
        v_diff.append(pow(val - v2[i],2))
    return(math.sqrt(np.mean(v_diff)))

def analyze_pulses():
    N = len(cbke_vectors['_'][0])
    idx1 = []
    idx2 = []
    # aligned1 = peak_alignment(cbke_vectors['_'][0])
    # aligned2 = peak_alignment(cbke_vectors['_'][1])
    aligned1 = cbke_vectors['_'][0]
    aligned2 = cbke_vectors['_'][1]
    #print(aligned
    cut_idx = 64
    for i in range(N):
        # print(aligned1[i])
        # print(aligned2[i])
        idx1 += aligned1[i][:cut_idx]
        idx2 += aligned2[i][:cut_idx]
        # idx1 += aligned2[i]
        # idx2 += aligned2[i + N //2]


    nu = np.mean(idx1)
    sigma = np.std(idx1)
    nu2 = np.mean(idx2)
    sigma2 = np.std(idx2)
    bins = int(math.sqrt(len(idx1)/5))
    #bins = 60
    
    rand_var = []
    rand_var2 = []
    for j in range(len(idx1)):
        rand_var.append(random.gauss(nu, sigma))
        #rand_var2.append(random.gauss(nu2, sigma2))

    mi = mutual_information_2d(idx1, idx2)
    mi_rand = mutual_information_2d(idx1, rand_var)
    mi_rand2 = calc_MI(rand_var,idx2, bins )
    print("*** length:" + str(len(idx1)))
    # print("*** Pulses mutual information (Method 1): " + str(mi) + " ***")
    # print("*** Pulses mutual information with random distrib: " + str(mi_rand) + " ***")
    print("*** Mean / STD: " + str(nu) + "/" + str(sigma))
    pearson, collision_proba = pearsonr(idx1,idx2)
    print("*** Pearson: " + str(pearson))
    print("Collision probability: " + str(collision_proba))
    print("*** Pulses mutual information (Method 2): " + str(calc_MI(idx1,idx2, bins)) + " ***")
    print("*** Pulses mutual information with random distrib (Method 2): " + str(mi_rand2) + " ***")
    print("*** Mean-squared difference:" + str(compute_msd(idx1,idx2)))
    print("*** Mean-squared difference with random distrib:" + str(compute_msd(idx1,rand_var)))

    plt.show()

def plot_pulses():
    fig = plt.figure()
    axe = fig.add_subplot(111)
    #peak_alignment(cbke_vectors['_'][0])
    nb_plots = 4
    for i in range(nb_plots):
        idx = peak_detection(cbke_vectors['_'][0][i])
        idx2 = peak_detection(cbke_vectors['_'][1][i])
        x_val = range(len(cbke_vectors['_'][0][i]))
        if i == nb_plots - 1:
            axe.plot(cbke_vectors['_'][0][i], c = '#33cccc', marker = '^', label = 'Alice')
            axe.plot(cbke_vectors['_'][1][i], c = '#ff6666', marker = '^', label = 'Bob')
        else:
            axe.plot(cbke_vectors['_'][0][i], c = '#33cccc', marker = '^')
            axe.plot(cbke_vectors['_'][1][i], c = '#ff6666', marker = '^')            
        axe.set_xlabel('CIR tap index', **font)
        axe.set_ylabel('Magnitude', **font)
        axe.legend()
        
        print("Number of peaks: " + str(len(idx)))
        plt.grid()
        plt.pause(1)
        plt.cla()
        #axe2.plot(cbke_vectors['_'][1][i])

    
    #plt.show()

def peak_detection(data):
    diff1 = np.diff(data)
    nu = np.mean(diff1)
    sigma = np.std(diff1)
    idx = []
    for i,val in enumerate(diff1):
        if val > nu + sigma:
            idx.append(i + 1)
    return(idx)

def peak_alignment(data_list):
    filtered_data = []
    for data in data_list:
        idx = peak_detection(data)
        if len(idx) > 0:
            first_peak = idx[0]
            shift = first_peak - 1 # first peak is defaulted to first tap
            del data[:shift]
            for i in range(shift):
                # appending dummy values for length preservation
                data.append(0)
        filtered_data.append(data)
    return(filtered_data)


def mutual_information_2d(x, y, sigma=1, normalized=False):
    """
    Computes (normalized) mutual information between two 1D variate from a
    joint histogram.
    Parameters
    ----------
    x : 1D array
        first variable
    y : 1D array
        second variable
    sigma: float
        sigma for Gaussian smoothing of the joint histogram
    Returns
    -------
    nmi: float
        the computed similariy measure
    """
    bins = (256, 256)

    jh = np.histogram2d(x, y, bins=bins)[0]

    # smooth the jh with a gaussian filter of given sigma
    ndimage.gaussian_filter(jh, sigma=sigma, mode='constant', output=jh)

    # compute marginal histograms
    jh = jh + EPS
    sh = np.sum(jh)
    jh = jh / sh
    s1 = np.sum(jh, axis=0).reshape((-1, jh.shape[0]))
    s2 = np.sum(jh, axis=1).reshape((jh.shape[1], -1))

    # Normalised Mutual Information of:
    # Studholme,  jhill & jhawkes (1998).
    # "A normalized entropy measure of 3-D medical image alignment".
    # in Proc. Medical Imaging 1998, vol. 3338, San Diego, CA, pp. 132-143.
    if normalized:
        mi = ((np.sum(s1 * np.log(s1)) + np.sum(s2 * np.log(s2))) /
              np.sum(jh * np.log(jh))) - 1
    else:
        mi = (np.sum(jh * np.log(jh)) - np.sum(s1 * np.log(s1)) -
              np.sum(s2 * np.log(s2)))

    return (mi / math.log(2))

def calc_MI(X,Y,bins):

   c_XY = np.histogram2d(X,Y,bins)[0]
   
   hist_X = np.histogram(X,bins)
   c_X = hist_X[0]
   bins = hist_X[1]
    
   c_Y = np.histogram(Y,bins)[0]
#    print(c_X)
#    print(bins)
   #print(c_Y)
   H_X = shan_entropy(c_X)
   H_Y = shan_entropy(c_Y)
   H_XY = shan_entropy(c_XY)

   MI = H_X + H_Y - H_XY
   return MI

def shan_entropy(c):
    c_normalized = c / float(np.sum(c))
    c_normalized = c_normalized[np.nonzero(c_normalized)]
    H = -sum(c_normalized* np.log2(c_normalized))  
    return H

            
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
        #decile_idx = mean_length // mean_length
        decile_idx = 1
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
    decile_idx = len(sorted_data) // 10
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
    bin_size = nu / 80
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
    frequencies = [n * (FREQ_UNIT/(2 * N)) for n in range(N)]
    return(frequencies, transfo)


def apply_hpf(data):
    order = 2
    cutoff = 5 * LC
    fs = FS
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    filtered =lfilter(b, a, data)
    # hpf = scipy.signal.butter(2, 20, 'highpass', fs=800, output='sos')
    # #lpf = scipy.signal.butter(10, HC, 'lp', fs=1600, output='sos')
    # filtered = scipy.signal.sosfilt(hpf, data)
    #filtered = scipy.signal.sosfilt(lpf, filtered)
    return(filtered)

def compute_confidence_interval(data):
    N = len(data)
    intervals = []
    intervals_opposite = []
    for d in range(N - 4):
        threshold = Z / math.sqrt(N - d)
        intervals.append(threshold)
        intervals_opposite.append(-threshold)
    #print("*** Confidence interval 5% at lag 10: " + str(intervals[9]))
    return(intervals, intervals_opposite)

def convert_key(key):
    converted_key = ""
    i = 0
    while (i < len(key)):
        if key[i:i+2] == '00':
            char = 'A'
        if key[i:i+2] == '01':
            char = 'B'
        if key[i:i+2] == '10':
            char = 'C'
        if key[i:i+2] == '11':
            char = 'D'
        i += 2
        converted_key += char
    return(converted_key)




def compare_keys(key1, key2):
    #one_counter = 0
    err_counter = 0
    one_counter = 0
    a_counter = 0
    b_counter = 0
    c_counter = 0
    d_counter = 0
    for i, c in enumerate(key1):
        if c == '1':
            one_counter += 1
        if c != key2[i]:
            err_counter +=1
    print("BER:" + str(err_counter / len(key1)))
    print("Bit balance" + str(one_counter / len(key1)))
    err_counter = 0

    key1 = convert_key(key1)
    key2 = convert_key(key2)
    for i, c in enumerate(key1):
        # if c == '1':
        #     one_counter += 1
        if c == 'A':
            a_counter += 1
        if c == 'B':
            b_counter += 1
        if c == 'C':
            c_counter += 1
        if c == 'D':
            d_counter += 1
        if c != key2[i]:
            err_counter += 1
    print(key1)
    print(key2)
    #print("bit balance:" + str(one_counter / len(key1)))
    n = len(key1)
    print("Balance:" + str(a_counter / n) + "; " + str(b_counter/n) + "; " + str(c_counter / n) + "; " + str(d_counter /n) + "; ")

    return(err_counter / len(key1))


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
    d1, d2 = truncate(cbke_vectors[param][0], cbke_vectors[param][1])
    
    #for i,data in enumerate(cbke_vectors[param]):      
    for i,data in enumerate([d1, d2]):  
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
    low_cut = 0
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
    if (bit_counter > 0):   
        return(100 * (ber / bit_counter))
    else:
        return(0)

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

def skip(data, acc_length,gap_length):
    ctr = 0
    skip = False
    output = []
    for val in data:
        if ctr == acc_length:
            skip = True
        if ctr == acc_length + gap_length:
            ctr = 0
            skip = False
        if not(skip):
            output.append(val)
        ctr += 1
    return(output)


def truncate(data1, data2):
    nu1 = np.mean(data1)
    sigma1 = np.std(data1)
    nu2 = np.mean(data2)
    sigma2 = np.std(data2)
    m = 1.67
    out1 = []
    out2 = []

    for i, val1 in enumerate(data1):
        val2 = data2[i]
        if (val1 > nu1 - m * sigma1 ) and (val1 < nu1 + m * sigma1) and (val2 > nu2 - m * sigma2) and (val2 < nu2 + m * sigma2):
            out1.append(val1)
            out2.append(val2)
    return(out1, out2)





def process_data(data):
    print("*** Vector length: " + str(len(data)))
    sigma = np.mean(data)
    nu = np.std(data)
    print("*** Standard deviation:" + str(nu))
    kurtosis = compute_kurtosis(nu,sigma)
    print("*** Kurtosis: " + str(kurtosis))

    # 2 - center
    #processed_data = median_filter(data)
    # processed_data = truncate(data)

    processed_data = data
    processed_data = center(processed_data)
    # 4 - HPF
    if HPF:
        processed_data = apply_hpf(processed_data)
    #processed_data = data
    
    #processed_data = processed_data[100:]
    #processed_data = skip(processed_data, mean_length, 6)
    # 1- median
    #processed_data = median_filter(data)
    #processed_data = data

    print("length processed data" + str(len(processed_data)))
       
    # 3 - sliding window
    #processed_data = sliding_mean_filter(processed_data)
    # while (len(processed_data) % 4 != 0):
    #     processed_data.append(0)
    #processed_data = mean_median_filter(processed_data)
    #print("len after mean" + str(processed_data))
    #processed_data = mean_filter(processed_data)

    





    return(processed_data)



def test_MI(N, nu, sigma):
    var1 = []
    var2 = []
    
    random.seed()
    for i in range(N):
        var1.append(random.gauss(nu, sigma))

    random.seed()
    for i in range(N):
        var2.append(random.gauss(nu, sigma))
    
    print("*** MI method1:" + str(calc_MI(var1,var2, int(math.sqrt(N/6)))))
    array1 = np.array(var1)
    array1 = np.reshape(array1, [-1, 1])
    array2 = np.array(var2)
    array2 = np.reshape(array2, [-1, 1])
    # array2.reshape(-1, 1)
    #array1 = np.random.randn(100,1)
    #array2 = np.random.randn(100,1)
    
    print("*** Test MI:" + str(mi.mutual_information([array1, array2], k = 8)))

def curate_data(data):
    nu = np.mean(data)
    sigma = np.std(data)
    out = []
    for val in data:
        if val < (nu + 2 * sigma) and val > (nu - 2 * sigma):
            out.append(val)
    return(out)

def compute_MI(a,b):
    # a2 = curate_data(a)
    # b2 = curate_data(b)

    # fig = plt.figure()
    # axe = fig.add_subplot(111)
    # axe.plot(a2)
    # axe.plot(b2)
    # plt.show()

    # slice_lgth = 100
    # n = len(a) // slice_lgth
    # for i in range(n):
    #     idx = i * slice_lgth
    #     chunk_a = a[idx:idx+slice_lgth]
    #     chunk_b = b[idx:idx+slice_lgth]
    #     chunk_a2 = curate_data(chunk_a)
    #     chunk_b2 = curate_data(chunk_b)
    #     print("MI " + str(calc_MI(chunk_a2, chunk_b2, int(math.sqrt(len(chunk_a2))))))


    array1 = np.array(a)
    array2 = np.array(b)
    array1 = np.reshape(array1, (-1,1))
    array2 = np.reshape(array2, (-1,1))
    print(array1)
    print("*** Compute MI:" + str(mi.mutual_information([array1, array2], k = 1)))


if __name__ == "__main__":
    mean_length = 4

    parseFile()
    

    print("*** LoS indicator:" + str(np.mean(cbke_vectors["$"][0])))
    print("*** SNR: " + str(np.mean(cbke_vectors["*"][0])))

    
    #print(compute_pdf(cbke_vectors["#"][0]))
    # analyze_pulses()
    # plot_pulses()
    print(compare_keys(key[0], key[1]))
    plot_pulses()
    # if len(sys.argv) > 1:
    #     if len(sys.argv) == 3:
    #         arg = sys.argv[1]
    #         if arg == 'fp':
    #             arg = '^'
    #         mean_length = int(sys.argv[2])
    #     a =  cbke_vectors[arg][0]
    #     b =  cbke_vectors[arg][1]
    #     bins = 20
    #     print("*** Mutual Information: " + str(calc_MI(a,b, bins)))
    #     sigma = np.std(a)
        
    #     #compute_MI(a,b)
    #     #test_MI(100, 0, 10)
        
    #     plot(arg)
 
    # else:
    #     plot("^")


