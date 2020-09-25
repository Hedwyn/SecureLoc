import sys
from datetime import date
import random


dir = 'saved_data'
input_file = 'CBKE_log_final.txt'

if __name__ == "__main__":
    # struct: PRF | PLENGTH | Channel | Distance (cm) | Eavesdrop
    # struct pulses: PULSE_LENGTH | NB_REF_POINTS | CHANNEL_SWITCH | PP_DELAY 0 80
    if len(sys.argv) > 1:
        filename = ''
        for p in sys.argv[1:]:
            filename += p
            filename += '_'
        today = date.today()
        d = today.strftime("%d_%m")
        filename += d
        filename += '_' + str(random.choice(range(100)))
        with open(input_file, 'r') as f:
            print(filename)
            try:
                f_cpy = open(dir + '/' + filename, 'w')
                for line in f:
                    f_cpy.write(line)
                f_cpy.close()
            except:
                print("Could not open create output file")
            
                
