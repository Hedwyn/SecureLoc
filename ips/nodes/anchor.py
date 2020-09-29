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

@file anchor.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Anchor class - position of the reference station, distances accumalator, distances filtering
@see https://github.com/Hedwyn/SecureLoc
"""

## subpackages
from ips.core.parameters import *
from ips.localization.filter import Filter
from ips.gui.rendering_interface import RenderedNode


class Anchor(RenderedNode):
    """Anchor class - position of the reference station, distances accumalator, distances filtering"""
    def __init__(self, x, y, z, name="unnamed", color='red'):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.name = name
        self.shown = False
        self.isActive = False
        self.distance = {}
        self.raw_distance = {}
        self.rangings = {}
        self.correction_filter = Filter('COR')
        # initialization of the ranging lists for the two robots
        self.init_rangings()

        # genereates the visual representation of the anchor in the 3D engine
        self.create_sphere()

        # displays the name of the anchor in the 3D engine
        self.create_text()

    def get_coordinates(self):
        return(self.x,self.y,self.z)

    def set_coordinates(self,x,y,z):
        """Sets the anchor coordinates. Should be used carefully; this will lead to errors in the localization algorithm.
        Use move_node instead if you wish to move only the node representation in the 3D engine"""
        self.x = x
        self.y = y
        self.z = z

    def get_ID(self):
        """returns anchor ID"""
        return(self.name)

    def set_color(self):
        self.color = color

    def get_all_distances(self):
        """return the distances of the anchor with every robot as a dictionary."""
        return(self.distance)

    def get_raw_distance(self,robotname):
        """ gets the unfiltered distance between the anchor and the given robot"""
        return(self.raw_distance[robotname])

    def set_raw_distance(self,distance,robotname):
        """ sets the unfiltered distance between the anchor and the given robot"""
        self.raw_distance[robotname] = distance

    def init_rangings(self):
        """generates an entry for each robot id in the rangings dictionary"""
        for id_bot in bots_id:
            # adding an entry in the rangings dictionary for each robot id
            self.rangings[id_bot] = []
            self.raw_distance[id_bot] = 0

    def update_rangings(self, distance,target):
        """updates the list of the last NB_RANGINGS rangings"""
        global correction_coeff
        global correction_offset



        # if this is the first ranging
        # writing NB_RANGINGS times the first distance to fill up the list


        #corrected_distance = self.correction_filter.apply( [ distance, correction_coeff[self.name],correction_offset[self.name] ] )[0]
        corrected_distance = distance
        if (self.rangings[target] == [] ):
            for i in range(1, NB_RANGINGS):

                self.rangings[target].append(corrected_distance)



        else:

            self.rangings[target].append(corrected_distance)
            # removes first element to maintain list size
            self.rangings[target].pop(0)




    def get_distance(self, robot_id):
        """ gets the filtered distance between the anchor and the given robot"""

        if (robot_id in self.distance):

            return self.distance[robot_id]
        else:
            # unknown robot id
            return(0)

    def set_distance(self, distance, robot_id):
        """ sets the filtered distance between the anchor and the given robot"""
        if robot_id in self.distance:
            self.distance[robot_id] = distance
        else:
            self.distance[robot_id] = distance
