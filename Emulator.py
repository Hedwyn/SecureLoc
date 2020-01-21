import math
import random
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import copy

NB_ANCHORS = 4
NB_TAGS = 1
START_POS = (2,2,0)

# dimensions
W = 10
L = 10
H = 5

ANCHORS_COORD = [(0,0,0),(L,0,0), (L,W,0), (0,W,0)]

# gaussian noise parameters
sigma = 0
mu = 2
MAX_SPEED = 0.5
PARTICLE_DUPLICATION_FACTOR = 12

class Node:
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
        self.noise = random.gauss(sigma,mu)

    def get_pos(self):
        return(self.x, self.y, self.z)

    def move(self,pos):
        (x,y,z) = pos
        self.x = x
        self.y = y
        self.z = z

class IPS:
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




class Particle(Node):
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



class Scheduler:
    def __init__(self):
        self.ips = None
        self.gui = GUI()
        self.gui.init_figure()
        self.init_ips()
        self.iteration_idx = 0

    def init_ips(self):
        self.ips = IPS()
        print("init IPS")
        for i in range(NB_ANCHORS):
            (x,y,z) = ANCHORS_COORD[i]
            self.ips.append_node( Node(x,y,z, str(i), True) )
        for j in range(NB_TAGS):
            x = random.uniform(0,L)
            y = random.uniform(0,W)
            #z = random.uniform(0,H)
            z= 0
            tag = Node(x,y,z, str(j), False)
            self.ips.generate_noise()
            self.ips.append_node(tag)
            self.ips.generate_particles(tag)
            self.gui.display_particles(self.ips.particles[tag.name])
            print(self.ips.weighted_centroid_2D(tag))
            print("tag " + tag.name + " is at position " + str(tag.get_pos()))


    def iteration(self):
        for tag in [self.ips.tags[key] for key in self.ips.tags]:
            self.ips.generate_noise()
            #self.ips.show_particles_fleet(tag)
            print("Resampling")
            self.ips.particles_resampling(tag)
            #self.ips.show_particles_fleet(tag)
            self.ips.move_particles(tag)
            #print(self.ips.weighted_centroid_2D(tag))
            self.gui.display_particles(self.ips.particles[tag.name])
            p = self.ips.output_solution_particle(tag)
            print(p.get_pos())
            print(p.get_chain_likelihood())
            return(p)
            self.iteration_idx += 1
            #print(p.get_depth())

            #print(str(len(self.ips.particles[tag.name])) + " particles")

    def run(self,n_iterations):
        for i in range(n_iterations):
            self.iteration()

class MotionGenerator:
    @staticmethod
    def generate_random_speed(max_speed = MAX_SPEED):
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
        return(sign_x * speed_x,sign_y * speed_y, sign_z * speed_z)

    def generate_random_speed_2D(max_speed = MAX_SPEED):
        speed_norm = random.uniform(0, max_speed)


        speed_x = random.random()
        speed_y = random.random()


        sign_x = random.choice([-1,1])
        sign_y = random.choice([-1,1])



        speed_x = speed_x * speed_norm /(speed_x + speed_y)
        speed_y = speed_y * speed_norm /(speed_x + speed_y)

        return(sign_x * speed_x,sign_y * speed_y, 0)

class GUI:
    def __init__(self):
        self.ax1 = None
        self.fig1 = None
        self.fig2 = None
        self.ax2 = None

    def init_figure(self):
        self.fig1 = plt.figure()
        self.ax1 = self.fig1.add_subplot(111, projection = '3d')
        self.ax1.set_title("Particles")


    def display_particles(self,particles_list):
        x_list = []
        y_list = []
        z_list = []
        for pos in [particle.get_pos() for particle in particles_list]:
            (x,y,z) = pos
            x_list.append(x)
            y_list.append(y)
            z_list.append(z)
        if self.ax1:
            self.ax1.set_xlim3d([0.0, L])
            self.ax1.set_ylim3d([0.0, W])
            self.ax1.set_zlim3d([0.0, H])
            self.ax1.scatter(x_list[:],y_list[:],z_list[:])
            plt.draw()
            plt.pause(0.2)

    def plot_trace(self,particle):

        self.ax2 = self.fig1.add_subplot(111, projection = '3d')
        self.ax2.set_title("Trace")
        self.fig2 = plt.figure()
        x_list = []
        y_list = []
        z_list = []
        p = particle
        while p:
            (x,y,z) = p.get_pos()
            x_list.append(x)
            y_list.append(y)
            z_list.append(z)
            p = p.previous_particle
        if self.ax2:
            self.ax1.set_xlim3d([0.0, L])
            self.ax1.set_ylim3d([0.0, W])
            self.ax1.set_zlim3d([0.0, H])
            self.ax1.scatter(x_list[:],y_list[:],z_list[:])
            plt.plot()






if __name__ == '__main__':
    random.seed(5)
    # ips = IPS()
    #
    # for i in range(NB_ANCHORS):
    #     (x,y,z) = ANCHORS_COORD[i]
    #     ips.append_node( Node(x,y,z, str(i), True) )
    # for j in range(NB_TAGS):
    #     x = random.uniform(0,L)
    #     y = random.uniform(0,W)
    #     #z = random.uniform(0,H)
    #     z= 0
    #     tag = Node(x,y,z, str(j), False)
    #     print("tag " + tag.name + " is at position " + str(tag.get_pos()))
    #     ips.append_node(tag)
    #
    # ips.generate_noise()
    # ips.get_all_rangings()
    # tag = ips.tags['0']
    #
    # anchor1 = ips.anchors['0']
    # anchor2 = ips.anchors['1']
    # anchor3 = ips.anchors['2']
    # anchor4 = ips.anchors['3']
    # # ips.trilateration_2D(anchor1, anchor2, tag)
    # # ips.trilateration_2D(anchor1, anchor3, tag)
    # # ips.trilateration_2D(anchor1, anchor4, tag)
    # # ips.trilateration_2D(anchor3, anchor4, tag)
    # #print(ips.get_all_trilateration_solutions(tag))
    # print(ips.weighted_centroid_2D(tag))
    # ips.generate_particles(tag)
    # ips.compute_particles_likelihood(tag)
    scheduler = Scheduler()
    scheduler.run(10)
    #print(MotionGenerator.generate_random_speed_2D(10))
