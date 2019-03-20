LIGHTSPEED = 229702547.0
TIMEBASE = 15.65E-12


class Ranging:
    """contains the low-level ranging protocols such as recomputing the ranging output 
    with different protocols on the same date"""
    
    def __init__(self,timestamps, lightspeed = LIGHTSPEED, timebase = TIMEBASE ):
        # timestamps
        self.timestamps = timestamps # list of timestamps
        self.distance = None
        self.lightspeed = lightspeed
        self.timebase = timebase

    def TWR(self):
        # computes Two-Way Ranging protocols
         if ( len(self.timestamps) != 4 ):
             print("Incorrect number of timestamps")
         else:
             [t1,t2,t3,t4] = self.timestamps
             tof = (t4 - t1 - (t3 - t2)) / 2; 
             self.distance = tof * self.lightspeed * self.timebase
    
    def getDistance(self, protocol = 'TWR'):
        if protocol == 'TWR':
            self.TWR()
        else:
            print("This protocol does not exist")
            return(0)
            
        return(self.distance)
        
# tests
test = Ranging([-1404924849,193340928,218452047,-1379812821])
print(test.getDistance() )
    
        