from panda3d.core import *
from parameters import *
from Filter import Filter
from abc import ABC,ABCMeta,abstractmethod
from direct.showbase.ShowBase import ShowBase
from threading import Thread
import time
import utils

class Renderer(ABC,ShowBase):
    """Stub for the interface between the Rendering engine and the main application.
    Will be used automatically if the 3D engines packages are not installed
    or if headless mode is being used."""


    def init_render(self):
        #qqShowBase.__init__(self)
        pass



class RenderedNode(ABC):
    """Stub for node rendering in the 3D engine.
    Will be used automatically if the 3D engines packages are not installed
    or if headless mode is being used."""

    def color(self):
        pass

    def shown(self):
        pass

    def text(self):
        pass

    def is_Anchor(self):
        pass

    def get_coordinates(self):
        pass

    @abstractmethod
    def set_coordinates(self,x,y,z):
        pass

    @abstractmethod
    def get_ID(self):
        pass

    def get_all_distances(self):
        raise NotImplementedError

    def change_color(self,color = 'red'):
        pass

    def displays_node_at(self,x,y,z):
        pass

    def move(self,pos = None):
        pass

    def create_sphere(self):
        pass

    def show(self):
        pass

    def hide(self):
        pass

    def get_distances_as_str(self):
        pass

    def get_position_as_str(self):
        pass

    def create_text(self):
        pass

    def update_text_task(self, task):
        pass

class RenderedWorld(ABC):
    """Stub for 3D engine World."""
    def create_grid(self):
        pass


class task:
    """Stub for task class of Panda 3D"""
    done = 0
    cont = 1
    again = 2

    def __init__(self, delayTime = 0):
        task.delayTime = delayTime

class taskMgr(Thread):
    """Stub for Panda 3D taskMgr"""
    @classmethod
    def wrapper(self,delayTime,target,name = ''):
        #creating a new task
        new_task = task(delayTime)
        task_output = task.again
        while (task_output == task.again):
            task_output = target(task)
            time.sleep(task.delayTime)
            # TODO: check thread termination
            # TODO: getting rid of the delay ?

    @classmethod
    def doMethodLater(self,delayTime,target,name = ''):
        handler = Thread(target = self.wrapper,args = (delayTime,target))
        handler.start()

    # TODO: implement other methods (e.g add)
