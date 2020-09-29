import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from ips_simulator import Node, Particle
from ips.core.parameters import W,L,H

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
