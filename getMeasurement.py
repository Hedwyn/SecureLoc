import sys
import os

if __name__ == "__main__":
    idx = sys.argv[1]

    # get number of lines in rp
    logsfile = open("rangings/logs"  + str(idx) + ".txt")
    nb_mes = 0
    for line in logsfile:
        values = line.split()
        if (len(values) == 0) and (nb_mes > 0):
            logsfile.close()
            break;
        if (len(values) == 4):
            nb_mes += 1

    print("nb_mes :" +str(nb_mes) )
    rpfile = open("rp_playback.tab")
    rp = []
    for line in rpfile:
        rp.append(line)

    
        
        
    outfile = open("measurements/playback/logs" + str(idx) + ".txt", 'w+')

    i = 1
    while (os.path.exists("measurements/raw/logs" + str(i) + ".txt" ) ):
        i += 1
    logspos = open("measurements/raw/logs" + str(i - 1)  + ".txt")
    mes_counter = nb_mes
    
    for line in logspos:
        values = line.split()
        
        
        if (mes_counter < nb_mes):
           line = values[0] + " " + values[1] + " " + values[2] + "\n"
           
           outfile.write(line)
           mes_counter += 1
        

        elif (len(rp) == 0):
            break;

        else:
            mes_counter = 0
            outfile.write("\n\n\n" + str(rp[0]) + "\n")
            rp.pop(0)
    
       
        
        


    
        
    
