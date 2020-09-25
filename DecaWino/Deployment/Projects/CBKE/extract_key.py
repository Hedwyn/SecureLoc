import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys
import math
from process_data import calc_MI, compute_confidence_interval
from scipy.stats.stats import pearsonr
import keyboard
import random

plt.style.use('C:/Users/pestourb/Documents/Plateforme src/matplotlib-master/lib/matplotlib/mpl-data/stylelib/custom.mplstyle')
font = {'fontname':'Century Gothic', 'size' : 16}
in_file = 'CBKE_log_final.txt'

NB_REF_POINTS = 10
GAUSSIAN_MID_RATIO = 0.667
GUARD_MARGIN_RATIO = 0.2
MEDIAN_SIZE = 3
OFFSET_CROSSCOR = 0


def parseFile(file):
    pulses_list = []
    key_list = []
    with open(file) as f:
        for line in f:
            p = line[0]           
            if p == '_':        
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
                    if sample:
                        data.append(sample)
                
                pulses_list.append(data)
            elif p == '/':
                key_list.append(line[1:-1])
    return(pulses_list, key_list)


def plot_pulses(pulses):
    fig = plt.figure()
    axe = fig.add_subplot(111)
    
    for i in range(NB_REF_POINTS):
        if i == NB_REF_POINTS - 1:
            axe.plot(pulses[0][i], c = '#33cccc', marker = '^', label = 'Alice')
            axe.plot(pulses[1][i], c = '#ff6666', marker = '^', label = 'Bob')
        else:
            axe.plot(pulses[0][i], c = '#33cccc', marker = '^')
            axe.plot(pulses[1][i], c = '#ff6666', marker = '^')            
        axe.set_xlabel('CIR tap index', **font)
        axe.set_ylabel('Magnitude', **font)

        plt.grid()
        plt.pause(10)
        plt.cla()

def median_filter(data, size):
    buffer = []
    filtered_data = []
    for i,val in enumerate(data):
        buffer.append(val)
        if (len(buffer) == size) or (i == len(data) - 1 ):
            median = np.median(buffer)
            filtered_data.append(median)
            buffer = []
    return(filtered_data)

def center(data):
    mean = np.mean(data)
    return([val - mean for val in data])

def moving_average(data, window_length):
    ma = 0
    filtered_data = []
    for i,val in enumerate(data):
        if i < window_length:
            ma *= i
            ma += val
            ma /= (i + 1)
        else:
            ma += (val - data[i - window_length]) / window_length
        filtered_data.append(val - ma)
    return(filtered_data)



def process_pulses(pulses):
    """applies all needed filtering on given pulses"""
    processed_pulses = []
    for pulse in pulses:
        processed_pulse = []
        for chunk in pulse:
            processed_chunk = center(median_filter(chunk, MEDIAN_SIZE))
            processed_pulse.append(processed_chunk)
        processed_pulses.append(processed_pulse)
    return(processed_pulses)


def quantize(pulse):
    key = ""
    key_chunk = ""
    for chunk in pulse:       
        # processing data
        processed_chunk = center(median_filter(chunk, MEDIAN_SIZE))
        # processed_chunk = median_filter(moving_average(chunk, 16), MEDIAN_SIZE)[16:]
        std = np.std(processed_chunk)
        threshold = GAUSSIAN_MID_RATIO * std
        guard_margin = GUARD_MARGIN_RATIO * std
        # quantizing
        for sample in processed_chunk:
            if sample > guard_margin:
                if abs(sample) > (threshold + guard_margin):
                    key_chunk += "11"
                    # key_chunk += "1"
                elif abs(sample) < (threshold - guard_margin):
                    key_chunk += "10"
                    # key_chunk += "1"
                else:
                    key_chunk += "1?"
                    # key_chunk += "?"
            elif sample < -guard_margin:
                if abs(sample) > (threshold + guard_margin):
                    key_chunk += "00"
                    # key_chunk += "0"
                elif abs(sample) < (threshold - guard_margin):
                    # key_chunk += "0"
                    key_chunk += "01"
                else:
                    key_chunk += "0?"
                    # key_chunk += "?"
            else:
                # the guard margin should be inferior to the threshold
                key_chunk += "??"
                # key_chunk += "?"
               
        key += key_chunk
        key_chunk = ""
    return(key)

def gen_random_key(length):
    key = ""
    while len(key) < length:
        key += str(random.randint(0,1))
    return(key)

def alt_quantize(pulse):
    key = ""
    key_chunk = ""
    for chunk_idx,chunk in enumerate(pulse):   
        # processing data
        processed_chunk = center(median_filter(chunk, MEDIAN_SIZE))
        random.seed(chunk_idx)
        # the permutation should have an even length; if chunk has an odd length, substracting one
        perm_len = 2 * (len(processed_chunk) // 2)
        perm = [i for i in range(perm_len)]
        random.shuffle(perm)
        # processed_chunk = median_filter(moving_average(chunk, 16), MEDIAN_SIZE)[16:]
        std = np.std(processed_chunk)
        guard_margin = GUARD_MARGIN_RATIO * std    
        i = 0
        while i < len(perm) - 1:
            prev_sample = processed_chunk[perm[i]]
            sample = processed_chunk[perm[i + 1]]
            if sample > (prev_sample + guard_margin):
                key_chunk += "1"
            elif sample < (prev_sample - guard_margin):
                key_chunk += "0"
            else:
                key_chunk += "?"
            i += 2
        key += key_chunk
        key_chunk = ""
    return(key)


def convert_key(key):
    converted_key = ""
    i = 0
    while (i < len(key)):
        if key[i:i+2] == '00':
            char = 'A'
        elif key[i:i+2] == '01':
            char = 'B'
        elif key[i:i+2] == '10':
            char = 'C'
        elif key[i:i+2] == '11':
            char = 'D'
        else:
            char = '?'
        
        i += 2
        converted_key += char
    return(converted_key)

def compute_character_repetition_rate(key):
    """Computes the probability that a character in the key is the same as the previous one"""
    repetition_counter = 0
    known_bits = [c for c in key if c != '?']
    print("** Key length:" + str(len(known_bits)))
    prev = known_bits[0]
    for char in known_bits[1:]:        
        if char == prev:
            repetition_counter += 1
        prev = char
    return(repetition_counter /  len(known_bits))

def compare_keys(key1, key2):
    err_counter = 0
    one_counter = 0
    unknown_counter = 0
    occurence_counter = {'A': 0,'B': 0, 'C': 0, 'D': 0, '?':0}

    # Computing BER and bit balance
    for i, c in enumerate(key1):
        if c == '1':
            one_counter += 1
        if c == '?' or key2[i] == '?':
            unknown_counter += 1
        elif c != key2[i]:
            err_counter += 1
    
    unknown_rate = unknown_counter / len(key1)
    ber = err_counter / len(key1)
    ber = ber / (1 - unknown_rate)
    print("BER:" + str(ber))
    print("Unknown rate:" + str(unknown_rate))
    print("Bit balance: " + str(one_counter / (len(key1) - unknown_counter)))
    err_counter = 0

    # converting binary to a 4-chracter alphabet {A,B,C,D}
    key1 = convert_key(key1)
    key2 = convert_key(key2)

    # computing frequency of each character
    for c in key1:
        occurence_counter[c] += 1

    for char in occurence_counter:
        # computing proportion 
        occurence_counter[char] /= len(key1)
        # converting to a %
        occurence_counter[char] *= 100

    # displaying keys
    print("Alice's key: " + str(key1))
    print("Bob's key: " + str(key2))

    # displaying each character's frequency

    print("Character balance:")
    print("00 (A):" + str(occurence_counter['A']) + "%")
    print("01 (B):" + str(occurence_counter['B']) + "%")
    print("10 (C):" + str(occurence_counter['C']) + "%")
    print("11 (D):" + str(occurence_counter['D']) + "%")
    print("?? (?):" + str(occurence_counter['?']) + "%")

def compute_ber(key1, key2):
    err_ctr = 0
    unknown_ctr = 0
    for b1,b2 in zip(key1, key2):
        if b1 == '?' or b2 == '?':
            unknown_ctr += 1
        elif b1 != b2:
            err_ctr += 1
    return(err_ctr / (len(key1) - unknown_ctr))

def plot_ber(key1, key2, chunk_length):
    fig_ber = plt.figure()
    axe_ber = fig_ber.add_subplot(111)
    ber = []
    i = 0
    j = chunk_length * 2
    while i < len(key1):
        slice1 = key1[i:j]
        slice2 = key2[i:j] 
        ber.append(compute_ber(slice1, slice2))
        i += chunk_length * 2
        j += chunk_length * 2
    axe_ber.plot(ber, c = '#33cccc', marker = '^')
    plt.show()


def unpack(pulse):
    return([sample for sublist in pulse for sample in sublist])

def get_ideal_bin_number(data):
    return(1 + int(math.sqrt(len(data))))

def compute_autocor(data):
    # normalizing by the length
    a = (data - np.mean(data)) / (np.std(data) * len(data))
    a_delayed = (data - np.mean(data)) / (np.std(data))
    autocor = np.correlate(a, a_delayed, 'full')
    return(autocor[(len(autocor) // 2):])

def compute_crosscor(data1, data2):
    a = (data1 - np.mean(data1)) / (np.std(data1) * len(data1))
    b = (data2 - np.mean(data2)) / (np.std(data2))
    crosscor = np.correlate(a, b, 'full')
    return(crosscor[(len(crosscor) // 2):]) 

def analyze_crosscor(pulse):
    for i, rp1 in enumerate(pulse[OFFSET_CROSSCOR:]):
        for j, rp2 in enumerate(pulse[i + 1:]):
            crosscor = compute_crosscor(rp1, rp2)
            print("*Cross-correlation at index " + str(i) +";" + str(j + i + 1) + ": " + str(max(crosscor)))




def compute_mutual_information(alice, bob):
    # index of current reference point
    idx = 1
    # calculating mutual information for each reference point (rp)
    print("*** Individual results for each reference point: ")
    for rp_alice, rp_bob in zip(alice,bob):
        # computing ideal bin number for mutual information calculation
        bins = get_ideal_bin_number(rp_alice)
        mi = calc_MI(rp_alice, rp_bob, bins)
        pearson_coeff = pearsonr(rp_alice, rp_bob)[0]
        mean_alice = np.mean(rp_alice)
        mean_bob = np.mean(rp_bob)
        std_alice = abs(np.std(rp_alice) / mean_alice)
        std_bob = abs(np.std(rp_bob) / mean_bob)
        print("\n** Reference point " + str(idx))
        print("Mutual Information: " + str(mi) + "bits")
        print("Pearson: " + str(pearson_coeff))
        print("Standard deviation Alice: " + str(std_alice) + " Bob: " + str(std_bob))        
        idx += 1

    print("\n*** Overall results: ")
    flat_alice = unpack(alice)
    flat_bob = unpack(bob)
    bins = get_ideal_bin_number(flat_alice)
    mi = calc_MI(flat_alice, flat_bob, bins)
    pearson_coeff = pearsonr(flat_alice, flat_bob)[0]
    print("Mutual Information: " + str(mi) + "bits")
    print("Pearson: " + str(pearson_coeff))         

def plot_mi_vs_std(pulses):
    fig_mi = plt.figure()
    axe_mi = fig_mi.add_subplot(111)
    axe_std = axe_mi.twinx()
    alice = pulses[0]
    bob = pulses[1]
    mi = []
    std = []

    for rp_alice, rp_bob in zip(alice,bob):
        # computing ideal bin number for mutual information calculation
        bins = get_ideal_bin_number(rp_alice)
        mi_rp = calc_MI(rp_alice, rp_bob, bins)
        std_rp = np.std(rp_alice)
        mean_rp = np.mean(rp_alice)
        norm_std = pow(std_rp / mean_rp, 1)
        mi.append(mi_rp)
        std.append(norm_std)

    axe_mi.plot(mi, c = '#33cccc', marker = '^', label = 'Mutual Information')
    axe_std.plot(std, c = '#ff6666', marker = '^', label = 'Standard deviation') 
    axe_mi.set_xlabel('Delay', **font)
    axe_mi.set_ylabel('Mutual Information (bits)', **font)  
    plt.grid()
    plt.show()
    

def plot_autocor(pulses):
    fig_autocor = plt.figure()
    axe_autocor = fig_autocor.add_subplot(111)
    for alice, bob in zip(pulses[0], pulses[1]):
        # computing autocorrelation for the current reference point
        autocor_alice = compute_autocor(alice)
        autocor_bob = compute_autocor(bob)

        # computing boundaries for 95% confidence interval
        confidence_interval_low, confidence_interval_high = compute_confidence_interval(alice)

        # displaying autocorrelation curve
        axe_autocor.plot(autocor_alice, c = '#33cccc', marker = '^', label = 'Alice')
        axe_autocor.plot(autocor_bob, c = '#ff6666', marker = '^', label = 'Bob')

        # plotting 95% confidence interval limit in black
        axe_autocor.plot(confidence_interval_low, 'black')
        axe_autocor.plot(confidence_interval_high, 'black')
        plt.grid()
        plt.pause(3)
        plt.cla()

def plot_crosscor(pulse):
    fig_crosscor = plt.figure()
    axe_crosscor = fig_crosscor.add_subplot(111)
    highest_cor = []
    for i,rp1 in enumerate(pulse):
        highest_cor = []
        highest_random_cor = []
        for rp2 in pulse[i+ 1:]:
            crosscor = compute_crosscor(rp1, rp2)
            # highest_cor.append(max(crosscor))
            highest_cor.append(crosscor[0])
            random_cross_cor = compute_crosscor(rp1, [random.gauss(np.mean(rp1), np.std(rp1)) for i in range(len(rp1))])
            # highest_random_cor.append(max(random_cross_cor))
            highest_random_cor.append(random_cross_cor[0])
        threshold = [(1.414 / (math.sqrt(len(rp1)))) for i in range(len(highest_cor))]
        threshold_neg = [-val for val in threshold]
        axe_crosscor.plot(highest_cor, c = '#33cccc', marker = '^', label = 'Cross-correlation')
        axe_crosscor.plot(highest_random_cor, c = '#ff6666', marker = '^', label = 'Cross-correlation random function')
        axe_crosscor.plot(threshold, c = 'red', marker = '^', label = 'Significance threshold')
        axe_crosscor.plot(threshold_neg, c = 'red', marker = '^', label = 'Significance threshold')
        axe_crosscor.legend()
        plt.grid()
        plt.pause(3)
        plt.cla()


def compute_pdf(data):
    nb_bins = get_ideal_bin_number(data) 
    hist, bins = np.histogram(data, nb_bins)
    return(hist,bins)

def plot_pdf(pulse):
    fig_pdf = plt.figure()
    axe_pdf = fig_pdf.add_subplot(111)
    flat_pulse = unpack(pulse)
    pdf, bins = compute_pdf(flat_pulse)
    bin_centers = bins[1:]
    axe_pdf.plot(bin_centers, pdf, c = '#33cccc', marker = '^', label = 'Probability Density Function')
    plt.grid()
    plt.show()
    
def analyze_pulses(pulses):
    names = ['Alice', 'Bob']
    for pulse, name in zip(pulses, names):
        flat_pulse = unpack(pulse)
        print("Mean " + name + ": " + str(np.mean(flat_pulse)))
        print("Standard deviation " + name + ": " + str(np.std(flat_pulse)))


if __name__ =="__main__":
    pulses, keys = parseFile(in_file)
    # compare_keys(keys[0], keys[1])
    #analyze_pulses(pulses)
    # compute_mutual_information(pulses[0], pulses[1])
    # plot_all(pulses)s
    processed_pulses = process_pulses(pulses)
    key1 = alt_quantize(pulses[0])
    key2 = alt_quantize(pulses[1])

    # print(compute_ber(key1, key2))

    compare_keys(key1, key2)
    # plot_ber(key1, key2, 10)
    # analyze_crosscor(pulses[0])
    # plot_mi_vs_std(pulses)
    # plot_crosscor(pulses[1])
    # plot_pdf(pulses[0])
    # plot_pulses(processed_pulses)
    # plot_mi_vs_std(pulses)
    # plot_autocor(pulses)
    plot_pulses(processed_pulses)

    print(compute_character_repetition_rate(key1))
    # print(compute_character_repetition_rate(convert_key(keys[0])))



    