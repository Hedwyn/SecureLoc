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

@file Menu.py
@author Baptiste Pestourie
@date 2018 March 1st
@brief Interface for the localization engine control - triggers filtering & attack simulation
@see https://github.com/Hedwyn/SecureLoc
"""


from tkinter import *
import tkinter as tk
from tkinter import ttk
from threading import Thread
import time as time
from parameters import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys
from functools import partial
from multiprocessing import Process, Queue


class Menu(Thread):
    """Interface for the localization engine control - triggers filtering & attack simulation"""
    def __init__(self):
        Thread.__init__(self)
        #super(Menu, self).__init__()

        self.scale = []
        self.var = []
        self.accel = ACCELERATION
        self.anchors_list = []
        self.tags_list = []
        self.attack_list = []
        self.attack_offset = None
        self.root = None
        self.frozen = False


        self.mse = None


        self.hidden = True
        self.frame = None
        self.MSE = []
        self.canvas = None
        self.application_pipe = None


    def update_mse(self,mse):
        self.MSE.append(mse)
        if len(self.MSE) == 20:
            self.MSE.pop()





    def update_param(self,value,idx):
        """handler for rangings correction parameters updating"""
        global correction_coeff
        global correction_offset


        if (idx < len(correction_coeff)):
            correction_coeff[ anchors_labels[idx] ] = float(value)
        elif(idx < 2 * len(correction_coeff)):
            correction_offset[ anchors_labels[idx - len(correction_coeff) ]] = float(value)
        else:
            # acceleration

            self.accel = value





    def run(self):
        """Initializes Tkinter window, scales & buttons"""
        self.root = Tk()

        # Window configuration
        self.root.configure(background = "#dcecf5")
        print("root is " + str(self.root))
        # creating display button
        display_button = Button(self.root, text = "Corrections",background = "#dcecf5", command = self.display_corrections)
        display_button.pack()
        # creating the scales
        nb_anchors = len(anchors_labels)
        acceleration = DoubleVar()
        for i in range(2 * nb_anchors):
            # variable initialization


            self.var.append( DoubleVar() )
            #
            # self.scale.append( Scale(self.root, variable = self.var[i], label = MENU_LABELS[i],
            #                     length = 200, orient = HORIZONTAL, from_ = -2.0 , to = 2.0,
            #                     digits = 4, resolution = 0.01,background = "#dcecf5",
            #                     command = lambda value,idx = i : self.update_param(value,idx) ) )
            # if ( i < nb_anchors):
            #     # correction coeff initialization
            #     self.scale[i].set( correction_coeff[ anchors_labels[i] ] )
            # else:
            #     # correction offset initialization
            #     self.scale[i].set( correction_offset[ anchors_labels[i - 4] ] )

            #☺self.scale[i].grid(row = 0, column = 0)(anchor = CENTER)

        # creating reset button
        reset_button = Button(self.root, text = "Reset",background = "#dcecf5", command = self.reset)
        reset_button.pack()

        ## freeze button
        freeze_button = Button(self.root, text = "Freeze",background = "#dcecf5", command = self.freeze)
        freeze_button.pack()

        # creating show MSE button
        graph_button = Button(self.root, text = "Show MSE",background = "#dcecf5", command = self.show_MSE)
        graph_button.pack()

        # fictive anchor creation button
        fictive_anchor_pop_btn = Button(self.root, text = "Create Fictive Anchor",background = "#dcecf5", command = self.create_fictive_anchor)
        self.fictive_anchor_x = Entry(self.root)
        self.fictive_anchor_y = Entry(self.root)
        self.fictive_anchor_z = Entry(self.root)
        fictive_anchor_pop_btn.pack()
        self.fictive_anchor_x.pack()
        self.fictive_anchor_y.pack()
        self.fictive_anchor_z.pack()

        # fictive tag creation button
        fictive_tag_pop_btn = Button(self.root, text = "Create Fictive Tag",background = "#dcecf5", command = self.create_fictive_tag)
        self.fictive_tag_x = Entry(self.root)
        self.fictive_tag_y = Entry(self.root)
        self.fictive_tag_z = Entry(self.root)
        fictive_tag_pop_btn.pack()
        self.fictive_tag_x.pack()
        self.fictive_tag_y.pack()
        self.fictive_tag_z.pack()




        if PLAYBACK:
            accel_button = Scale(self.root, variable = acceleration, label = "Playback Speed",
                                    length = 200, orient = HORIZONTAL, from_ = 0.5 , to = 50,
                                    digits = 4, resolution = 0.5,background = "#dcecf5",
                                    command = lambda value,idx = (2 * len(correction_coeff)) : self.update_param(value,idx) )
            accel_button.set(ACCELERATION)
            accel_button.pack()
        
        self.root.mainloop()

    def generate_attacks_panel(self):
        ## attacks spinbox
        attacks_label = ttk.Label(self.root, text = "Attack")
        attacks_label.pack()
        self.attacks = tk.StringVar()
        self.attack_spinbox = Spinbox(self.root, values= self.attack_list , textvariable=self.attacks)
        self.attack_spinbox.pack()

        ## attacks offset entry
        self.attack_offset_label = Label(self.root, text = "Attack Offset")
        self.attack_offset =  tk.Entry(self.root)
        self.attack_offset_label.pack()
        self.attack_offset.pack()


        ## anchors buttons
        self.anchors_btns = []
        for anchor in self.anchors_list:
             self.anchors_btns.append(Button(self.root, text = anchor,background = "#dcecf5", command = partial(self.simulate_attack,anchor)))

        anchors_label = ttk.Label(self.root, text = "Anchors")
        anchors_label.pack()

        for btn in self.anchors_btns:
            btn.pack()

        ## tags buttons
        self.tags_btns = []
        for tag in self.tags_list:
             self.tags_btns.append(Button(self.root, text = tag,background = "#dcecf5", command = partial(self.simulate_attack,tag)))


        tags_label = ttk.Label(self.root, text = "Tags")
        tags_label.pack()

        for btn in self.tags_btns:
            btn.pack()

    def freeze(self):
        """Freezes the execution in the 3D engine"""

        self.frozen = not(self.frozen)
        self.application_pipe.send({"Freeze":self.frozen})
        print("Frozen state " + str(self.frozen))

    def create_fictive_anchor(self):
        """Creates an anchor at the given x,y,z coordinates"""
        print("creating anchor at pos" + self.fictive_anchor_x.get() + self.fictive_anchor_y.get() + self.fictive_anchor_z.get())
        try:
            x_coord = float(self.fictive_anchor_x.get())
            y_coord = float(self.fictive_anchor_y.get())
            z_coord = float(self.fictive_anchor_z.get())
            pos = (x_coord, y_coord, z_coord)
        except:
            print("Unvalid coordinates. Please provide floats")
            return

        if self.application_pipe:
            print("sending to application pipe")
            data = {"anchor_position": pos}
            self.application_pipe.send(data)

    def create_fictive_tag(self):
        """Creates an tag at the given x,y,z coordinates"""
        print("creating tag at pos" + self.fictive_tag_x.get() + self.fictive_tag_y.get() + self.fictive_tag_z.get())
        try:
            x_coord = float(self.fictive_tag_x.get())
            y_coord = float(self.fictive_tag_y.get())
            z_coord = float(self.fictive_tag_z.get())
            pos = (x_coord, y_coord, z_coord)
        except:
            print("Unvalid coordinates. Please provide floats")
            return

        if self.application_pipe:
            print("sending to application pipe")
            data = {"tag_position": pos}
            self.application_pipe.send(data)


    def display_corrections(self):
        """ Hide/display button for ranging correction scales"""
        if self.hidden:
            for s in self.scale:
                s.pack()
            self.hidden = False
        else:
            for s in self.scale:
                s.pack_forget()
            self.hidden = True


    def show_MSE(self):
        # deleting old frame
        if self.frame is not(None):
            self.frame.destroy()
        self.frame = Frame(self.root,width=100,height=100)
        f = plt.Figure(figsize=(5,5), dpi=100)
        a = f.add_subplot(111)
        a.plot([i for i in range(len(self.MSE))],self.MSE)

        self.canvas = FigureCanvasTkAgg(f, self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.frame.pack()

    def simulate_attack(self,target):
        """Simulates the chosen attack in the spinbox on the chosen target"""
        print("target is " + target)
        print(self.root)
        if self.application_pipe:
            self.application_pipe.send({"Attack": self.attacks.get(), "Target": target, "Offset": self.attack_offset.get()})



    def space(self):
        """draws a seperator"""
        separator = Frame(width=500, height=4, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=5)



    def callback(self):
        """Exit function"""
        #self.root.update_idletasks()
        self.root.destroy()
        #sys.exit()




    def getAccel(self):
        """Returns acceleration"""
        return(float(self.accel))


    def reset(self):
        """Brings back correction scales to 0"""
        for i,s in enumerate(self.scale):
            if ( i < len(self.scale) / 2):
                # correction coeff reset
                s.set( CORRECTION_COEFF[ anchors_labels[i] ] )
            else:
                # correction offset reset
                s.set( CORRECTION_OFFSET[ anchors_labels[i - 4] ] )



if __name__ == "__main__":
    Menu()
    menu.attack_list.append("Test")
    menu.anchors_list.append('A')
    menu.anchors_list.append('B')
    menu.tags_list.append("T1")
    menu.generate_attacks_panel()
    time.sleep(1)
