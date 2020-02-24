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

@file world.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Contains all the positioning methods for the localization
@see https://github.com/Hedwyn/SecureLoc
"""

from anchor import Anchor
#from application import *
from Filter import Filter
from parameters import *
import math
import operator
from GaussNewton import *
import numpy as np
import sympy as sp
from RenderingInterface import RenderedWorld

class World(RenderedWorld):
    """World class, represents the room in which the robots will evolve.
    The world contains the anchors with their positions, and is able
    to return the positions of the robots or whatever is moving in it"""

    def __init__(self, width: float, height: float, anchors: list):
        """anchors should be a list of 4 valid anchors"""
        self.width = width
        self.height = height
        self.anchors = anchors
        self.target = None
        self.shown = False
        self.create_grid()
        self.create_anchors()

    def create_anchors(self):
        """Displays anchors"""
        for anchor in self.anchors:
            anchor.show()

    def gen_anchors_name(self, nb_anchors):
        """generates a list of anchors id for the given total number of anchors"""
        if (nb_anchors > 26):
            print("cannot handle " + str(nb_anchors) + "\n")
            print("the number of anchors should be below 26")

        else:
            anchors_name = []
            for i in range(nb_anchors):
                # generates successive letters starting from A
                anchors_name.append(str(i + 1))

        return(anchors_name)




    def get_target(self,robot):
        """ gets the id of the robot to localize"""
        self.target = robot

    def update_anchor(self, name: str, distance: float,robot_id,options = None):
        """Updates distance between anchor and robot.
           Note that anchors names should be unique for this to work"""
        if (distance < 0) or (distance > DMAX):
            return
        for anchor in self.anchors:
            if anchor.name == name:


                anchor.update_rangings(distance,robot_id)
                anchor.set_raw_distance(distance,robot_id)


                if (options == "SW"):
                    # sliding window enabled

                    sliding_windows = Filter("SW",[anchor.rangings[robot_id],SW_SIZE,SW_ELIMINATIONS,0])
                    filtered_distance = sliding_windows.apply()[0] # output(s) of filters are returned as a list


                    anchor.set_distance(filtered_distance,robot_id)

                else:
                    anchor.set_distance(distance,robot_id)




                # activates the anchor the first time it uploads a distance
                if (not(anchor.isActive) and distance > 0.0):

                    anchor.isActive = True
                return


    def ranging(self,x,y,z,anchor_idx):

        anchor_x = self.anchors[anchor_idx].x
        anchor_y = self.anchors[anchor_idx].y
        anchor_z = self.anchors[anchor_idx].z

        return(math.sqrt(pow( x - anchor_x , 2) + pow( y - anchor_y, 2) + pow( z - anchor_z,2) ))

    def get_distance(self,pos1,pos2):
        """ returns the distance between pos1 and pos2"""

        (x1,y1,z1) = pos1
        (x2,y2,z2) = pos2

        distance = math.sqrt(pow( (x1 - x2), 2) + pow( (y1 - y2), 2) +  pow( (z1 - z2), 2) )
        return(distance)


    def mse(self,rangings,pos):
        """ Calculates the Mean Square Error of the given position.
        Error is defined as the difference between the ranging of the given position and the given rangings"""

        mean_error = 0

        (x,y,z) = pos



        for (i,distance) in enumerate(rangings):
            error = (self.ranging(x,y,z,i) - distance)
            #print("error is:" + str(error) )
            mean_error += pow(error,2)
        if rangings:
            mean_error = mean_error / len(rangings)


        return(mean_error)

    def gauss_newton(self,rangings,start_pos):
        """applies Gauss-Newton on the set of rangings to find the tag's position. Uses the given position as starting point"""
        xvals= []
        yvals = []
        zvals = []
        # squaring the ranging to avoid computing square root in GN algorithm. This reduces the computation load.
        sq_rangings = [pow(ranging,2) for ranging in rangings]

        if RANDOM_SEARCH:
            start_pos = DEFAULT_POS

        # getting the anchors coordinates
        for anchor in self.anchors:
            xvals.append(anchor.x)
            yvals.append(anchor.y)
            zvals.append(anchor.z)
        #print("xvals: " + str(xvals))
        #print("yvals: " + str(yvals))

        # creating the dataset
        rangings_ds = GNdataset(
               name = "Rangings",
               expr = "((x-b1)**2 + (y-b2)**2 + (z-b3)**2)",
            symbols = sp.symbols("x y z b1:4"),
              xvals = np.array(xvals),
              yvals = np.array(yvals),
              zvals = np.array(zvals),
              rangingvals = np.array(sq_rangings),
              cvals = None,
             starts = np.array((start_pos,))
        )

        # solving Gauss-Newton
        # Warning: Default parameters are used here; refer to GaussNewton class.
        sol, its = rangings_ds.solve(rangings_ds.starts[0])
        v_print("Gauss-Newton solution: " + str(sol))
        sol = tuple(sol)
        mse = self.mse(rangings,sol)

        return(sol,mse)


    def iterate(self,rangings,start_pos):
        """ Finds the minimum MSE in the neighborhood of start_pos and repeats the process from that new position"""

        step = 0.01
        # starting from the center if random search is enabled
        if (RANDOM_SEARCH):

            start_pos = DEFAULT_POS #center of the platform

        # starting iterations
        k = 0
        pos = start_pos
        while (k < NB_STEPS ):
            (x,y,z) = pos

            v_print("position at iteration " + str(k) + ":\n:" + str(pos) )

            # choosing direction
            directions = []
            for i in range(-10,11):
                for j in range(-10,11):
                    directions.append( (x+(i * step ),y+(j * step),0) )

            mean_squared = []


            for (i,direction) in enumerate(directions):


                error = self.mse(rangings, direction)
                mean_squared.append(error)
                #v_print("mean squared for " + name_directions[i] + ": " + str(error))


            minimum = 1000
            min_idx = 0
            for (i,ms) in enumerate(mean_squared)   :
                if (ms < minimum):
                    min_idx = i
                    minimum = ms
            #v_print(name_directions[min_idx])

            pos = directions[min_idx]
            k += 1
        v_print("MSE :" + str(ms) )

        return(pos,ms)

    def localize(self,target):
        """localizes the given target"""
        rangings = []
        # getting ranging values from anchors
        for anchor in self.anchors:
            distance = anchor.get_distance(target)
            rangings.append(distance)

        # trilateration-based solutions

        if len(self.anchors) ==  0:
            raise TooFewAnchors("No anchor detected")
        elif len(self.anchors) == 1:
            # Calulating position on y axis
            anchor_pos = (self.anchors[0].x,self.anchors[0].y,self.anchors[0].z)
            x = self.anchors[0].x
            y = self.anchors[0].y
            z = self.anchors[0].z
            centroid = (x, y + self.anchors[0].get_distance(target) , z )
            mse_sum = 0
        elif len(self.anchors) == 2:
            d_print("Only two anchors for position computation. Assuming that the tag is on the positive part of the y axis")
            centroid = self.trilateration(target,self.anchors[0], self.anchors[1])[0]
            mse_sum = 0
        else:
            solutions = []
            solutions_mse = []
            for i,anchor in enumerate(self.anchors):
                j = i + 1
                while j < len(self.anchors):
                    # finding which of the two solution is the most likely one
                    (s,mse) = self.trilateration(target,self.anchors[i], self.anchors[j])
                    solutions.append(s)
                    solutions_mse.append(mse)
                    j += 1

                mse_inv = [1/x for x in solutions_mse]
                mse_sum = sum(solutions_mse)
                mse_inv_sum = sum(mse_inv)

                centroid = (0,0,0)
                weighted_s = (0,0,0)
                tuple(map(operator.add, centroid, weighted_s))

                for idx,s in enumerate(solutions):
                    # mapping the + operation on tuples to a dimension by dimension sum


                    weight = mse_inv[idx] / mse_inv_sum
                    weighted_s = (weight * coord for coord in s)
                    centroid = tuple(a + b for a,b in zip(centroid,weighted_s) )


        # checking which localization method is enabled
        if (GN):
            pos,mse = self.gauss_newton(rangings,centroid)
        elif (ITERATIVE):
            pos,mse = self.iterate(rangings,centroid)
        else:
            # defaulting to weighted centroid
            pos,mse = centroid,mse_sum


        (x,y,z) = pos
        anchors_mse = {}

        # calculating the MSE of each anchor
        for idx,anchor in enumerate(self.anchors):
            anchors_mse[anchor.name] = pow(self.ranging(x,y,z,idx) - anchor.get_distance(target),2)


        return(pos,mse,anchors_mse)

    def trilateration(self,target,anchor1,anchor2, anchor3 = None, mode = '2D'):
        """computes the trilateration of target based on the rangings from anchor 1 and 2.
        Two solutions are obtained based on Pythagora's theorem, both are returned"""
        pos1 = (anchor1.x, anchor1.y, anchor1.z)
        pos2 = (anchor2.x, anchor2.y, anchor2.z)

        # getting the distance between both anchors
        base = self.get_distance(pos1, pos2)

        # checking that anchors do not share the same coordinates
        if base == 0:
            return

        # applying Pythagora on the triangle (anchor1, anchor 2, target)
        # considering the cartesian system of {anchor 1 (0,0);anchor 2 (0, base) }
        # calculating dx = x and dy = |y| with (x,y) the tag's coordinates in the cartesian system of (anchor1, anchor 2)
        r1 = anchor1.get_distance(target)
        r2 = anchor2.get_distance(target)


        dx = ( pow(r1,2) - pow(r2,2) + pow(base,2) ) / ( 2 * base)

        # if the rangings have been perturbated a negative solution may be obtained
        # zeroing dx and dy in that case

        if dx < 0:
            dx = 0

        dy = pow(r1,2) - pow(dx,2)
        if (dy < 0):
            dy = 0
        else:
            dy = math.sqrt(dy)

        # coordinate changes -> calculating the coordiantes in the global cartesian system
        # vect_o denotes the vector from the origin to anchor 1;
        # vect_a denotes the vector from anchor 1 to the tag

        if mode == '2D':
            # z is assumed to be 0
            # calculations are exclusively based on x,y

            # calculating vect_base_x and vect_base_y coordinates in the global cartesian system
            vect_base_x  = [(anchor2.x - anchor1.x) / base,(anchor2.y - anchor1.y) / base ]
            vect_base_y = [-vect_base_x[1], vect_base_x[0]]
            vect_o = [anchor1.x, anchor1.y]

            # computing first solution
            vect_a = [dx, dy]
            ##print("vect_a" + str(vect_a))
            s1 = [vect_base_x[0] * vect_a[0] + vect_base_y[0] * vect_a[1]   , vect_base_x[1] * vect_a[0] + vect_base_y[1] * vect_a[1] ]
            ##print("s1" + str(s1))
            s1[0]+= vect_o[0]
            s1[1]+= vect_o[1]

            # appending z coordinate
            s1.append(0)

            # computing second solution
            vect_a = [dx, -dy]
            vect_a = [dx, dy]
            s2 = [vect_base_x[0] * vect_a[0] + vect_base_y[0] * vect_a[1]   , vect_base_x[1] * vect_a[0] + vect_base_y[1] * vect_a[1] ]
            s2[0]+= vect_o[0]
            s2[1]+= vect_o[1]
            # appending z coordinate
            s2.append(0)

            # determining which one of the two solution is the right one based on MSE of the other rangings
            rangings = []
            for anchor in (self.anchors):
                if anchor.name == anchor1.name or anchor.name == anchor2.name:
                    continue
                rangings.append(anchor.get_distance(target))
            # converting solutions from list to tuple
            s1 = tuple(s1)
            s2 = tuple(s2)

            #comapring the mean sqaured error for both solution and picking the best one
            mse1 = self.mse(rangings, s1)
            mse2 = self.mse(rangings, s2)
            if mse1 > mse2:
                return(s2,mse2)
            else:
                return(s1,mse1)

        elif mode == '3D':
            # z is assumed to be 0
            # calculating vect_base_x and vect_base_y coordinates in the global cartesian system
            vect_base_x  = [(anchor2.x - anchor1.x) / base,(anchor2.y - anchor1.y) / base ]
            vect_base_y = [-vect_base_x[1], vect_base_x[0]]
            vect_o = [anchor1.x, anchor1.y]

            # computing first solution
            vect_a = [dx, dy]
            ##print("vect_a" + str(vect_a))
            s1 = [vect_base_x[0] * vect_a[0] + vect_base_y[0] * vect_a[1]   , vect_base_x[1] * vect_a[0] + vect_base_y[1] * vect_a[1] ]
            ##print("s1" + str(s1))
            s1[0]+= vect_o[0]
            s1[1]+= vect_o[1]

            # appending z coordinate
            s1.append(0)

            # computing second solution
            vect_a = [dx, -dy]
            vect_a = [dx, dy]
            s2 = [vect_base_x[0] * vect_a[0] + vect_base_y[0] * vect_a[1]   , vect_base_x[1] * vect_a[0] + vect_base_y[1] * vect_a[1] ]
            s2[0]+= vect_o[0]
            s2[1]+= vect_o[1]
            # appending z coordinate
            s2.append(0)

            # determining which one of the two solution is the right one based on MSE of the other rangings
            rangings = []
            for anchor in (self.anchors):
                if anchor.name == anchor1.name or anchor.name == anchor2.name:
                    continue
                rangings.append(anchor.get_distance(target))
            # converting solutions from list to tuple
            s1 = tuple(s1)
            s2 = tuple(s2)

            #comapring the mean sqaured error for both solution and picking the best one
            mse1 = self.mse(rangings, s1)
            mse2 = self.mse(rangings, s2)
            if mse1 > mse2:
                return(s2,mse2)
            else:
                return(s1,mse1)
            raise NotImplementedError
        else:
            raise ValueError("The specifed mode does not exist")


    def update_correction(self,rangings,solution):
        """dynamically corrects the offset applied to the rangings, by comparing the received ranging value to the estimated one.
            The correction is based on a ratio of the difference between the two values"""

        global correction_offset
        ratio = 0 # disabled
        # Noise estimation
        (x,y,z) = solution
        for idx in range (len(self.anchors)):
            v_print("position :" + str(solution) )
            real_ranging = self.ranging(x,y,z,idx)
            measured_ranging = rangings[idx]
            v_print("estimated :" + str(real_ranging) + "measured :" + str(measured_ranging))
            offset = ratio * (real_ranging - rangings[idx] )
            correction_offset[self.anchors[idx].name] += offset
            v_print("offset anchor " + str(self.anchors[idx].name) + " : " + str(correction_offset[self.anchors[idx].name] ))


    def predict_pos(self,robot):
        """estimates the position at the next iteration based on tag's speed"""


        (X,Y,Z) = robot.get_pos()
        (x,y,z) = robot.get_pre_pos()

        predicted_pos = (2 * X - x, 2 * Y - y, 2 * Z - z)

        return(predicted_pos)


    def chose_closest_solution(self,solutions_list,position):
        """returns the closest solution of solutions_list from the given position"""
        min_idx = 0
        min_distance = 0
        for (idx,solution) in enumerate(solutions_list):
            distance = self.get_distance(solution,position)
            if (distance < min_distance):
                min_idx = idx
                min_distance = distance

        return(solutions_list[min_idx])
