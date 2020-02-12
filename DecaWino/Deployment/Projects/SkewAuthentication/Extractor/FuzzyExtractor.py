import math
import os
import matplotlib.pyplot as plt

reference_signature = 'References/signature_COM17.txt'
#reference_signature = 'References/COM17/S3_afaic_nlos_128.txt'
current_signature_dir = 'Challenges'
MAX_STEP = 0.2
DISTANCE_PER_SAMPLE = 32
MIN_THRESHOLD = 500
MIN_THRESHOLD = 1500

# taking the first file in signatures dir
current_signature = current_signature_dir + '/' + os.listdir(current_signature_dir).pop()

def extract_sig(file):
    signatures = []
    data = []
    with open(file, 'r') as f:
        for line in f:
            if line == '\n' and data:
                signatures.append(data.copy())
                data = []
            else:
                str_data = [x for x in line.split("|") if x != '\n' ]
                float_data = []
                for str in str_data:
                    try:
                        float_data.append(float(str))
                    except:
                        print("Malformed flaot value")
                data += float_data
    if data:
        signatures.append(data.copy())
    return(signatures)

def shrink_signature(signature, sample_size):
    """shrinks down the length of signature by sample_size."""
    idx = 0
    sum = 0
    shrinked_signature = []
    for val in signature:
        if idx == sample_size:
            shrinked_signature.append(sum/sample_size)
            idx = 0
            sum = 0
        else:
            idx +=1
            sum += val

    return(shrinked_signature)



def display_signature(signature):
    # creating figure
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(signature[:])
    plt.show()


def filter_signature(signature):
    """eliminates failed values from signature"""
    return([x for x in signature if (x > MIN_THRESHOLD) and (x < MAX_THRESHOLD)])


def truncate_first_values(sig,lgth):
    if (len(sig) > lgth):
        return(sig[lgth:])
    else:
        print("Cannot truncate - signature is too short")




def shift(sig,sig_ref, max_step):
    success = True
    print("Shifting vector")
    for shift_idx,val in enumerate(sig_ref):
        if abs(val - sig[0]) <= max_step:
            break;
    else:
        success = False
    print("Index of first value after shifting: " + str(shift_idx) + " for step: " + str(max_step))
    return(success, shift_idx)



def compare_sig(sig, sig_ref):
    step = 0
    ret = False
    while not(ret) and (step < MAX_STEP):
        ret, shift_idx = shift(sig, sig_ref, step)
        step += 0.01


    # calculating euclidean distance
    euclidean_distance = 0
    errors = []
    for idx,val in enumerate([x for x in sig]):
        if (idx + shift_idx) >= len(sig_ref):
            break
        error = pow(val - sig_ref[idx + shift_idx], 2)
        errors.append(error)
        euclidean_distance += error



    #euclidean_distance = math.sqrt(euclidean_distance/idx)
    euclidean_distance = errors[int(len(errors)/ 2)]

    print("Values iterated: " + str(idx))
    print("Euclidean distance: " + str(euclidean_distance))
    return(euclidean_distance)








if __name__== "__main__":

    sig_ref = extract_sig(reference_signature).pop()
    challenge_sig = extract_sig(current_signature)
    print(challenge_sig)
    for sig in challenge_sig:
        print("length of signature: " + str(len(sig)))
        compare_sig(shrink_signature(sig,2),shrink_signature(sig_ref,2))
        compare_sig(sig,sig_ref)
        #compare_sig(shrink_signature(truncate_first_values(sig, 10),32),shrink_signature(sig_ref,32))
        #compare_sig(truncate_first_values(sig,50),sig_ref)
