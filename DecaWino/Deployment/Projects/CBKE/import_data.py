import sys
import os

dir = 'saved_data'
output_file = 'CBKE_log_final.txt'

if __name__ == "__main__":
    list_files = os.listdir(dir)
    for f in list_files:
        tags = f.split("_")
        if len(sys.argv) > 1:
            found = True
            for i,arg in enumerate(sys.argv[1:]):
                try:
                    if arg != tags[i]:
                        found = False
                        break
                except:
                    print("malformed file")
            if found:
                print(f)
                try:
                    f_in = open(dir + '/' + f, 'r')
                    with open(output_file,  'w') as f_out:
                        for line in f_in:
                            f_out.write(line)
                    f_in.close()
                except:
                    print("Could not open input file")
                break
    else:
        print("f not found")
                 
    
