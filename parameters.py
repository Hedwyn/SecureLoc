from tkinter import *
from threading import Thread
import time as time

DEBUG = 0
VERBOSE = 0
ENABLE_LOGS = 1
NB_BOTS = 1
JSON_DIR = 'json'
PLAYBACK_DIR = 'Playback'
PLAYBACK = False 
MEASURING = False

MQTT_REPO = 'mqtt'
POS_REPO = 'pos'
MEASUREMENTS_REPO = 'measurements'
PLAYBACK_REPO = 'playback'

ACCELERATION = 1.0
REFRESH_TIME = 0.2

SQUARE_SIZE = 0.304
TILES = False
NB_BYTES = 4
NB_MES = 200
NB_REST = 15
START_DELAY = 1
SQUARE_SIZE = 0.304
ANCHOR_NAME = 'A'
anchors_labels = ['01',
                  '02',
                  '03',
                  '04']
bots_labels = ['03']
ROOT = 'SecureLoc/anchors_data/'

end_score = [('E4',0.33),
             ('G#4',0.33),
             ('A4',0.33),
             ('B4',0.66),
             ('G#4',0.33),
             ('B4',1.0)
             ]
start_score= [('B5',0.5),
              ('G#5',0.5),
              ('E5',1.0)
              ]

launch_score = [('E6',0.5),
                ('E6',0.5)
                ]

LOGSFILE = 'measurements/logs'
LOGSRANGINGS = 'rangings/logs'
LOGSFILE_PLAYBACK = 'measurements/raw/logs'
LOGSRANGINGS_PLAYBACK = 'rangings/playback/logs'




anchors_id = ["000000000000000a",
              "000000000000000b",
              "000000000000000c",
              "000000000000000d"]

bots_id = ["0001020300010203",
          "0001020300010202"]



colorList = ['orange', 'red'] # used for the robots representation
           

anchors_name = ["1","2","3","4"]

# constants, defines init values for the correction
CORRECTION_COEFF = {'A': 1.,'B':  1.,'C': 1.,'D':1.}
CORRECTION_OFFSET = {'A':0.,'B':0.,'C':0.,'D':0.}

# global var used by the tkinter menu

##correction_coeff = {'A': 1.,'B':  1.,'C': 1.,'D':1.}
##correction_offset = {'A':0.,'B':0.,'C':0.,'D':0.}

##correction_coeff = {'A': 1.0,'B':1.0,'C': 1.0,'D':1.0}
##correction_offset = {'A':-0.40,'B':-0.35,'C':0.30,'D':0.35}

correction_coeff = {'1': 1.,'2':  1.,'3': 1.,'4':1.,'5':1.,'6':1.,'7':1.,
                    '8':1.,'9':1.,'10':1.,'11':1.,'12':1.,'13':1.,'14':1.,'15':1.,}
correction_offset = {'1':0.,'2':-0.20,'3':0.30,'4':0.35,'5':0.,'6':0.,'7':0.,
                    '8':0.,'9':0.,'10':0.,'11':0.,'12':0.,'13':0.,'14':0.,'15':0.}

##correction_coeff = {'A': 1.1,'B':  1.1,'C': 1.1,'D':1.1}
##correction_offset = {'A':0.,'B':-0.40,'C':0.0,'D':0.35}

MENU_LABELS = ['Coeff {A}','Coeff {B}','Coeff {C}','Coeff {D}',
                  'Offset{A}','Offset{B}','Offset{C}','Offset{D}']




T = 0.1 # sample time (s), should match the sample time of the hardware


NB_RANGINGS = 25 # size of the list that keeps track of the last rangings
NB_SAMPLES = 1000 # used for logs reading, maximum number of samples that will be read/replayed 
LOGS_POS = 'logs/logs_pos.txt'
LOGS_RANGING = 'logs/logs_ranging.txt'
LOGS_SPEED = 'logs/logs_speed.txt'



#HOST = '127.0.0.1' #for local server
HOST = '169.254.1.1'                 
PORT = 80              # Arbitrary non-privileged port


SPEED_LIST_SIZE = 5 #size of the list storing the last speed measurements
POS_LIST_SIZE = 5 #size of the list storing the last positions measurements
ACC_LIST_SIZE = 5

# parameters for SAT filter
DEFAULT_ACC_THOLD = 10
STEP = 1

def d_print(msg):
    """print function for debugging"""
    if (DEBUG == 1):
        print(msg)

        
def v_print(msg):
    """print function enabled in verbose mode"""
    if (VERBOSE == 1):
        print(msg)


def id_to_name(id):
    dic = {"01":"1","02":"2","03":"3","04":"4","05":"5","06":"6","07":"7","08":"8",
               "09":"9"}
    if id in dic:        
        return(dic[id])
    else:
        return(id)
    
 
def name_to_id(name):
    dic = {"02":"0001020300010202",
           "03":"0001020300010203"
           }
    return(dic[name])



    
    
class Menu(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.scale = []
        self.var = []
        self.accel = ACCELERATION

        self.position = (0,0,0)
        self.rangings = [0,0,0,0]
        self.start()
      

    def update_param(self,value,idx):
        global correction_coeff
        global correction_offset
        

        if (idx < 4):
            correction_coeff[ anchors_name[idx] ] = float(value)
        elif(idx < 8):
            correction_offset[ anchors_name[idx - 4 ]] = float(value)
        else:
            # acceleration
            
            self.accel = value
            
            
        
        
    
    def run(self):
        
        self.root = Tk()
        #self.scale = []
        #self.var = []
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        # creating the scales
        for i in range(8):
            # variable initialization
            
            acceleration = DoubleVar()
            self.var.append( DoubleVar() )
            
            self.scale.append( Scale(self.root, variable = self.var[i], label = MENU_LABELS[i],
                                length = 200, orient = HORIZONTAL, from_ = -2.0 , to = 2.0,
                                digits = 4, resolution = 0.01,
                                command = lambda value,idx = i : self.update_param(value,idx) ) )
            if ( i < 4):
                # correction coeff initialization
                self.scale[i].set( correction_coeff[ anchors_name[i] ] )
            else:
                # correction offset initialization
                self.scale[i].set( correction_offset[ anchors_name[i - 4] ] )

            self.scale[i].pack(anchor = CENTER)
            
        # creating reset button
        reset_button = Button(self.root, text = "Reset", command = self.reset)
        reset_button.pack()

        accel_button = Scale(self.root, variable = acceleration, label = "Acceleration",
                                length = 200, orient = HORIZONTAL, from_ = 0.5 , to = 50,
                                digits = 4, resolution = 0.5,
                                command = lambda value,idx = 8 : self.update_param(value,idx) )
        accel_button.set(ACCELERATION)
        accel_button.pack()

        
        self.update()   
        self.root.mainloop()
        
    def update_pos(self,pos):
        self.position = pos
        self.root.update_idletasks()

    def update_rangings(self,rangings):
        self.rangings = rangings
        self.root.update_idletasks()

    def draw(self,oldframe = None):

        frame = Frame(self.root,width=100,height=100,relief='solid',bd=1)
        frame.place(x=10,y=10)
        
        

        
        
        position = StringVar()
        rangings = StringVar()

  
    

        position.set(str(self.position))
        rangings.set(str(self.rangings))
      

        
        # creatings labels
        Label(frame, text="Ranging values: ").pack()
        Label(frame, textvariable= rangings ).pack()
        #self.space()

        
        Label(frame, text="Position of robot " + bots_id[1]).pack()
        Label(frame, textvariable= position ).pack()
        #self.space()

        frame.pack()
        if oldframe is not None:
            oldframe.destroy() # cleanup        
        
        return frame

    def update(self,frame=None):
        
        frame = self.draw(frame)
        frame.after(50, self.update, frame) 
        

        
    def space(self):
        separator = Frame(width=500, height=4, bd=1, relief=SUNKEN)
        separator.pack(fill=X, padx=5, pady=5)



    def callback(self):
        self.root.quit()

    def getAccel(self):
        return(float(self.accel))
        

    def reset(self):
        for i in range(8):
            
            
           
            if ( i < 4):
                # correction coeff reset
                self.scale[i].set( CORRECTION_COEFF[ anchors_name[i] ] )
            else:
                # correction offset reset
                self.scale[i].set( CORRECTION_OFFSET[ anchors_name[i - 4] ] )

            

        
        


if __name__ == "__main__":

    menu = Menu()
    time.sleep(1)
    print("now")
    menu.update_pos((2,2,2))
    menu.update_rangings([1,1,1,1])
    time.sleep(5)
    
    


    
    
    
    



