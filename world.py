from panda3d.core import *
import typing
from anchor import Anchor
from application import *
from Filter import Filter
from parameters import *
import math


threshold = -0.5
ITERATE = True
TwoD = False
RANDOM_SEARCH = False










class World:
    """World class, represents the room in which the robots will evolve.
    The world contains the anchors with their positions, and is able
    to return the positions of the robots or whatever is moving in it"""
    def __init__(self, width: float, height: float, anchors: list):
        """anchors should be a list of 4 valid anchors"""
        self.width = width
        self.height = height
        self.anchors = anchors
        self.target = None
        self.shown = False
        self.create_grid()
        self.create_anchors()
        

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
       

    def create_anchors(self):
        """Displays anchors"""
        for anchor in self.anchors:
            anchor.show()
            
    def gen_anchors_name(self, nb_anchors):
        """generates a list of anchors id for the given total number of anchors"""
        if (nb_anchors > 26):
            print("cannot handle " + str(nb_anchors) + "\n")
            print("the number of anchors should be below 26")
                
        else:
            anchors_name = []
            for i in range(nb_anchors):
                # generates successive letters starting from A
                anchors_name.append(str(i + 1))
                
        return(anchors_name)
            
    def gen_bots_id(self, nb_bots):
        """generates a list of anchors id for the given total number of anchors"""

        bots_id = []
        rootid = '000100020003'
        for i in range(nb_bots):
            # generates successive letters starting from A
            if (i > 9):
                idb = rootid  + '00' + str(i)
            else:
                idb = rootid + '000' + str(i)
                
            bots_id.append(idb)
                
        return(bots_id)        
            
            
    def get_target(self,robot):
        """ gets the id of the robot to localize"""
        self.target = robot

    def update_anchor(self, name: str, distance: float,robot_id,options = None):
        """Updates distance between anchor and robot.
           Note that anchors names should be unique for this to work"""
        for anchor in self.anchors:
            if anchor.name == name:
                
                anchor.update_rangings(distance,robot_id)
                anchor.set_raw_distance(distance,robot_id)

                if (options == "SW"):
                    # sliding window enabled
                    
                    sliding_windows = Filter("SW",[anchor.rangings[robot_id],20,12,0])
                    filtered_distance = sliding_windows.apply()[0] # output(s) of filters are returned as a list
                    
                    
                    anchor.set_distance(filtered_distance,robot_id)
                else:
                    anchor.set_distance(distance,robot_id)
                    
                    
                    
                # activates the anchor the first time it uploads a distance
                if (not(anchor.isActive) and distance > 0.0):
                    
                    anchor.isActive = True
                return


    def ranging(self,x,y,z,anchor_idx):
        
        anchor_x = self.anchors[anchor_idx].x
        anchor_y = self.anchors[anchor_idx].y 
        anchor_z = self.anchors[anchor_idx].z 
            
        return(math.sqrt(pow( x - anchor_x , 2) + pow( y - anchor_y, 2) + pow( z - anchor_z,2) ))

    def get_distance(self,pos1,pos2):
        """ returns the distance between pos1 and pos2"""

        (x1,y1,z1) = pos1
        (x2,y2,z2) = pos2

        distance = math.sqrt(pow( (x1 - x2), 2) + pow( (y1 - y2), 2) +  pow( (z1 - z2), 2) )
        return(distance)

    
    def mmse(self,rangings,pos):
        """ Calculates the Mean Square Error of the given position.
        Error is defined as the difference between the ranging of the given position and the given rangings"""
     
        mean_error = 0
      
        (x,y,z) = pos 

  
        
        for (i,distance) in enumerate(rangings):
            error = (self.ranging(x,y,z,i) - distance)
            #print("error is:" + str(error) )
            mean_error += pow(error,2)
        mean_error = mean_error / len(rangings)


        return(mean_error)



    def iterate(self,start_pos,rangings):
        """ Finds the minimum MSE in the neighborhood of start_pos and repeats the process from that new position"""
        
        step = 0.01
        # getting solution from basic multilateration
        pos = start_pos

        # starting from the center if random search is enabled
        if (RANDOM_SEARCH):
            NB_STEPS = 20
            pos = (0.9,2.4,0)
        else:
            NB_STEPS = 5
        
        

        k = 0
        v_print("pos before :" + str(pos) )
        while (k < NB_STEPS ):
            (x,y,z) = pos
            
            v_print("\n\n" + "current position :" + str(pos) )
            # choosing direction

            
            directions = []
            for i in range(-10,11):
                for j in range(-10,11):
                    directions.append( (x+(i * step ),y+(j * step),0) )
            
            mean_squared = []
            
            
            for (i,direction) in enumerate(directions):
                

                error = self.mmse(rangings, direction)
                mean_squared.append(error)
                #v_print("mean squared for " + name_directions[i] + ": " + str(error))

                
            minimum = 1000
            min_idx = 0
            for (i,ms) in enumerate(mean_squared)   :
                if (ms < minimum):
                    min_idx = i
                    minimum = ms
            #v_print(name_directions[min_idx])

            pos = directions[min_idx]
            k += 1

        v_print("pos after:" + str(pos) )


        d_print("pos mmse :" + str(ms) )

        return(pos,ms)

    def localize(self,target):
        """localizes the given target"""
        
        (bary_pos,solutions) = self.multilateration_2D(target)
        
        solutions_list = []
        

        rangings = []
        # getting ranging values from anchors
        for anchor in self.anchors:
            distance = anchor.get_distance(target)
            rangings.append(distance)
            
        if not(ITERATE):
            v_print("Barycentric solution")
            #self.update_correction(rangings,solution)
            return(bary_pos)


        
        minimum = 1000
        min_idx = 0


        
        (ite_pos, ite_ms) =  self.iterate(bary_pos,rangings)
        bary_ms = self.mmse(rangings,bary_pos)
        v_print("mse ite" + str(ite_ms)) 
        v_print("mse bary" + str(bary_ms) )
        (a,b,c) = ite_pos
        (d,e,f) = bary_pos
        #coef_bary = 0
        # scoef_ite = 1.0

        coef_bary =  (1 / bary_ms) / ( (1/bary_ms) + (1/ite_ms) ) 
        coef_ite = (1 / ite_ms) / ( (1/bary_ms) + (1/ite_ms) )
                            
        x = coef_ite * a + coef_bary * d
        y = coef_ite * b + coef_bary * e
        z = coef_ite * c + coef_bary * f
        pondered_pos = (x,y,z)
        predicted_pos = self.predict_pos(self.target)
        solutions_list.append(bary_pos)
        solutions_list.append(ite_pos)
        solutions_list.append(pondered_pos)
        #for solution in solutions:
        #    solutions_list.append(solution)
        current_pos = self.target.get_pos()
        #next_pos = self.chose_closest_solution(solutions_list,current_pos)
        self.update_correction(rangings,current_pos)
        return(pondered_pos)

    def trilateration_2D(self,anchor,Rx,Ry):
        """Computes the relative tag position  to the given anchor(X) and its right neighbor(Y). Rx/y denote the distance to both anchors.
            Calculation is based on Pythagora's theorem and is done in 2D"""
        # computing trilateration with anchor and its right neighbor
        # getting the distances between both both anchors
        dx = self.anchors[3].x
        dy = self.anchors[1].y


        if ( (anchor.name == '1') or (anchor.name == '3') ):
            distance = dx
        else:
            distance = dy
        
        if (Rx < 0):
            Rx = 0
        if (Ry < 0):
            Ry = 0
            
        X = (pow(Rx,2) - pow(Ry,2) + pow(distance,2)) / (2 * distance)
        if (X < 0):
            X = 0
        if (pow(Rx,2) - pow(X,2) <= 0 ):
            Y = 0
        else:
            Y = math.sqrt( pow(Rx,2) - pow(X,2) )
            

        coordinates_change = [(X,Y),(Y, dy - X),(dx - X,dy - Y),( dx - Y,X)  ]
        anchors = ['1','2','3','4']
        (x,y) = coordinates_change[anchors.index(anchor.name)]
        #print(X,Y)
        #print(distance)

        #print("anchor : " + anchor.name + " Rx : " + str(Rx) + "Ry :  " + str(Ry) + "pos " + str((x,y) ) )

        return(x,y)

    def update_correction(self,rangings,solution):
        """dynamically corrects the offset applied to the rangings, by comparing the received ranging value to the estimated one.
            The correction is based on a ratio of the difference between the two values"""
       
        global correction_offset

        # parameters
        #ratio = 0.002
        ratio = 0
        # Noise estimation
        (x,y,z) = solution
        for idx in range (len(self.anchors)):
            v_print("position :" + str(solution) )
            real_ranging = self.ranging(x,y,z,idx)
            measured_ranging = rangings[idx]
            v_print("estimated :" + str(real_ranging) + "measured :" + str(measured_ranging))
            offset = ratio * (real_ranging - rangings[idx] )
            correction_offset[self.anchors[idx].name] += offset
            v_print("offset anchor " + str(self.anchors[idx].name) + " : " + str(correction_offset[self.anchors[idx].name] ))
        
        
    def predict_pos(self,robot):
        """estimates the position at next iteration based on tag's speed"""
        

        (X,Y,Z) = robot.get_pos()
        (x,y,z) = robot.get_pre_pos()

        predicted_pos = (2 * X - x, 2 * Y - y, 2 * Z - z)

        return(predicted_pos)


    def chose_closest_solution(self,solutions_list,position):
        """returns the closest solution of solutions_list from the given position"""
        min_idx = 0
        min_distance = 0
        for (idx,solution) in enumerate(solutions_list):
            distance = self.get_distance(solution,position)
            if (distance < min_distance):
                min_idx = idx
                min_distance = distance

        return(solutions_list[min_idx])
            
            

    def multilateration_2D(self,target):
        """computes the target position through a 2D calculation. Z is assumed to be 0"""
        rangings = []
        solutions = []
        anchors_list = []
        
        coeff = [0.2,0.2,0.2,0.4]
       

        
        
        i = 1
       
        for anchor in self.anchors:
            rangings.append(anchor.get_distance(target))
            # appending anchors 1 to 4 to anchors list for square multilateration
            if (i < 5):
                anchors_list.append(anchor)
            i+=1
                
                
        # getting the rangings for the square centroid
        [Ra,Rb,Rc,Rd] = [rangings[0], rangings[1], rangings[2], rangings[3]]
        anchors = anchors_name

        for (idx,anchor) in enumerate(anchors_list):
            (Rx,Ry) =( rangings[idx],rangings[(idx - 1) % 4] )
            (x,y) = self.trilateration_2D(anchor,Rx,Ry)
            solutions.append( (x,y,0) )



         # coeff calculation
        mmse = []
        sum_inv_mmse = 0
        for solution in solutions:
            error = self.mmse(rangings,solution)
            mmse.append(error )
            sum_inv_mmse += 1 / error

        for (idx,error) in enumerate(mmse):
            coeff[idx] = (1/error) / sum_inv_mmse
        
        
        
        
            
            

        coeff = [0.25,0.25,0.25,0.25] 
        mean_x = 0
        mean_y = 0
       

        for idx,solution in enumerate(solutions):
            (x,y,z) = solution
            mean_x += x * coeff[idx]
            mean_y += y * coeff[idx]
        final_solution = (mean_x,mean_y,0)
        
            
        #return( (solutions[3],solutions) )
        return((final_solution,solutions))
           
            
            
            

        
        

        
        
        
                        
        
        
        

           


    @staticmethod
    def order_anchors(anchors: list) -> list:
        """Regenerate anchors list to always have anchors in a easy-to-work
        order"""
        return anchors




#testing
