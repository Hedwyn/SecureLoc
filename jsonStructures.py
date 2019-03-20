

class dataset:
    
    def __init__(self,sample = None, protocol = '',anchorID = None, botID= None, rp = None, distance = None,timestamps = [], rssi = None):
        self.sample = sample
        self.protocol = protocol
        self.anchorID = anchorID
        self.botID = botID
        self.rp = rp # used only in the case of measurement protocol
        self.distance = distance
        self.timestamps = timestamps
        
        self.rssi = rssi
        
    def export(self):
        """returns the dataset as a dictionary"""
        
        return({"sample":self.sample, 
                "protocol":self.protocol,
                "anchorID":self.anchorID,
                "botID":self.botID,
                "distance":self.distance,
                "reference_point":self.rp,
                "timestamps":self.timestamps,
                "rssi":self.rssi})
    
    
class position:
    
    def __init__(self,bot_id = '', x = 0, y = 0, z = 0):
        self.bot_id = bot_id
        self.x = x
        self.y = y
        self.z = z
        
    def export(self):
        """returns position as a dictionary"""
        
        return({"bot_id": self.bot_id,
                "x": self.x,
                "y":self.y,
                "z":self.z})
    
class metadata:
    
    def __init__(self, tabfile = 'anchors.tab',comments = ''):
        self.tabfile = tabfile
        self.tabfile_content = ''
        self.comments = comments
    
    def dump_tabfile(self):
        """returns the content of anchors tabfile as a string"""
              
        with open('anchors.tab','r') as f:
            for line in f:
                self.tabfile_content = self.tabfile_content + line[:-1] + " | "
        return
     

        
    def export(self):
        """returns metadata as dictionary"""    
        self.dump_tabfile()
                      
        return({"metadata":True,
                "anchors_positions":str(self.tabfile_content)})
        



     
     