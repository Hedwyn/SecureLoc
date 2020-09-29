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

## subpackages
from ips.nodes.anchor import Anchor
from ips.localization.gauss_newton import *
from ips.localization.filter import Filter
from ips.localization.particle_filters import Node, Particle, ParticleFleet
from ips.core.parameters import *
from ips.gui.rendering_interface import RenderedWorld


## other libraries
import math
import operator
import numpy as np
import sympy as sp


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
        self.particle_fleet = None
        self.localization_algorithm = DEFAULT_LOCALIZATION_ALGORITHM
        if PARTICLES:
            self.init_particle_filter()

    def get_localization_algorithm(self):
        """Returns the localization algorithm being currently employed"""
        if self.localization_algorithm == GN:
            algorithm = 'GN'
        elif self.localization_algorithm == WCN:
            algorithm = 'WCN'
        elif self.localization_algorithm == ITERATIVE:
            algorithm = 'Iterative'
        elif self.localization_algorithm == PARTICLES:
            algorithm = 'Particles'
        return(algorithm)

    def init_particle_filter(self):
        self.particle_fleet = ParticleFleet()
        self.particle_fleet.init_anchors(self.anchors)        


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
        (x,y,z) = start_pos
        if (MODE_3D):
            z += 0.01
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
             starts = np.array(((x,y,z),))
        )

        # solving Gauss-Newton
        # Warning: Default parameters are used here; refer to GaussNewton class.
        sol, its = rangings_ds.solve(rangings_ds.starts[0])
        v_print("Gauss-Newton solution: " + str(sol))
        sol = tuple(sol)
        mse = self.mse(rangings,sol)


        return(sol,mse)

    def particle_filter(self, target, rangings, solutions):
        """ Computes the position with a particle filter"""      
        self.particle_fleet.register_tag_potential_positions(target, solutions)
        self.particle_fleet.register_tag_rangings(target, rangings)
        self.particle_fleet.generate_particles(target)
        self.particle_fleet.move_particles(target)
        self.particle_fleet.compute_particles_likelihood
        # computing solution
        solution_particle = self.particle_fleet.output_solution_particle(target)
        solution = solution_particle.get_pos()
        mse = self.mse(rangings, solution)
        print(solution_particle.get_depth())
        solution_particle.show_trajectory()

        # resampling particles
        self.particle_fleet.particles_resampling(target)



        return(solution,mse)


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
            centroid = self.trilateration_2D(target,self.anchors[0], self.anchors[1])[0]
            mse_sum = 0
        else:
            solutions = []
            solutions_mse = []
            if MODE_3D:
                N = len(self.anchors)
                for i,anchor in enumerate(self.anchors):                  
                    (s, mse) = self.trilateration_3D(target, anchor, self.anchors[(i + 1) % N], self.anchors[(i + 2) % N])
                    solutions.append(s)
                    solutions_mse.append(mse)

            else: # 2D localization                    
                for i,anchor in enumerate(self.anchors):
                    j = i + 1
                    while j < len(self.anchors):
                        # finding which of the two solution is the most likely one
                        (s,mse) = self.trilateration_2D(target,self.anchors[i], self.anchors[j])
                        solutions.append(s)
                        solutions_mse.append(mse)
                        j += 1

            mse_inv = [1/(x + RESOLUTION) for x in solutions_mse]
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
        if self.localization_algorithm == GN:
            pos,mse = self.gauss_newton(rangings,centroid)

        elif self.localization_algorithm == PARTICLES:
            pos, mse = self.particle_filter(target, rangings, solutions)

        elif self.localization_algorithm == ITERATIVE:
            pos,mse = self.iterate(rangings,centroid)

        elif self.localization_algorithm == WCN:
            # defaulting to weighted centroid
            pos,mse = centroid,mse_sum


        (x,y,z) = pos
        anchors_mse = {}

        # calculating the MSE of each anchor
        for idx,anchor in enumerate(self.anchors):
            anchors_mse[anchor.name] = pow(self.ranging(x,y,z,idx) - anchor.get_distance(target),2)


        return(pos,mse,anchors_mse)

    @staticmethod
    def compute_orthogonal_vector(vect_a, vect_b):
        """In 3D, if vect_a and vect_b are orthogonal, calculates vect_c such as (A,B,C) is a cartesian orthonormal system"""
        (x1, y1, z1) = vect_a
        (x2, y2, z2) = vect_b
        (a, b, c) = (0 , 0, 0)
        ## with vect_c = (a,b,c), we get:
        # ax1 + by1 + cz1 = 0
        # ax2 + by2 + cz2 = 0

        # first round: eliminating y
        # applying L1 - (y1 / y2) L2
        if y2 != 0:
            a = x1 - (y1 / y2) * x2
            c = z1 - (y1 / y2) * z2

            if a == 0:
                 # choosing arbitrarily c = 1
                c = 1
            else:
                # choosing arbitrarily a = 1
                a = 1
            if c != 0:
                c = -a / c
            a = 1 

        else:
            # equivalent to a 2D equation: ax2 = -cz2
            # choosing arbitrarily a = 1
            a = 1
            if z2 == 0:
                # x2 =0 not possible as we would get a null vector; hence a = 0
                # we get L1: by1 + cz1 = 0 => b = -cz1 / y1           
                # # choosing arbitrarily c = 1   
                if z1 != 0:
                    c = 1
            else:
                c = -x2 / z2
        
        # computing b
        if y1 != 0:
            b = -(a * x1 + c * z1) / y1

        # normalizing
        norm = math.sqrt( pow(a, 2) + pow(b, 2) + pow(c, 2) )
        a /= norm
        b /= norm
        c /= norm

        vect_c = (a,b,c)
        return(vect_c)



    def trilateration_2D(self,target,anchor1,anchor2):
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

    def trilateration_3D(self,target,anchor1,anchor2, anchor3):
        """computes the 3D trilateration of target based on the rangings from anchor 1, 2, and 3.
        Anchors are assumed to be on the same plan.
        Two solutions are obtained based on Pythagora's theorem, the one with the lowest mse is returned"""
        pos1 = [anchor1.x, anchor1.y, anchor1.z]
        pos2 = [anchor2.x, anchor2.y, anchor2.z]
        pos3 = [anchor3.x, anchor3.y, anchor3.z]

        ## coordinates system
        # Anchor 3
        #    |  
        #    | base_y
        #    |
        #    |          base_x
        # Anchor 2 ----------------Anchor 1

        # getting the distance between both anchors
        base_x = self.get_distance(pos1, pos2)
        base_y = self.get_distance(pos2,pos3)

        # checking that anchors do not share the same coordinates
        if (base_x == 0) or (base_y == 0):
            return

        # applying Pythagora on the triangles  (anchor1, anchor 2, target) and (anchor2, anchor 3, target)
        # considering the cartesian system of {anchor 1 (0,0);anchor 2 (0, base) }
        # calculating dx = x and dy = |y| with (x,y) the tag's coordinates in the cartesian system of (anchor1, anchor 2)
        r1 = anchor1.get_distance(target)
        r2 = anchor2.get_distance(target)
        r3 = anchor3.get_distance(target)

        # d_print("rangings: ")
        # d_print(anchor1.name, anchor2.name, anchor3.name)
        # d_print(r1,r2,r3)

        dx = ( pow(r2,2) - pow(r1,2) + pow(base_x,2) ) / ( 2 * base_x)
        dy = ( pow(r2,2) - pow(r3,2) + pow(base_y, 2) ) / ( 2 * base_y)

        # computing dz
        dz_square = pow(r2, 2) - (pow(dx, 2) + pow(dy, 2))
        if dz_square > 0:
            dz = math.sqrt(dz_square)
        else:
            dz =  0

        # d_print("dx / dy / dz")
        # d_print(dx, dy, dz)
        # coordinate changes -> calculating the coordiantes in the global cartesian system
        # vect_o denotes the vector from the origin to anchor 1;
        # vect_a denotes the vector from anchor 1 to the tag

        # z is assumed to be 0
        # calculations are exclusively based on x,y

        # calculating vect_base_x and vect_base_y coordinates in the global cartesian system
        # vectors A2->A1 and A2-> A3 are orthognal
        vect_base_x  = [(anchor1.x - anchor2.x) / base_x,(anchor1.y - anchor2.y) / base_x, (anchor1.z - anchor2.z) / base_x ]
        vect_base_y = [(anchor3.x - anchor2.x) / base_y,(anchor3.y - anchor2.y) / base_y, (anchor3.z - anchor2.z) / base_y ]

        # computing third vector required for cartesian orthonormal system

        # cross-product
        vect_base_z = np.cross(vect_base_x, vect_base_y)
       
        # normalization
        base_z_norm = math.sqrt(pow(vect_base_z[0], 2) + pow(vect_base_z[1], 2) + pow(vect_base_z[2], 2))
        vect_base_z /= base_z_norm

        # getting origin
        vect_o = [anchor2.x, anchor2.y, anchor2.z]

        # d_print(vect_base_x, vect_base_y, vect_base_z, vect_o)

        # preparing solutions 
        s1 = vect_o
        s2 = s1.copy()

        # computing first solution- 
        s1 = [vect_base_x[0] * dx + vect_base_y[0] * dy + vect_base_z[0] * dz,
         vect_base_x[1] * dx + vect_base_y[1] * dy + vect_base_z[1] * dz,
         vect_base_x[2] * dx + vect_base_y[2] * dy + vect_base_z[2] * dz ]

        # computing second solution
        # s2 symmetric to s1 about (x,y) plan -> dz = -dz
        s2 = [vect_base_x[0] * dx + vect_base_y[0] * dy - vect_base_z[0] * dz,
         vect_base_x[1] * dx + vect_base_y[1] * dy - vect_base_z[1] * dz,
         vect_base_x[2] * dx + vect_base_y[2] * dy - vect_base_z[2] * dz ]


        # determining which one of the two solution is the right one based on MSE of the other rangings
        rangings = []
        for anchor in (self.anchors):
            # skipping anchors 1,2,3 as they will have a mse of 0
            if anchor.name == anchor1.name or anchor.name == anchor2.name or anchor.name == anchor3.name:
                continue
            rangings.append(anchor.get_distance(target))
        # converting solutions from list to tuple
        s1 = tuple(s1)
        s2 = tuple(s2)

        # comparing the mean squared error for both solution and picking the best one
        mse1 = self.mse(rangings, s1)
        mse2 = self.mse(rangings, s2)

        if mse1 > mse2:
            return(s2,mse2)
        else:
            return(s1,mse1)


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


if __name__ == "__main__":
    vect_a = (7,5,2)
    vect_b = (3, -5, 2)
    vect_c = World.compute_orthogonal_vector(vect_a, vect_b)
    print(vect_c)
    