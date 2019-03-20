from panda3d.core import *
from parameters import *
from Filter import Filter

import utils




def placeholder_distance(pos1, pos2):
    x, y, z = pos1
    xt, yt, zt = pos2
    return pow(xt-x, 2)+pow(yt-y, 2)+pow(zt-z, 2)



class Anchor:
    """Anchor class: represents an anchor"""
    def __init__(self, x, y, z, name="unnamed", color='red'):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
        self.name = name
        self.shown = False
        self.isActive = False
        self.distance = {}
        self.raw_distance = {}
        self.rangings = {}
        self.correction_filter = Filter('COR')
        # initialization of the ranging lists for the two robots
        self.init_rangings()
        
        

        
        # genereates the visual representation of the anchor in the 3D engine
        self.create_sphere()

        # displays the name of the anchor in the 3D engine
        self.create_text()
        
        
    def init_rangings(self):
        """generates an entry for each robot id in the rangings dictionary"""
        for id_bot in bots_id:
            # adding an entry in the rangings dictionary for each robot id
            self.rangings[id_bot] = []
            self.raw_distance[id_bot] = 0
            
    def set_raw_distance(self,distance,robotname):
        """ sets the unfiltered distance between the anchor and the given robot"""
        self.raw_distance[robotname] = distance
        #print("distance set " + str(distance))

    def get_raw_distance(self,robotname):
        """ gets the unfiltered distance between the anchor and the given robot"""
        return(self.raw_distance[robotname])

    def update_rangings(self, distance,target):
        """updates the list of the last NB_RANGINGS rangings"""
        global correction_coeff
        global correction_offset
        
        

        # if this is the first ranging
        # writing NB_RANGINGS times the first distance to fill up the list
        
            
        corrected_distance = self.correction_filter.apply( [ distance, correction_coeff[self.name],correction_offset[self.name] ] )[0]
        
        if (self.rangings[target] == [] ):
            for i in range(1, NB_RANGINGS):
                
                self.rangings[target].append(corrected_distance)
        

       
        else:
            
            self.rangings[target].append(corrected_distance)
            # removes first element to maintain list size
            self.rangings[target].pop(0)
        

    def create_sphere(self):
        """Create the anchors representation for the 3D world"""
        self.model = loader.load_model("smiley")
        self.model.set_color(utils.colors[self.color])
        self.model.set_scale(0.1)
        self.model.set_pos(self.x, self.y, self.z)

    def create_text(self):
        """Create display text with anchor name"""
        self.label = TextNode('anchor label {}'.format(self.name))
        self.label.set_text(self.name)
        if (bots_id[0] in self.distance and bots_id[1] in self.distance):
            self.label.set_text(self.name + ": " + str(self.get_distance(bots_id[0])) + " / " + str(self.get_distance(bots_id[1])))
            
        self.label.set_card_decal(True)
        self.label.set_text_color(utils.colors[self.color])
        self.label_np = render.attach_new_node(self.label)
        self.label_np.set_pos(self.x - 0.1, self.y + 0.1, self.z)
        self.label_np.set_scale(0.2)
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        taskMgr.add(self.update_text_task, 'update text {}'.format(self.name))

    def show(self):
        """Displays anchor"""
        if not self.shown:
            self.model.reparent_to(render)
            self.shown = True

    def hide(self):
        """Hides anchor"""
        if self.shown:
            self.model.detach_node()
            self.shown = False

    def get_distance(self, robot_id):
        """ gets the filtered distance between the anchor and the given robot"""
        if (robot_id in self.distance):
            
            return self.distance[robot_id]
        else:
            # unknown robot id 
            return(0)

    def set_distance(self, distance, robot_id):
        """ sets the filtered distance between the anchor and the given robot"""
        if robot_id in self.distance:
            self.distance[robot_id] = distance
        else:
            self.distance[robot_id] = distance
            print("new robot id added")
    
    
    def split_dist(self, distance):
        result = ""
        x = 0
        for i in distance:
            if x <= 4:
                result += i
                x += 1
            else:
                break
        return result

    def update_text_task(self, task):
        """Updates the text angle for it to always face the camera"""
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        if (bots_id[0] in self.distance):
            self.label.set_text(self.name + ": " + self.split_dist( str( self.get_distance(bots_id[0]) ) ) )
        return task.cont

