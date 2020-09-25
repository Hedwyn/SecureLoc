from extract_key import parseFile
import os
import sys


PORT_PROVER = "COM18"
PORT_VERIFIER = "COM29"
LOG_NAME = "CBKE_log_"
TXT_EXTENSION = ".txt"
BLENDED_LOG_NAME = LOG_NAME + "final" + TXT_EXTENSION
DATASET = "Dataset1"
PULSE_PREFIX = "_"


def blend_dataset(dataset):
    log_prover_name = LOG_NAME + PORT_PROVER
    log_verifier_name = LOG_NAME + PORT_VERIFIER
    blended_line_verifier = blend_pulses(log_verifier_name, dataset)
    blended_line_prover = blend_pulses(log_prover_name, dataset)

    # writing blended results in a single log
    with open(dataset + "/" + BLENDED_LOG_NAME, 'w+') as f_write:
        f_write.write(blended_line_verifier)
        f_write.write("\n")
        f_write.write(blended_line_prover)

def blend_pulses(fileroot, dataset):
    dir_files = os.listdir(dataset)
    blended_line = PULSE_PREFIX
    chunks = []
    for f in dir_files:
        if fileroot in f:
            with open(dataset + "/" + f) as f_read:
                for line in f_read:
                    # logs for pulses magnitude alway start with '_'
                    if line[0] == PULSE_PREFIX:
                        line_chunks = line[1:-1].split("|")
                        for chunk_idx, chunk in enumerate(line_chunks):
                            if chunk_idx == len(chunks):
                                chunks.append(chunk)
                            else:
                                chunks[chunk_idx] += chunk

    # appending separator between blended chunks, and creating final blended line
    blended_line = PULSE_PREFIX
    for chunk in chunks:
        blended_line += chunk
        blended_line += '|'
   
    return(blended_line)

def import_dataset(dataset):
    blend_dataset(dataset)
    with open(BLENDED_LOG_NAME, 'w+') as f_write:
        f_read = open(dataset + "/" + BLENDED_LOG_NAME)
        for line in f_read:
            f_write.write(line)


def append_to_dataset(log, dataset):
    # removing extension
    log_name = log.split(".")[0]
    files_in_dataset = os.listdir(dataset)
    latest_idx = 0
    print(log_name)
    for f in files_in_dataset:
        if log_name in f:
            # splitting '_' to isolate file index
            f_info = f.split("_")
            # removing extension from the last block to get index
            f_idx = int(f_info[-1].split(".")[0])
            if f_idx > latest_idx:
                latest_idx = f_idx
    new_file_idx = latest_idx + 1
    new_file_name = log_name + "_" + str(new_file_idx) + TXT_EXTENSION

    # copying file
    with open(dataset + "/" + new_file_name, 'w+') as new_file:
        f_log = open(log)
        for line in f_log:
            new_file.write(line)

def append_logs_to_dataset(dataset):
    """Appends the last measurements logs collected to the dataset"""
    log_prover_name = LOG_NAME + PORT_PROVER + TXT_EXTENSION
    log_verifier_name = LOG_NAME + PORT_VERIFIER + TXT_EXTENSION
    append_to_dataset(log_prover_name, dataset)
    append_to_dataset(log_verifier_name, dataset)


if __name__ == "__main__":
    # append_logs_to_dataset(DATASET)
    
    if len(sys.argv) == 1:
        print("You need to provide an argument. \n'+' for appending latests logs to the dataset.\n'x for blending and importing dataset")
    else:
        if (sys.argv[1] == '+'):
            append_logs_to_dataset(DATASET)
        elif (sys.argv[1] == 'x'):
            import_dataset(DATASET)
        else:
            print("Unknown command")





    


            


