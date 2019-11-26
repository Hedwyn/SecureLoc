from panda3d.core import *
from parameters import *
from Filter import Filter
from abc import ABC,ABCMeta,abstractmethod
from direct.showbase.ShowBase import ShowBase
import utils

class Renderer(ABC,ShowBase):
    """Interface between the Rendering engine and the main application.
    Will be used only if the 3D packages are installed, otherwise it will stubbed"""


    def init_render(self):
        """Initialize the renderer's properties"""
        ShowBase.__init__(self)
        self.win_props = WindowProperties.get_default()
        self.win_props.set_fullscreen(False)
        self.win_props.set_fixed_size(True)
        self.win_props.set_size(640, 480)
        self.win_props.set_title("SecureLoC")
        base.win.request_properties(self.win_props)

        render.set_shader_auto()
        render.set_antialias(AntialiasAttrib.MAuto)
        """Set the overview parameters"""
        base.cam.set_pos(4, 10, 3)
        base.cam.look_at(0, 0, 0)



class RenderedNode(ABC):
    """Representation of a node in the 3D engine. Anchors & mobile tags are both considered as nodes.
    Contains all graphical methods common to all types of nodes"""

    def color(self):
        pass

    def shown(self):
        """whether the node is visible or not"""
        pass

    def text(self):
        """text displayed above the node"""

    def is_Anchor(self):
        """whether the node is an anchor or not"""
        pass

    def get_coordinates(self):
        pass

    @abstractmethod
    def set_coordinates(self,x,y,z):
        pass

    @abstractmethod
    def get_ID(self):
        """returns node ID; can be used to find out if the node is an anchor or a tag"""
        pass

    def get_all_distances(self):
        """returns all the distances measured by the node"""
        raise NotImplementedError

    def change_color(self,color = 'red'):
        """Changes the node color in the 3D engine. Default color is red"""
        self.color = color
        self.model.set_color(utils.colors[self.color])
        # refreshing node color
        self.hide()
        self.show()

    def displays_node_at(self,x,y,z):
        """Displays the node at the given coordinates.
        Note that this only affects the representation of the node in the 3D engine, not the actual coordinates.
        Use move instead in the latter case."""
        self.model.set_pos(pos)

    def move(self,pos = None):
        """Moves the node at the given position.
        This affects both the position of the node in the 3D engine and the sotred coordinates
        Calling without argument will move to the current position.
        Giving position as tuple in input will define this position as the current position"""

        if pos is None:
            # getting coordinates if the position is not given
            (x,y,z) = self.get_coordinates()
        else:
            # setting new coordinates
            (x,y,z) = pos
            self.set_coordinates(x,y,z)
        # displaying refreshed pos
        self.model.set_pos(pos)

    def create_sphere(self):
        """Create the node representation for the 3D world"""
        (x,y,z) = self.get_coordinates()
        self.model = loader.load_model("smiley")
        self.model.set_color(utils.colors[self.color])
        self.model.set_scale(0.1)
        self.model.set_pos(x, y, z)
        self.shown = False
        self.is_Anchor = not(is_bot_id(self.get_ID()))

    def show(self):
        """Displays node in the 3D engine"""
        if not self.shown:
            self.model.reparent_to(render)
            self.shown = True

    def hide(self):
        """Hides node in the 3D engine"""
        if self.shown:
            self.model.detach_node()
            self.shown = False

    def get_distances_as_str(self):
        """converts the distances measured by the node into a string.
        The string is formatted as 'distance1 / distance2/... distance n'
        The order given follows the order of IDs"""
        # getting the distances measured by the node as a dic
        distances_dic = self.get_all_distances()

        # getting the distances measured by the node as a list
        distances_list = []
        for id in distances_dic:
            distances_list.append(distances_dic[id])

        # creating the text with the distances
        self.text = ''
        while (distances_list):
            # define printing the first 4 digits each time
                self.text += str(distances_list.pop())[:4]
                # checing if it's the last one of the list
                if (distances_list):
                    self.text += '/ '

    def get_position_as_str(self):
        """converts the node position into a string"""
        (x,y,z) = self.get_coordinates()
        # printing only the first 4 digits
        self.text = ("(" + str(x)[:4] + "," + str(y)[:4] + "," +str(z)[:4] + str(")") )



    def create_text(self):
        """Displays distance above the node representation.
        If multiple distance are given, they all displayed"""
        name = self.get_ID()
        (x,y,z) = self.get_coordinates()
        self.label = TextNode('Node label {}'.format(self.name))
        self.label.set_text(name)
        # truncating node ID
        if (len(name) > 2):
            short_name = name[:-2]
        else:
            short_name = name

        self.label.set_text(short_name[:-2] + ": ")
        self.label.set_card_decal(True)
        self.label.set_text_color(utils.colors[self.color])
        self.label_np = render.attach_new_node(self.label)

        # shifting the text above the node representation
        self.label_np.set_pos(x, y, z + 0.2)
        self.label_np.set_scale(0.2)
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        taskMgr.add(self.update_text_task, 'update text {}'.format(name))

    def update_text_task(self, task):
        """Updates the text angle for it to always face the camera"""
        name = self.get_ID()
        (x,y,z) = self.get_coordinates()
        self.label_np.look_at(-base.cam.get_x(), -base.cam.get_y(), -base.cam.get_z())
        # updating node text
        if self.is_Anchor:
            # displaying the distances to the tags
            self.get_distances_as_str()
        else:
            # for a tag, displaying only the positions
            # TODO: tags can also display distances in cooperative approaches
            self.get_position_as_str()
        # truncating node ID
        if (len(name) > 2):
            # keeping only the last 2 digits
            short_name = name[-2:]
        else:
            short_name = name
        self.label.set_text(short_name + ": " + self.text)

        # placing text above the node
        self.label_np.set_pos(x, y, z + 0.2)
        return task.cont

class RenderedWorld(ABC):
    """Representation of the World in the 3D engine."""
    def create_grid(self):
        """Create the ground grid"""
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData("vertices", format, Geom.UHStatic)
        vdata.setNumRows(4)

        vertexWriter = GeomVertexWriter(vdata, "vertex")
        vertexWriter.addData3f(0,0,0)
        vertexWriter.addData3f(self.width,0,0)
        vertexWriter.addData3f(self.width,self.height,0)
        vertexWriter.addData3f(0,self.height,0)

        # step 2) make primitives and assign vertices to them
        tris=GeomTriangles(Geom.UHStatic)

        # adding vertices one by one as they are not in the right order
        tris.addVertex(0)
        tris.addVertex(1)
        tris.addVertex(3)

        # indicates that vertices have been added for the first triangle.
        tris.closePrimitive()


        tris.addConsecutiveVertices(1,3) #add vertex 1, 2 and 3
        tris.closePrimitive()

        # step 3) make a Geom object to hold the primitives
        squareGeom=Geom(vdata)
        squareGeom.addPrimitive(tris)

        # now puts squareGeom in a GeomNode. You can now position your geometry in the scene graph.
        squareGN=GeomNode("square")
        squareGN.addGeom(squareGeom)
        render.attachNewNode(squareGN)
