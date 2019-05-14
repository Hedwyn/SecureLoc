from tkinter import *
from threading import Thread
import time as time
from parameters import *
import matplotlib.pyplot as plt
import sys
   
    
class Menu(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.scale = []
        self.var = []
        self.accel = ACCELERATION


        self.mse = None

        self.start()
        self.hidden = False

        
      

    def update_param(self,value,idx):
        """handler for rangings correction parameters updating"""
        global correction_coeff
        global correction_offset
        

        if (idx < 4):
            correction_coeff[ anchors_labels[idx] ] = float(value)
        elif(idx < 8):
            correction_offset[ anchors_labels[idx - 4 ]] = float(value)
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

            self.scale[i].pack(anchor = CENTER)
            
        # creating reset button
        reset_button = Button(self.root, text = "Reset",background = "#dcecf5", command = self.reset)
        reset_button.pack()


        
        
        if PLAYBACK:
            accel_button = Scale(self.root, variable = acceleration, label = "Playback Speed",
                                    length = 200, orient = HORIZONTAL, from_ = 0.5 , to = 50,
                                    digits = 4, resolution = 0.5,background = "#dcecf5",
                                    command = lambda value,idx = 8 : self.update_param(value,idx) )
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
            





        
    def update_mse(self,mse):
        """updates MSE of the last localization"""
        self.mse = mse
        self.root.update_idletasks()
        

        

       

        
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

    

