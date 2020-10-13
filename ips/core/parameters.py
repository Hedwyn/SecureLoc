import os

## SecureLoc mode and DEBUG parameters
HEADLESS = False
DEBUG = 0
VERBOSE = 0
ENABLE_LOGS = 1
PLAYBACK = False
EMULATE_MQTT = False
MEASURING = False
TRANSMIT_POSITION = False

# 3D engine parameters
WINDOW_HEIGHT = 1200
WINDOW_WIDTH = 720
BASE_CAM_POS = 2, 5, 1
SCALE = 0.05
TEXT_SCALE = 0.1
TAG_COLOR = 'green'
ANCHOR_COLOR = 'blue'

## MQTT parameters
HOST = '169.254.1.1'   # IP address of the MQTT brokerq
PORT = 80              # Arbitrary non-privileged port
MQTT_TOPICS = ["/distance","/ts1","/ts2","/ts3","/ts4","/skew","/rssi","/fp_power","/fp_ampl2","/std_noise","/temperature", "/differential_distance"]
TOPIC_SERIAL = 'Serial'

## Standard mode
T = 0.1 # sample time (s), should match the sample time of the hardware
NB_RANGINGS = 25 # size of the list that keeps track of the last rangings
REFRESH_PERIOD = 0.0
DMAX = 15 # maximum distance on the platform

## Measurements mode parameters
SQUARE_SIZE = 0.304
MSE_THRESHOLD = 0.6
TILES = False  # Gives the coordinates with a grid model with a resolution of SQUARE_SIZE
NB_BYTES = 4
NB_MES = 50
NB_REST = 10
START_DELAY = 1

## User inputs
UI_REFRESH_TIME = 0.10

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
REFRESH_TIME = 0.02  #default position refresh time. Decreased by ACCELERATION.

## anchors and robots
def is_bot_id(ID):
    """checks if the id provided refers to a bot"""
    return( (len(ID) > 2) and (ID[-3] == 'b') )

NB_BOTS = 1
anchors_labels = ['01',
                  '02',
                  '03',
                  '04',
                  '05',
                  '06',
                  '07',
                  '08'
                  '09']

bots_labels = ['01','02','03','04','05']
bots_id = ["0000000000000b01",
           "0000000000000b02",
           "0000000000000b03",
           "0000000000000b04",
           "0000000000000b05"]

# bots_labels = ['01']
# bots_id = ["0000000000000b01"]      

colorList = ['orange', 'orange','orange','orange','orange'] # used for the robots representation


## directories and files
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/.."  # root directory is parent directory
LOGSFILE = ROOT_DIR + '/logs/json/measurements/logs'
LOGSRANGINGS = ROOT_DIR + '/logs/json/rangings/logs'
LOGSFILE_PLAYBACK = ROOT_DIR + '/logs/json/measurements/raw/logs'
ANCHORS_CONFIG = "anchors.tab"
ANCHORS_PLAYBACK_CONFIG = "anchors_playback.tab"

LOGSRANGINGS_PLAYBACK = '/logs/json/rangings/playback/logs'

LOGS_DIR = ROOT_DIR + "/logs/json/"
MQTT_REPO = LOGS_DIR + 'mqtt'
POS_REPO = LOGS_DIR + 'pos'
MEASUREMENTS_REPO = LOGS_DIR + 'measurements'
PLAYBACK_REPO = LOGS_DIR + 'playback'

PLAYBACK_DIR = ROOT_DIR + '/logs/Playback'
ROOT = 'SecureLoc/anchors_data/'
COOPERATIVE_STREAM = 'cooperative_data'
COOPERATIVE_ROOT = 'SecureLoc' + '/' + COOPERATIVE_STREAM + '/'


## localization parameters
# localization algorithms
WCN = 0 # Weighted centroid 
ITERATIVE = 1 # Weighted centroid + discrete mse-optimizing iterations 
GN = 2  # Gauss-Newton algorithm 
PARTICLES = 3 # Particle filter

# Change localization method here
DEFAULT_LOCALIZATION_ALGORITHM = WCN

# algorithm parameters
RESOLUTION = 0.01 # m, the lowest resolution is 1 cm
Z_POSITIVE = True # indicates that the platform physical configuration does not allow z <0
RANDOM_SEARCH = False # notifies that GN and iterative algorithm should use the default pos as starting point
DEFAULT_POS = (0.9,2.4,0) # default position; center of the platform
NB_STEPS = 10 #Steps number for position iterative resolution
MODE_3D = False

# particle filter 
MAX_SPEED = 0.05
PARTICLES_FLEET_SIZE = 50
MAX_PARTICLE_CHAIN_LEN = 20
STILL_NODE_PROBABILITY = 0.5
LKH_DECREASE_FACTOR = 1

# Filters & speed/acceleration computation parameters
SPEED_BUFFER_LEN = 5 #size of the list storing the last speed measurements
POSITIONS_BUFFER_LEN = 5 #size of the list storing the last positions measurements
ACC_BUFFER_LEN = 5
# SW filter
SW_SIZE = 3
SW_ELIMINATIONS = 1

DEFAULT_ACC_THOLD = 10 #THold for SAT filter
STEP = 1 # Steps for SAT filter

# differential TWR
RMSE_SW_LEN = 10
RMSE_MALICIOUS = 1.0 # indicates that a node is probably malicious

## cooperative methods
ENABLE_COOPERATIVE = True
COOP_DIST_SW_LEN = 5
SECURITY_CHECK_PERIOD = 0.5
COOPERATIVE_DEVIATION_THOLD = 1.0

## trust indicator parameters
TI_PARAMETERS = {"slew": -0.1, "offset":0.02,"threshold": 4}
TI_THRESHOLD = 0.5

# correction default factors
correction_coeff = {'01': 1,'02': 1,'03': 1,'04':1}
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


def anchor_id_to_name(id):
    dic = {"01":"1","02":"2","03":"3","04":"4","05":"5","06":"6","07":"7","08":"8",
               "09":"9"}
    if id in dic:
        return(dic[id])
    else:
        return(id)




def tag_name_to_id(name):
    return("0000000000000b" + name)
   


