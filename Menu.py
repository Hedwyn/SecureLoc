from tkinter import *
import tkinter as tk
from tkinter import ttk
from threading import Thread
import time as time
from parameters import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys
   
    
class Menu(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.scale = []
        self.var = []
        self.accel = ACCELERATION


        self.mse = None

        self.start()
        self.hidden = True
        self.frame = None
        self.MSE = []
        self.canvas = None
        

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

        # creating display button
        display_button = Button(self.root, text = "Corrections",background = "#dcecf5", command = self.display_corrections)
        display_button.pack()
        # creating the scales
        nb_anchors = len(anchors_labels)
        acceleration = DoubleVar()
        for i in range(2 * nb_anchors):
            # variable initialization
            
            
            self.var.append( DoubleVar() )
            
            self.scale.append( Scale(self.root, variable = self.var[i], label = MENU_LABELS[i],
                                length = 200, orient = HORIZONTAL, from_ = -2.0 , to = 2.0,
                                digits = 4, resolution = 0.01,background = "#dcecf5",
                                command = lambda value,idx = i : self.update_param(value,idx) ) )
            if ( i < nb_anchors):
                # correction coeff initialization
                self.scale[i].set( correction_coeff[ anchors_labels[i] ] )
            else:
                # correction offset initialization
                self.scale[i].set( correction_offset[ anchors_labels[i - 4] ] )

            #☺self.scale[i].pack(anchor = CENTER)
            
        # creating reset button
        reset_button = Button(self.root, text = "Reset",background = "#dcecf5", command = self.reset)
        reset_button.pack()
        
        # creating show MSE button
        graph_button = Button(self.root, text = "Show MSE",background = "#dcecf5", command = self.show_MSE)
        graph_button.pack()


        
        
        if PLAYBACK:
            accel_button = Scale(self.root, variable = acceleration, label = "Playback Speed",
                                    length = 200, orient = HORIZONTAL, from_ = 0.5 , to = 50,
                                    digits = 4, resolution = 0.5,background = "#dcecf5",
                                    command = lambda value,idx = (2 * len(correction_coeff)) : self.update_param(value,idx) )
            accel_button.set(ACCELERATION)
            accel_button.pack()
              
              
        self.root.mainloop()
     
        
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
        
            
       
    def space(self):
        """draws a seperator"""
        separator = Frame(width=500, height=4, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=5)



    def callback(self):
        """Exit function"""
        self.root.update_idletasks()
        sys.exit()
        
    
  

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

    menu = Menu()
    time.sleep(5)

    

