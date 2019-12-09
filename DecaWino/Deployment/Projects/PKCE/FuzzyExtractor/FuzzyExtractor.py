import math
import os

reference_signature = 'References/signature_COM17.txt'
current_signature_dir = 'Challenges'
MAX_SKEW_DISTANCE = 2
DISTANCE_PER_SAMPLE = 32

# taking the first file in signatures dir
current_signature = current_signature_dir + '/' + os.listdir(current_signature_dir).pop()

def extract_sig(file):
    data = []
    with open(file, 'r') as f:
        for line in f:
            data += [x for x in line.split("|") if x != '\n']
    print(data)
    return(data)


def shift(sig,sig_ref, max_step):
    success = True
    print("Shifting vector")
    for shift_idx,val in enumerate(sig_ref):
        if abs(int(val) - int(sig[0])) <= max_step:
            break;
    else:
        success = False
    print("Index of first value after shifting: " + str(shift_idx) + " for step: " + str(max_step))
    return(success, shift_idx)



def compare_sig(sig, sig_ref):
    step = 0
    ret = False
    while not(ret):
        ret, shift_idx = shift(sig, sig_ref, step)
        step += 1


    # calculating euclidean distance
    euclidean_distance = 0
    for idx,val in enumerate([int(x) for x in sig]):
        euclidean_distance += pow(val - int(sig_ref[idx + shift_idx]), 2)
    euclidean_distance = math.sqrt(euclidean_distance/idx)

    print("Values iterated: " + str(idx))
    print("Euclidean distance: " + str(euclidean_distance))
    return(euclidean_distance)






if __name__== "__main__":

    sig_ref = extract_sig(reference_signature)
    sig = extract_sig(current_signature)
    compare_sig(sig,sig_ref)
