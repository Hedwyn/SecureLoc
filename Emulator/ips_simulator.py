import math
import random
from ips.core.parameters import *
from motion_generator import MotionGenerator

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
        (x,y,z) = pos
        distance = math.sqrt(pow(self.x - x, 2) + pow(self.y - y, 2) + pow(self.z - z, 2))
        return(distance)

    def get_distance(self,node):
        distance = self.get_distance_to_pos(node.get_pos())
        return(distance)

    def get_distance_noisy(self,pos):
        distance = self.get_distance(pos)
        return(distance + self.noise)

    def generate_noise(self):
        self.noise = random.gauss(HF_SIGMA,HF_MU)

    def get_pos(self):
        return(self.x, self.y, self.z)

    def move(self,pos):
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

    def get_depth(self):
        """Returns the depth of the particle recursive chain"""
        depth = 1
        while self.previous_particle:
            depth += 1
        return(depth)

    def get_speed_chain(self):
        """returns the vector of the speeds all the particles of the chain """
        speed_vect = []
        particle = self
        while particle and particle.speed:
            speed_vect.append(particle.speed)
        return(speed_vect)

    def get_chain_likelihood(self):
        total_likelihood = self.likelihood
        p = self.previous_particle
        while p:
            total_likelihood += p.likelihood
            p = p.previous_particle
        return(total_likelihood)


class IPS:
    """An instance of indoor positioning system. Contains different sets of nodes and provide the localization-related functions"""
    def __init__(self):
        self.anchors = {}
        self.tags = {}
        self.particles = {}

    def append_node(self, node):
        if node.is_ref:
            self.anchors[node.name] = node
        else:
            self.tags[node.name] = node
            self.particles[node.name] = []

    def generate_noise(self):
        for anchor in [self.anchors[key] for key in self.anchors]:
            anchor.generate_noise()

    def get_rangings(self, target):
        output = {}
        rangings = []
        for key in self.anchors:
            anchor = self.anchors[key]
            distance = anchor.get_distance_noisy(self.tags[target])
            #print("Anchor " + anchor.name + " : " + str(distance))
            rangings.append(distance)
        return(rangings)

    def get_distances_to_pos(self, pos):
        output = {}
        distances = []
        for key in self.anchors:
            anchor = self.anchors[key]
            distance = anchor.get_distance_to_pos(pos)
            distances.append(distance)
        return(distances)

    def get_all_rangings(self):
        for key in self.tags:
            self.get_rangings(key)

    def get_mse(self, rangings,pos):
        distances = self.get_distances_to_pos(pos)
        mse = 0
        for idx,distance in enumerate(distances):
            mse += math.sqrt(pow(rangings[idx] - distance, 2))
        return(mse)

    def trilateration_2D(self, ref1, ref2, target):
        # applying Pythagora
        base = ref1.get_distance(ref2)

        # computing relative coordinates
        r1 = ref1.get_distance_noisy(target)
        r2 = ref2.get_distance_noisy(target)


        X= (pow(r1,2) + pow(base, 2) - pow(r2,2)) / (2 * base)
        Y_sq = pow(r1,2) - pow(X,2)
        if Y_sq > 0:
            Y = math.sqrt(Y_sq)
        else:
            Y = 0

        # coordinates change
        (x1, y1, z1) = ref1.get_pos()
        (x2, y2, z2) = ref2.get_pos()

        # with the current coordinates, x axis vector is (dx, dy) and y axis vector (-dy, dx)
        dx = (x2 - x1) / base
        dy = (y2 -y1) / base

        # computing the two solutions

        x_out1 = X * dx - Y * dy + x1
        y_out1 = X * dy + Y * dx + y1
        sol_1 = (x_out1, y_out1, 0)

        x_out2 = X * dx + Y * dy + x1
        y_out2 = X * dy - Y * dx + y1
        sol_2 = (x_out2, y_out2, 0)

        # print("Coordinates of solution 1 = " + str(sol_1))
        # print("Coordinates of solution 2 = " + str(sol_2))

        return(sol_1, sol_2)

    def get_all_trilateration_solutions(self,target):
        solutions = []
        anchors_list = [self.anchors[key] for key in self.anchors]
        rangings = self.get_rangings(target.name)
        for idx, anchor in enumerate(anchors_list):
            for i in range(idx + 1, len(anchors_list)):
                ref1 = anchor
                ref2 = anchors_list[i]
                (sol_1, sol_2) = self.trilateration_2D(ref1, ref2,target)
                sol = self.reduce_to_one_solution(rangings,(sol_1, sol_2))
                solutions.append(sol)
                # solutions.append(sol_1)
                # solutions.append(sol_2)
        return(solutions)

    def reduce_to_one_solution(self, rangings, solutions_tuple):
        sol_1, sol_2 = solutions_tuple
        mse1 = self.get_mse(rangings, sol_1)
        mse2 = self.get_mse(rangings, sol_2)

        if mse1 > mse2:
            return(sol_2)
        else:
            return(sol_1)


    def weighted_centroid_2D(self,target):
        solutions = self.get_all_trilateration_solutions(target)
        rangings = self.get_rangings(target.name)
        mse_inv_sum = 0
        coeff = []
        for solution in solutions:
            mse = self.get_mse(rangings,solution)
            mse_inv = 1 / (mse + 0.0000001)
            mse_inv_sum += mse_inv
            coeff.append(mse_inv)



        # weighted centroid
        x_out = 0
        y_out = 0
        for i, sol in enumerate(solutions):
            (x,y,z) = sol
            x_out += x * coeff[i]
            y_out += y *coeff[i]

        x_out = x_out / mse_inv_sum
        y_out = y_out / mse_inv_sum

        return((x_out,y_out, 0))

    def generate_particles(self,target):
        # getting trilateration solutions from anchor pairs
        positions = self.get_all_trilateration_solutions(target)
        randomly_generated_positions = []

        # generating random particles as centroid with random coefficients of trilateration solutions
        for i in range(PARTICLE_DUPLICATION_FACTOR):
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
        print("Total number of particles: " + str(len(final_positions)))

        # creating particles

        for pos in final_positions:
            (x,y,z) = pos
            particle = Particle(x,y,z)
            self.particles[target.name].append(particle)

    def particles_resampling(self, target):
        particles_fleet = self.particles[target.name]
        self.compute_particles_likelihood(target)
        self.show_particles_fleet(target)
        lkh = [particle.likelihood for particle in particles_fleet]

        cumul = 0
        cum_lkh = []
        for i,l in enumerate(lkh):
            cumul += l
            cum_lkh.append(cumul)

        total_likelihood = sum(lkh)
        print("cum lkh: " + str(cum_lkh) + " total lkh:" + str(total_likelihood))
        resampled_particles_fleet = []
        for i in range(len(particles_fleet)):
            ran = random.uniform(0,total_likelihood)
            print(ran)
            idx = 0
            for l in cum_lkh:
                if ran < l:
                    break
                idx+= 1
            (x,y,z) = particles_fleet[idx].get_pos()
            copied_particle = Particle(x,y,z)
            resampled_particles_fleet.append(copied_particle)
        #return(resampled_particles_fleet)
        self.particles[target.name] = resampled_particles_fleet
        self.show_particles_fleet(target)

    def move_particles(self,target):
        particles_fleet = self.particles[target.name]
        iterated_particle_fleet = []
        for particle in particles_fleet:
            (x,y,z) = particle.get_pos()
            # creating speed vector
            (sx, sy, sz) = MotionGenerator.generate_random_speed_2D()
            # creating new particle
            p = Particle(x + sx, y + sy, z + sz)

            p.previous_particle = particle
            iterated_particle_fleet.append(p)
        self.particles[target.name] = iterated_particle_fleet

    def show_particles_fleet(self,target):
        particles_fleet = self.particles[target.name]
        for particle in particles_fleet:
            particle.show()

    def output_solution_particle(self, target):
        """Outputs the msot likely solution i.e. the particle with highest likelihood"""
        particles_fleet = self.particles[target.name]
        max = 0
        max_idx = 0
        for i,p in enumerate(particles_fleet):
            likelihood = p.get_chain_likelihood()
            if likelihood > max:
                max_idx = i
                max = likelihood
        return(particles_fleet[i])

    def compute_particles_likelihood(self,target):
        rangings = self.get_rangings(target.name)
        for particle in self.particles[target.name]:
            mse = self.get_mse(rangings, particle.get_pos())
            particle.likelihood = 1 / (mse + 0.1)
            #particle.show()


class NoiseGenerator:
    """generates gaussian noise with tunable variation speed."""
    def __init__(self, mu, offset, period):
        self.mu = mu
        self.offset = offset
        self.period = period
        self.clock_counter = 0
        self.current_noise_value = 0
        self.next_noise_value = 0

    def clock_tick(self):
        self.clock_counter += 1
        if random.randint(0, self.period) == 1:
            self.current_noise_value = self.next_noise_value
            self.generate_gaussian_noise()
        return(self.clock_counter)

    def generate_gaussian_noise(self):
        self.next_noise_value = random.gauss(offset, mu)

    def get_noise(self):
        return(self.current_noise_value)

class RangingNoiseGenerator:
    """Ranging noise is represented by the sum of three noise sources:
        - High-Frequency noise (HF) which represents the measurements fluctuations and are completely random and re-generated at each measurement
        - Low-Frequency Noise (LF) representeing the noise induced by the environment (e.g. movements or interferences), which is varying more occasionally
        - Location-related noise, which is the ranging error associated to a certain lcoation"""

    def __init__(self, ):
        HF_noise = NoiseGenerator(HF_MU_HF_SIGMA)
        LF_noise = NoiseGenerator(LF_MU, LF_SIGMA)
        Location_noise = 0 # TODO

    def set_HF_noise(self, mu, offset):
        self.HF_noise.mu = mu
        self.HF_noise.offset = offset

    def set_LF_noise(self, mu, offset):
        self.LF_noise.mu = mu
        self.LF_noise.offset = offset
