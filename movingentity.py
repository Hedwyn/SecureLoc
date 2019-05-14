import math
import utils
from direct.showbase.DirectObject import DirectObject
from panda3d.core import *
from parameters import *


class MovingEntity(DirectObject):
    """Moving tags"""
    def __init__(self, name, color='orange'):
        self.color = color
        self.name = name
        self.pos = []
        self.speed_vector = []
        self.acc_vector = []
    
        # pos_list needs POS_LIST_SIZE elements to avoid reading conflicts
        # initializing to 0
        
        for x in range(0, POS_LIST_SIZE):
            self.pos.append(DEFAULT_POS)

        # speed vector list needs SPEED_LIST-SIZE elements to avoid reading conflicts
        # initializing to 0
        
        for y in range(0, SPEED_LIST_SIZE):
            self.speed_vector.append([0,0,0])

        for z in range(0, ACC_LIST_SIZE):
            self.acc_vector.append([0,0,0])

        self.ready = False
        self.shown = False

        self.create_sphere()
        self.create_text()
        

    def create_sphere(self):
        """Creates a sphere representing the robot in the 3D world"""
        self.model = loader.load_model("smiley")
        self.model.set_color(utils.colors[self.color])
        self.model.set_scale(0.1)

    def create_text(self):
        """Generates the label of the anchor"""
        self.label = TextNode('anchor label {}'.format(self.name))
        self.label.set_text("x:"+str(self.get_pos()[0])+" y:"+str(self.get_pos()[1])+" z:"+str(self.get_pos()[2]))
        self.label.set_card_decal(True)
        self.label.set_text_color(utils.colors[self.color])
        self.label_np = render.attach_new_node(self.label)
        self.label_np.set_pos(float(self.get_pos()[0]-0.1), float(self.get_pos()[1]+0.2), float(self.get_pos()[2]))
        self.label_np.set_scale(0.2)
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        #self.show()
        taskMgr.add(self.update_text_task, 'update text {}'.format(self.name))

    def update_text_task(self, task):
        """Modifies the text above the anchor"""
        (x,y,z) = self.get_pos()
        (a,b,c) = self.get_coord(x,y,z)
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        if (TILES):
            self.label.set_text("x:" + self.split_pos(str(a) ) + " y:" + self.split_pos(str(b)) + " z:" + self.split_pos(str(c)))
        else:
            self.label.set_text("x:" + self.split_pos(str(x) ) + " y:" + self.split_pos(str(y)) + " z:" + self.split_pos(str(z)))

        #self.label_np.set_pos(float(a), float(b), float(c) )        
        self.label_np.set_pos(float(self.get_pos()[0] - 0.1), float(self.get_pos()[1] + 0.2), float(self.get_pos()[2]))
        return task.cont



    
    def get_coord(self,x,y,z):
        """returns the coordinates of the robot on a tiled floor. 
        The size of the tiles should be specified in parameters"""
        a = 0
        b = 0
        c = 0

        distance = 0

        while (distance <= x):
            distance += SQUARE_SIZE
            if ( (x - distance) > - (SQUARE_SIZE / 2) ):
                a += 1
        distance = 0

        while (distance <= y):
            distance += SQUARE_SIZE
            if ( (y - distance) > - (SQUARE_SIZE / 2) ):
                b += 1
        distance = 0

        while (distance <= z):
            distance += SQUARE_SIZE
            if ( (z - distance) > - (SQUARE_SIZE / 2) ):
                c += 1
        distance = 0
        
        
        
        

        return(a,b,c)

       

    def show(self):
        """Displays the robot's sphere"""
        if self.ready and not self.shown:
            self.model.reparent_to(render)
            self.shown = True

    def hide(self):
        """Hides the robot's sphere"""
        if self.shown:
            self.model.detach_node()
            self.shown = False
    
    def split_pos(self, position):
        """graphical function; displays robot position"""
        result = ""
        x = 0
        for i in position:
            if x <= 4:
                result += i
                x += 1
            else:
                break
        return result

    def get_pos(self):
        """ returns the most recent position in the position list"""
        return(self.pos[POS_LIST_SIZE - 1])

    def get_pre_pos(self):
        """ returns previous position for speed calculation"""
        return(self.pos[POS_LIST_SIZE - 2 ] )

    def set_pos(self, pos,replace_last = False):
        """Sets the robot position"""

        # robot is considered to be ready once its position is set
        if not self.ready:
            self.ready = True
        if (replace_last):
            # removes last element in replace mode
            self.pos.pop(POS_LIST_SIZE - 1 )
        else:
            # removes first element to keep a list size of POS_LIST_SIZE
            self.pos.pop(0)

        self.pos.append(pos)


    def display_pos(self):
        """ displays the robot position in th 3D engine"""
        self.model.set_pos(self.get_pos())

    def get_abs_speed(self):
        """computes the absolute speed from the speed vector"""

        speed_vector = self.get_speed_vector()
        abs_speed = math.sqrt(pow(speed_vector[0], 2) + pow(speed_vector[1], 2) + pow(speed_vector[2], 2))  # m/s
        return(abs_speed)

    def get_abs_acc(self):
        """computes the absolute acceleration from the acceleration vector"""
        acc =  self.get_acc_vector()
        abs_acc = math.sqrt(pow(acc[0], 2) + pow(acc[1], 2) + pow(acc[2], 2))  # m/s
        return(abs_acc)
        
    def set_speed_vector(self, speed_vector, replace_last=False):
        """Appends current speed to speed list and 
        removes the oldest speed data stored""" 
        if replace_last:
            # removes last element in replace mode
            self.speed_vector.pop(SPEED_LIST_SIZE - 1)
        else:
            # removes first element to keep a list size of SPEED_LIST_SIZE
            self.speed_vector.pop(0)

        self.speed_vector.append(speed_vector)

    def set_acc_vector(self, acc, replace_last=False):
        """Appends current acceleration to acceleration list and removes the oldes acceleration data stored"""
        if replace_last:
            #removes last element in replace mode
            self.acc_vector.pop(ACC_LIST_SIZE -1)
        else:
            # removes first element to keep a list size of SPEED_LIST_SIZE
            self.acc_vector.pop(0)

        self.acc_vector.append(acc)

    def get_speed_vector(self):
        """ returns the most recent speed vector in the speed vector list"""

        return(self.speed_vector[SPEED_LIST_SIZE - 1])

    def get_acc_vector(self):
        """ returns the most recent acceleration vector in the acceleration vector list"""

        return(self.acc_vector[ACC_LIST_SIZE - 1])

    def compute_speed(self,replace_mode = False):
        """calculates the speed after each position update"""
        pos = self.get_pos()
        pre_pos = self.get_pre_pos()

        # coordinates of the current position
        
        x = pos[0]
        y = pos[1]
        z = pos[2]

        # coordinates of the previous position

        pre_x = pre_pos[0]
        pre_y = pre_pos[1]
        pre_z = pre_pos[2]

        # calculates the speed as (position vector / sample time ) 
        speed_vector = [(x - pre_x)/T, (y - pre_y)/T, (z - pre_z) / T]

        # set the speed  of the robot
                
        self.set_speed_vector(speed_vector, replace_mode)
        v_print("robot " + self.name + " speed: " + str(self.get_abs_speed()) + " m/s")

    def compute_acc(self, replace_mode=False):
        """calculates the acceleration after each position update"""
        speed = self.get_speed_vector()
        pre_speed = self.speed_vector[SPEED_LIST_SIZE - 2]

        v_x = speed[0]
        v_y = speed[1]
        v_z = speed[2]

        pre_v_x = pre_speed[0]
        pre_v_y = pre_speed[1]
        pre_v_z = pre_speed[2]

        acc = [(v_x - pre_v_x) / T, (v_y - pre_v_y) / T, (v_z - pre_v_z) / T]
        self.set_acc_vector(acc, replace_mode)
        v_print("robot " + self.name + " acceleration: " + str(self.get_abs_acc()) + " m/s²" + "\n" )

