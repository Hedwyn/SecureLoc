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

@file particle_filters.py
@author Baptiste Pestourie
@date 2019 July 1st
@brief Implementation of a particle filter-based approach for positioning
@see https://github.com/Hedwyn/SecureLoc
"""

## subpackages
from ips.core.parameters import *

## other libraries
import math
import random




class Node:
    """Represents any node of the map, mobile or static.
    Node can be defined as reference points, in which case they will be involved in localization process by giving their distances to other nodes"""
    def __init__(self,x,y,z,name = 'Anonymous', is_ref = False):
        self.x = x
        self.y = y
        self.z = z
        self.name = name
        self.is_ref = is_ref
        self.noise = 0

    def get_distance_to_pos(self,pos):
        """Returns the distance to a given position"""
        (x,y,z) = pos
        distance = math.sqrt(pow(self.x - x, 2) + pow(self.y - y, 2) + pow(self.z - z, 2))
        return(distance)

    def get_distance(self,node):
        """Returns the distance to a given node"""
        distance = self.get_distance_to_pos(node.get_pos())
        return(distance)

    def get_distance_noisy(self,pos):
        """Returns the distance to a given position after applying the noise generated"""
        distance = self.get_distance(pos)
        return(distance + self.noise)

    def generate_noise(self):
        """Generates random noise on the rangings returned for this node"""
        self.noise = random.gauss(HF_SIGMA,HF_MU)

    def get_pos(self):
        """Returns the position of the node"""
        return(self.x, self.y, self.z)

    def move(self,pos):
        """Sets the position of the node"""
        (x,y,z) = pos
        self.x = x
        self.y = y
        self.z = z


class Particle(Node):
    """Particles are a particular type of node used for particle filters.
    Particles represent potential positions of a given target, associated with a certain likelihood. See particle filters for more information"""
    def __init__(self,x,y,z):
        super().__init__(x,y,z)
        self.likelihood = 0
        self.previous_particle = None
        self.speed = None

    def show(self):
        (x,y,z) = self.get_pos()
        pos_string = "(" + str(x)[:4] + ", " + str(y)[:4] + ", " + str(z)[:4] + ")"
        print("Part. " + pos_string + str("  likelihood: ") + str(self.likelihood)[:4])

    def link_previous_particle(self, particle):
        self.previous_particle = particle
        self.shorten_particle_len()

    def shorten_particle_len(self, len = MAX_PARTICLE_CHAIN_LEN):
        """Shortens the particle chain if its length exceeds the threholds"""
        iterator = self
        depth = 1
        while iterator.previous_particle:
            depth += 1
            if (depth > len):
                iterator.previous_particle = None
            else:
                iterator = iterator.previous_particle        

    def get_depth(self):
        """Returns the depth of the particle recursive chain"""
        depth = 1
        iterator = self
        while iterator.previous_particle:
            depth += 1
            iterator = iterator.previous_particle
        return(depth)

    def get_speed_chain(self):
        """returns the vector of the speeds all the particles of the chain """
        speed_vect = []
        particle = self
        while particle and particle.speed:
            speed_vect.append(particle.speed)
        return(speed_vect)

    def get_chain_likelihood(self):
        """ Returns the total likelihood of a particle chain. A particle chain represents a potential trajectory"""
        total_likelihood = self.likelihood
        p = self.previous_particle
        likelihood_coefficient = 1
        while p:
            total_likelihood += p.likelihood * likelihood_coefficient
            likelihood_coefficient *= LKH_DECREASE_FACTOR
            p = p.previous_particle
        return(total_likelihood)

    def show_trajectory(self):
        """ Displays the trajectory associated with the particle chain"""
        iterator = self
        trajectory = "Current trajectory:\n"
        while iterator:
            (x, y, z) = iterator.get_pos()
            str_pos = '{' + str(x)[:5] + ';' + str(y)[:5] + ';' + str(z)[:5] + '}'
            trajectory += str_pos
            trajectory += "->"
            iterator = iterator.previous_particle
        print(trajectory)

    def compute_speed(self):
        """ Calculates the speed associated to the particle chain"""
        speed_vect_x = []
        speed_vect_y = []
        speed_vect_z = []
        iterator = self
        while iterator.previous_particle:
            (x,y,z) = iterator.get_pos()
            (prev_x, prev_y, prev_z) = iterator.previous_particle.get_pos()
            speed_vect_x.append(x - prev_x)
            speed_vect_y.append(y - prev_y)
            speed_vect_z.append(z - prev_z)

            


class ParticleFleet:
    """An instance of indoor positioning system. Contains different sets of nodes and provide the localization-related functions"""
    def __init__(self):
        self.anchors = {}
        self.tags = {}
        self.rangings = {}
        self.particles = {}

    def init_anchors(self,anchors_list):
        """Registers the IPS anchors as reference particles"""
        print("initializing anchors...")
        for anchor in anchors_list:
            self.anchors[anchor.name] = Node(anchor.x, anchor.y, anchor.z, is_ref = True)

    def register_tag_potential_positions(self, tag, positions):
        """Registers the positions calculated for a tag by trilateration"""  
        self.tags[tag] = positions
        if not(tag in self.particles):
            self.particles[tag] = []

    def register_tag_rangings(self,tag, rangings):
        """Register the ranging values measured by the anchors for the given target"""
        self.rangings[tag] = rangings

    def get_rangings(self,tag):
        """Returns the ranging values measured by the anchors for the given target"""
        return(self.rangings[tag])

    def get_all_trilateration_solutions(self, target):
        """Returns all the solutions calcualted with trilateration for the target tag"""
        return(self.tags[target])           

    def get_distances_to_pos(self, pos):
        output = {}
        distances = []
        for key in self.anchors:
            anchor = self.anchors[key]
            distance = anchor.get_distance_to_pos(pos)
            distances.append(distance)
        return(distances)

    def get_mse(self, rangings,pos):
        distances = self.get_distances_to_pos(pos)
        mse = 0
        for idx,distance in enumerate(distances):
            mse += math.sqrt(pow(rangings[idx] - distance, 2))
        return(mse)

    def generate_particles(self,target):
        # getting trilateration solutions from anchor pairs
        positions = self.get_all_trilateration_solutions(target)
        randomly_generated_positions = []
        particle_duplication_factor = PARTICLES_FLEET_SIZE - len(positions)

        # generating random particles as centroid with random coefficients of trilateration solutions
        for i in range(particle_duplication_factor):
            coeff_x = []
            coeff_y = []
            coeff_z = []
            for pos in positions:
                coeff_x.append(random.random())
                coeff_y.append(random.random())
                coeff_z.append(random.random())
            sum_x = sum(coeff_x)
            sum_y = sum(coeff_y)
            sum_z = sum(coeff_z)
            random_pos_x = 0
            random_pos_y = 0
            random_pos_z = 0
            for i, pos in enumerate(positions):
                (x,y,z) = pos
                random_pos_x +=  x * coeff_x[i] / sum_x
                random_pos_y += y * coeff_y[i] / sum_y
                random_pos_z += z * coeff_z[i] / sum_z
            random_pos = (random_pos_x, random_pos_y, random_pos_z)
            randomly_generated_positions.append((random_pos))
        final_positions = positions + randomly_generated_positions


        # creating particles

        for pos in final_positions:
            (x,y,z) = pos
            particle = Particle(x,y,z)
            self.particles[target].append(particle)


    def particles_resampling(self, target):
        """Resamples the particle fleet. The step is mandatory after each iteration. 
        Particles with high likelihood are duplicated; everything is calculated by random sampling"""

        # getting the current particle fleet
        particles_fleet = self.particles[target]

        # calculating particles likelihood
        self.compute_particles_likelihood(target)
        lkh = [particle.likelihood for particle in particles_fleet]

        # calculating the cumulative probability distribution based on lieklihood
        cumul = 0
        cum_lkh = []
        for i,l in enumerate(lkh):
            cumul += l
            cum_lkh.append(cumul)

        total_likelihood = sum(lkh)

        # creating a new particle fleet -> sampling {PARTICLE_FLEET_SIZE} particles
        resampled_particles_fleet = []
        for i in range(PARTICLES_FLEET_SIZE):
            ran = random.uniform(0,total_likelihood)
            idx = 0
            for l in cum_lkh:
                if ran < l:
                    break
                idx+= 1

        # keeping the track of the previous particle for each new particle created
            original_particle = particles_fleet[idx]
            (x,y,z) = original_particle.get_pos()
            copied_particle = Particle(x,y,z)
            copied_particle.link_previous_particle(original_particle)
            resampled_particles_fleet.append(copied_particle)

        # registering the new particle fleet
        self.particles[target] = resampled_particles_fleet


    def move_particles(self,target):
        particles_fleet = self.particles[target]
        for particle in particles_fleet:
            (x,y,z) = particle.get_pos()
            # creating speed vector
            if (MODE_3D):
                (sx, sy, sz) = MotionGenerator.generate_random_speed()
            else:
                (sx, sy, sz) = MotionGenerator.generate_random_speed_2D()

            # checking z value
            if (Z_POSITIVE):
                if (z + sz  < 0):
                    sz = -z
            
            # moving particle
            particle.move((x + sx, y + sy, z + sz))


    def show_particles_fleet(self,target):
        particles_fleet = self.particles[target]
        for particle in particles_fleet:
            particle.show()

    def output_solution_particle(self, target):
        """Outputs the most likely solution i.e. the particle with highest likelihood"""
        particles_fleet = self.particles[target]
        max_val = 0
        max_idx = 0
        for i,p in enumerate(particles_fleet):
            likelihood = p.get_chain_likelihood()
            if likelihood > max_val:
                max_idx = i
                max_val = likelihood
        # print("Chained likelihood " + str(max_val))
        return(particles_fleet[max_idx])

    def compute_particles_likelihood(self,target):
        rangings = self.get_rangings(target)
        for particle in self.particles[target]:
            mse = self.get_mse(rangings, particle.get_pos())
            particle.likelihood = 1 / (mse + RESOLUTION)
            #particle.show()



class MotionGenerator:
    """Generates node displacements, either random or assetion-based"""
    @staticmethod
    def generate_random_speed(max_speed = MAX_SPEED):
        """Generates a random speed 3D vector, withtin the given maximum norm. 
        There is a certain probability to pick a null speed, corresponding to still particles. This probability can bet set in parameters, 
        and should be chosen according to the application"""
        # A given % of the random speed vectors should correspond tu still particle, i.e., null speed
        # The probability to sample a null speed is given by STILL_NODE_PROBABILITY
        is_still = random.random()
        if (is_still) < STILL_NODE_PROBABILITY:
            speed = (0,0,0)
        else:
            # if the particle is not still, sampling speed
            speed_norm = random.uniform(0, max_speed)


            speed_x = random.random()
            speed_y = random.random()
            speed_z = random.random()

            sign_x = random.choice([-1,1])
            sign_y = random.choice([-1,1])
            sign_z = random.choice([-1,1])


            speed_x = speed_x * speed_norm /(speed_x + speed_y + speed_z)
            speed_y = speed_y * speed_norm /(speed_x + speed_y + speed_z)
            speed_z = speed_z * speed_norm /(speed_x + speed_y + speed_z)

            speed = (sign_x * speed_x,sign_y * speed_y, sign_z * speed_z)
        return(speed)

    def generate_random_speed_2D(max_speed = MAX_SPEED):
        """Generates a random speed 2D vector, withtin the given maximum norm. 
        There is a certain probability to pick a null speed, corresponding to still particles. This probability can bet set in parameters, 
        and should be chosen according to the application"""
        # A given % of the random speed vectors should correspond tu still particle, i.e., null speed
        # The probability to sample a null speed is given by STILL_NODE_PROBABILITY
        is_still = random.random()
        if (is_still) < STILL_NODE_PROBABILITY:
            speed = (0,0,0)
        else:
            # if the particle is not still, sampling speed
            speed_norm = random.uniform(0, max_speed)
            speed_x = random.random()
            speed_y = random.random()

            sign_x = random.choice([-1,1])
            sign_y = random.choice([-1,1])

            speed_x = speed_x * speed_norm /(speed_x + speed_y)
            speed_y = speed_y * speed_norm /(speed_x + speed_y)
            speed = (sign_x * speed_x,sign_y * speed_y, 0)

        return(speed)


# if __name__ == "__main__":
