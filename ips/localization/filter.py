"""****************************************************************************
Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie

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

@file filter.py
@author Baptiste Pestourie
@date 2018 March 1st
@brief Contains different filters for the distance estimations extracted from ranging protocols
@see https://github.com/Hedwyn/SecureLoc
"""
## subpackages
from ips.core.parameters import *

## other libraries
import math




class Filter:
    """ defines the different type of filters that can be applied on the ranging or position data"""

    def __init__(self, mode = "SW", param = []):

        self.mode = mode
        self.param = param
        self.thold_acceleration = DEFAULT_ACC_THOLD

    def apply(self,args = None):
        """computes the filter associated to the chosen mode"""
        out = []
        if (args == None):
            args = self.param

        if (self.mode == 'SW'):
            # filter type : Sliding Window
            if (len(args) == 3):
                out.append( self.sliding_window(args[0], args[1], args[2] ) )
            else:
                out.append( self.sliding_window(args[0], args[1], args[2], args[3] ) )
        elif (self.mode == 'SAT'):
            out.append( self.saturation(args[0],args[1],args[2],args[3],args[4]) )
            #filtered_pos =
        elif (self.mode == 'COR'):
            out.append( self.correction( args[0], args[1], args[2] ) )

        return(out)




    def sliding_window(self,ranging_list,nb_samples,nb_eliminations_start,nb_eliminations_end = 0 ):
        """ removes the extremum values of the given list,
        then returns the average of remaining values"""

        sorted_ranging = []
        for idx in range(len(ranging_list) - nb_samples, len(ranging_list) ):

            ranging = ranging_list[idx]

            i = 0
            if (sorted_ranging == []):
                sorted_ranging.append(ranging)
            else:
                while(i < ( len(sorted_ranging) - 1) & (ranging < sorted_ranging[i]) ):
                    i += 1

                sorted_ranging.insert(i,ranging)

        for j in range(0, nb_eliminations_start):
            sorted_ranging.pop(0)



        for j in range(0, nb_eliminations_end):
            sorted_ranging.pop(len(sorted_ranging) - j - 1)

        sum = 0
        for ranging in sorted_ranging:
            sum += ranging

        average = sum / len(sorted_ranging)

        return(average)

    def set_thold_acceleration(self,thold_acceleration):
        """ modifies the threshold for maximum tolerated acceleration"""
        self.thold = thold_acceleration

    def get_abs_acc(self,acceleration):
        """returns absolute acceleration"""
        abs_acc = math.sqrt( pow(acceleration[0], 2 ) + pow(acceleration[1], 2 ) + pow(acceleration[2], 2 ) )
        return(abs_acc)

    def saturation(self,pre_pos,pos,speed,current_acc,step):
        """ saturates the position vector if maximum tolerated acceleration is exceeded.
        Returns the new position"""

        #current_acc = self.get_abs_acc(acceleration[len(acceleration) - 1])
        print("acceleration : " + str(current_acc) )
        print("thold ! :" + str(self.thold_acceleration) )

        if (current_acc > self.thold_acceleration):

            ratio = self.thold_acceleration / current_acc
            print("saturation ratio: " + str(ratio) )


            x = ratio * (pos[0] - pre_pos[0])
            y = ratio * (pos[1] - pre_pos[1])
            z = ratio * (pos[2] - pre_pos[2])


            (a,b,c) = pre_pos
            saturated_pos = ( x + a, y + b, z + c)
            self.thold_acceleration += step
        else:
            saturated_pos = pos
            self.thold_acceleration = DEFAULT_ACC_THOLD


        print("saturated_pos = " + str(saturated_pos))
        print("raw pos = " + str(pos) )
        return(saturated_pos)

    def correction(self,distance,coeff,offset):
        """linear correction for anchor rangings"""

        corrected_distance = distance * coeff + offset
        return(corrected_distance)













if __name__ == '__main__':
    # use for testing


    filter1 = Filter(2)
    p =  [6,6,5,6,6,6,6,6,6,8,9,10]
    acceleration = [ (2,2,2) ]
    speed = []
    pos = [ (1,1,1), (2,2,2) ]
    print(filter1.saturation(pos,speed,acceleration,0.1))

    filter2 = Filter("SW",[p,10,1])
    print(filter2.apply())
