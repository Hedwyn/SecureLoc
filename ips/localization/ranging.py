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

@file ranging.py
@author Baptiste Pestourie
@date 2019 March 1st
@brief Implementation of ranging protocols- extracts the distance from UWB timestamps for various ranging protocols
@see https://github.com/Hedwyn/SecureLoc
"""

LIGHTSPEED = 229702547.0
TIMEBASE = 15.65E-12


class Ranging:
    """contains the low-level ranging protocols such as recomputing the ranging output 
    with different protocols on the same date"""
    
    def __init__(self,timestamps, lightspeed = LIGHTSPEED, timebase = TIMEBASE ):
        # timestamps
        self.timestamps = timestamps # list of timestamps
        self.distance = None
        self.lightspeed = lightspeed
        self.timebase = timebase

    def TWR(self):
        # computes Two-Way Ranging protocols
         if ( len(self.timestamps) != 4 ):
             print("Incorrect number of timestamps")
         else:
             [t1,t2,t3,t4] = self.timestamps
             tof = (t4 - t1 - (t3 - t2)) / 2; 
             self.distance = tof * self.lightspeed * self.timebase
    
    def getDistance(self, protocol = 'TWR'):
        if protocol == 'TWR':
            self.TWR()
        else:
            print("This protocol does not exist")
            return(0)
            
        return(self.distance)
        

    
        