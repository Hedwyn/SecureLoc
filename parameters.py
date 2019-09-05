## SecureLoc mode and DEBUG parameters
HEADLESS = False
DEBUG = 0
VERBOSE = 0
ENABLE_LOGS = 1
PLAYBACK = True
MEASURING = False
HOST = '169.254.1.1'   # IP address of the MQTT broker

PORT = 80              # Arbitrary non-privileged port

## Standard mode
T = 0.1 # sample time (s), should match the sample time of the hardware
NB_RANGINGS = 25 # size of the list that keeps track of the last rangings

## Measurements mode parameters
SQUARE_SIZE = 0.304
MSE_THRESHOLD = 0.6
TILES = False  # Gives the coordinates with a grid model with a resolution of SQUARE_SIZE
NB_BYTES = 4
NB_MES = 500
NB_REST = 50
START_DELAY = 1

## audio signals for the measurement mode
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


## Playback parameters
ACCELERATION = 1.0  #used by Tkinter menu. Allows accelerating the playback
REFRESH_TIME = 0.2  #default position refresh time. Decreased by ACCELERATION.

## anchors and robots
def is_bot_id(ID):
    """checks if the id provided refers to a bot"""
    return( (len(ID) > 2) and (ID[-3] == 'b') )

NB_BOTS = 2
anchors_labels = ['01',
                  '02',
                  '03',
                  '04']
bots_labels = ['01','02']
bots_id = ["0000000000000b01",
           "0000000000000b02"]

colorList = ['orange', 'red'] # used for the robots representation


## directories and files
LOGSFILE = 'measurements/logs'
LOGSRANGINGS = 'rangings/logs'
LOGSFILE_PLAYBACK = 'measurements/raw/logs'
LOGSRANGINGS_PLAYBACK = 'rangings/playback/logs'

MQTT_REPO = 'mqtt'
POS_REPO = 'pos'
MEASUREMENTS_REPO = 'measurements'
PLAYBACK_REPO = 'playback'

JSON_DIR = 'json'
PLAYBACK_DIR = 'Playback'
ROOT = 'SecureLoc/anchors_data/'


## localization parameters

# If both GN and ITERATIVE are disabled the position is calulated only with weighted centroid
RANDOM_SEARCH = False # notifies that GN and iterative algorithm should use the default pos as starting point
GN = False # notifies that Gauss-Newton algorithm should be used for position computation
ITERATIVE = False # used only when GN is disabled. Notifies that iterative localization should be used for position computation
DEFAULT_POS = (0.9,2.4,0) # default position; center of the platform
NB_STEPS = 20 #Steps number for position iterative resolution

# Filters & speed/acceleration computation parameters
SPEED_BUFFER_LEN = 5 #size of the list storing the last speed measurements
POSITIONS_BUFFER_LEN = 5 #size of the list storing the last positions measurements
ACC_BUFFER_LEN = 5

DEFAULT_ACC_THOLD = 10 #THold for SAT filter
STEP = 1 # Steps for SAT filter


# correction default factors
correction_coeff = {'01': 0.7,'02':  0.7,'03': 0.7,'04':0.7}
correction_offset = {'01':0.,'02':0.,'03':0.,'04':0.}



## Menu parameters

MENU_LABELS = ['Coeff {A}','Coeff {B}','Coeff {C}','Coeff {D}',
                  'Offset{A}','Offset{B}','Offset{C}','Offset{D}']


## special prints and conversion functions


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
    dic = {"01":"0000000000000b01",
           "02":"0000000000000b02"
           }
    return(dic[name])
