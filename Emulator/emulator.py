import math
import random

from parameters import *
from gui import GUI
from ips_simulator import Node, Particle, IPS




class Scheduler:
    """Global clock for Indoor Positioning System. Provides the refresh frequency, and handles the timing for all IPS-related operations.
    Parameters need to be chosen appropriately to obtain realistic real-time outputs"""
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
