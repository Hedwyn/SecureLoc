"""****************************************************************************
Copyright (C) 2017-2020 LCIS Laboratory - Baptiste Pestourie

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, in version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************

@file MovingEntity.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Class for the mobile tags - contains position, speed and acceleration estimations
@see https://github.com/Hedwyn/SecureLoc
"""

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
    
       
        
        


    
        
    
