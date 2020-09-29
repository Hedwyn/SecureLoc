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

## subpackages
from ips.core.parameters import *
from ips.gui.rendering_interface import RenderedNode

## other libraries
import math
from direct.showbase.DirectObject import DirectObject
from panda3d.core import *



class Tag(DirectObject,RenderedNode):
    """Class for mobile tags"""
    def __init__(self, name, color='orange'):

        self.name = name # ID
        self.positions = [] #
        self.speed_vector = []
        self.acc_vector = []
        self.color = color
        self.rmse = {}  # root mean-squared error during differential TWR
        self.cooperative_distances = {} # in cooperative mode, distances to other tags
        self.cooperative_deviation = []
        self.is_attacked = False
        self.switch_attacked_state = False

        self.trust_indicator = 1 # level of trust in the tag on a scale of 0 to 1; decreases with suscpicious behaviors
        self.last_suspicious_event = 0

        # POSITIONS_BUFFER_LENt needs POSITIONS_BUFFER_LENT_SIZE elements to avoid reading conflicts
        # initializing to 0
        for x in range(0, POSITIONS_BUFFER_LEN):
            self.positions.append(DEFAULT_POS)

        # speed vector list needs SPEED_LIST-SIZE elements to avoid reading conflicts
        # initializing to 0

        for y in range(0, SPEED_BUFFER_LEN):
            self.speed_vector.append([0,0,0])

        for z in range(0, ACC_BUFFER_LEN):
            self.acc_vector.append([0,0,0])

        self.ready = False
        self.shown = False


        self.create_sphere()
        self.create_text()
        self.show()


    def get_coordinates(self):
        return(self.get_current_pos())

    def set_coordinates(self,x,y,z):
        """Sets the tag coordinates. Should be used carefully; this will lead to errors in the localization algorithm.
        Use move_node instead if you wish to move only the node representation in the 3D engine"""
        self.positions.append((x,y,z))
        if len(self.positions) > POSITIONS_BUFFER_LEN:
            # removing oldest position
            del self.positions[0]

    def get_ID(self):
        """returns tag ID"""
        return(self.name)

    def get_all_distances(self):
        """return the distances of the anchor with every robot as a dictionary."""
        # TODO: Returns currently empty list given that the tags do not localize other tags.
        # Needs to be modified for cooperative approaches.
        return({})

    def get_discretized_coordinates(self,x,y,z,granularity = SQUARE_SIZE ):
        """returns the coordinates of the robot on a tiled floor.
        Granularity is defined as the length of a tile"""
        a = 0
        b = 0
        c = 0

        distance = 0

        while (distance <= x):
            distance += granularity
            if ( (x - distance) > - (granularity / 2) ):
                a += 1
        distance = 0

        while (distance <= y):
            distance += granularity
            if ( (y - distance) > - (granularity / 2) ):
                b += 1
        distance = 0

        while (distance <= z):
            distance += granularity
            if ( (z - distance) > - (granularity / 2) ):
                c += 1
        distance = 0
        return(a,b,c)


    def get_current_pos(self):
        """ returns the most recent position in the position list"""
        if self.positions:
            return(self.positions[-1])
        else:
            print("Error: positions list is empty")
            return (0,0,0)

    def get_previous_pos(self):
        """ returns previous position for speed calculation"""
        if len(self.positions) > 1:
            return(self.positions[-2] )
        else :
            print("Error: not enough positions stored. Defaulting to current position")
            return(self.get_current_pos())

    def get_position(self):
        """Calls get_coordinates"""
        return(self.get_coordinates())

    def set_position(self, pos):
        """Takes position as a tuple in input.
        Sets coordinates and displays the node at its new position in the 3D engine"""
        (x,y,z) = pos
        self.set_coordinates(x,y,z)


    def add_rmse_sample(self,sample, anchor_id):
        """Add the most recent root mean-square error samples to the accumulator"""
        if not(anchor_id in self.rmse):
            self.rmse[anchor_id] = []

        if len(self.rmse[anchor_id] ) == RMSE_SW_LEN:
            del self.rmse[anchor_id][RMSE_SW_LEN // 2]
        idx = 0

        while idx < len(self.rmse[anchor_id]) and sample < self.rmse[anchor_id][idx]:
            idx += 1

        self.rmse[anchor_id].insert(idx, sample)


    def add_cooperative_distance_sample(self,sample, tag_id):
        """Add the most recent root mean-square error samples to the accumulator"""

        if not(tag_id in self.cooperative_distances):
            self.cooperative_distances[tag_id] = []

        if len(self.cooperative_distances[tag_id] ) == COOP_DIST_SW_LEN:
            del self.cooperative_distances[tag_id][COOP_DIST_SW_LEN // 2]
        idx = 0

        while idx < len(self.cooperative_distances[tag_id]) and sample < self.cooperative_distances[tag_id][idx]:
            idx += 1

        self.cooperative_distances[tag_id].insert(idx, sample)

    def add_cooperative_deviation_sample(self,sample):
        """Add the most recent root mean-square error samples to the accumulator"""

        if len(self.cooperative_deviation) == COOP_DIST_SW_LEN:
            del self.cooperative_deviation[COOP_DIST_SW_LEN // 2]
        idx = 0

        while idx < len(self.cooperative_deviation) and sample < self.cooperative_deviation[idx]:
            idx += 1

        self.cooperative_deviation.insert(idx, sample)

    def get_cooperative_deviation(self):
        # checking if the sliding window if full (will need a few seconds at the beginning)
        if len(self.cooperative_deviation) != COOP_DIST_SW_LEN:
            return(0)

        # returning  median
        return(self.cooperative_deviation[COOP_DIST_SW_LEN // 2])

    def get_rmse(self, anchor_id):
        """returns the current differential rmse with the given anchor"""
        
        # checking if the rmse has been written
        if not(anchor_id in self.rmse):
            return

        # checking if the sliding window if full (will need a few seconds at the beginning)
        if len(self.rmse[anchor_id]) != RMSE_SW_LEN:
            return(0)

        # returning  median
        return(self.rmse[anchor_id][RMSE_SW_LEN // 2])

        # averaging with decile elimination - uncomment to enable
        # decile_idx = len(self.rmse[anchor_id]) / 10
        # idx = 0
        # sum = 0
        # while idx < len(self.rmse[anchor_id]) - decile_idx:
        #     sum += self.rmse[anchor_id][idx]
        #     idx += 1
        
        # return(sum / idx )

    def get_cooperative_distance(self, tag_id):
        """returns the current differential rmse with the given anchor"""
        
        # checking if the rmse has been written
        if not(tag_id in self.cooperative_distances):
            return

        # checking if the sliding window if full (will need a few seconds at the beginning)
        if len(self.cooperative_distances[tag_id]) != COOP_DIST_SW_LEN:
            return(0)

        # returning  median
        return(self.cooperative_distances[tag_id][COOP_DIST_SW_LEN // 2])

    def get_average_rmse(self):
        """Returns the average of the differential rmse with all the anchors"""
        nb_anchors = 0
        total_rmse = 0
        for anchor in self.rmse:
            nb_anchors += 1 
            total_rmse += self.get_rmse(anchor)
    
        if (nb_anchors != 0):
            total_rmse /= nb_anchors
        else:
            total_rmse = 0


        # # checking for attacks
        # attack_detected =  (total_rmse > RMSE_MALICIOUS)  
             
        # if self.is_attacked != attack_detected:
        #     self.switch_attacked_state = True
        #     self.is_attacked = attack_detected


        return(total_rmse)

    def compute_rmse(self, current_distance, differential_distance):
        """calculates the root mean-squared error between the distances measured in normal and differential TWR"""
        rmse = math.sqrt(pow(current_distance - differential_distance, 2))
        return(rmse)

    def get_abs_speed(self):
        """computes the absolute speed from the speed vector"""

        speed_vector = self.get_speed_vector()
        abs_speed = math.sqrt(pow(speed_vector[0], 2) + pow(speed_vector[1], 2) + pow(speed_vector[2], 2))  # m/s
        return(abs_speed)

    def decrease_trust_indicator(self,factor = 1):
        """Decreases the trust indicator when a suspicious event is detected"""
        # suscpicious event detected, resetting counter
        p = TI_PARAMETERS
        self.last_suspicious_event = 0
        self.trust_indicator += factor * p["slew"] - p["offset"]
        if self.trust_indicator < 0:
            self.trust_indicator = 0

    def increase_trust_indicator(self):
        """Increases the trust indicator when a suspicious event is detected"""
        p = TI_PARAMETERS
        self.last_suspicious_event += 1
        if self.last_suspicious_event > p["threshold"]:
            self.trust_indicator += p["offset"]
            if self.trust_indicator >1:
                self.trust_indicator = 1



    def get_abs_acc(self):
        """computes the absolute acceleration from the acceleration vector"""
        acc =  self.get_acc_vector()
        abs_acc = math.sqrt(pow(acc[0], 2) + pow(acc[1], 2) + pow(acc[2], 2))  # m/s
        return(abs_acc)

    def set_speed_vector(self, speed_vector, replace_last=False):
        """Appends current speed to speed list and
        removes the oldest speed data stored"""
        if replace_last:
            # removes last element in replace mode
            self.speed_vector.pop(SPEED_BUFFER_LEN - 1)
        else:
            # removes first element to keep a list size of SPEED_BUFFER_LEN
            self.speed_vector.pop(0)

        self.speed_vector.append(speed_vector)

    def set_acc_vector(self, acc, replace_last=False):
        """Appends current acceleration to acceleration list and removes the oldes acceleration data stored"""
        if replace_last:
            #removes last element in replace mode
            self.acc_vector.pop(ACC_BUFFER_LEN -1)
        else:
            # removes first element to keep a list size of SPEED_BUFFER_LEN
            self.acc_vector.pop(0)

        self.acc_vector.append(acc)

    def get_speed_vector(self):
        """ returns the most recent speed vector in the speed vector list"""

        return(self.speed_vector[SPEED_BUFFER_LEN - 1])

    def get_acc_vector(self):
        """ returns the most recent acceleration vector in the acceleration vector list"""

        return(self.acc_vector[ACC_BUFFER_LEN - 1])

    def compute_speed(self,replace_mode = False):
        """calculates the speed after each position update"""
        pos = self.get_position()
        pre_pos = self.get_previous_pos()

        # coordinates of the current position

        x = pos[0]
        y = pos[1]
        z = pos[2]

        # coordinates of the previous position
        pre_x = pre_pos[0]
        pre_y = pre_pos[1]
        pre_z = pre_pos[2]

        # calculates the speed as (position vector / sample time )
        speed_vector = [(x - pre_x)/T, (y - pre_y)/T, (z - pre_z) / T]

        # sets the speed  of the robot
        self.set_speed_vector(speed_vector, replace_mode)
        v_print("robot " + self.name + " speed: " + str(self.get_abs_speed()) + " m/s")

    def compute_acc(self, replace_mode=False):
        """calculates the acceleration after each position update"""
        speed = self.get_speed_vector()
        pre_speed = self.speed_vector[SPEED_BUFFER_LEN - 2]

        v_x = speed[0]
        v_y = speed[1]
        v_z = speed[2]

        pre_v_x = pre_speed[0]
        pre_v_y = pre_speed[1]
        pre_v_z = pre_speed[2]

        acc = [(v_x - pre_v_x) / T, (v_y - pre_v_y) / T, (v_z - pre_v_z) / T]
        self.set_acc_vector(acc, replace_mode)
        v_print("robot " + self.name + " acceleration: " + str(self.get_abs_acc()) + " m/s²" + "\n" )
