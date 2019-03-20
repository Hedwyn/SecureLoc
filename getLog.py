import sys

if __name__ == "__main__":
    file_idx = sys.argv[1]
    in_log = open("Rangings/logs" + str(file_idx) + ".txt")
    out_log = open("Logs/logs_ranging.txt",'w+')
    rp_tab = open("rp_playback.tab",'w+')

    next_is_rp = True
    serie_started = False
    for line in in_log:
        values = line.split()
        if (len(values) == 4):
            out_log.write("0001020300010203 ")
            out_log.write(line)
        if (len(values) == 3):
            # rp
            rp_tab.write(line)

    in_log.close()
    out_log.close()
    
            

                
            
        

        

    
