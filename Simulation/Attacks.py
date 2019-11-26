import os,sys,inspect
# adding parent folder into the path
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import json
import random
from anchor import Anchor

class AttackSimulation:
    """Simulates the effects of an attack from the SYS perspective.
    An attack is represented by a distance modification associated to a probability distribution.T
    he attack has a given probability to succeed,
    as well as a given probability to disrupt the ranging process."""
    def __init__(self,success_rate = 0,dos_rate = 0, distribution = 0):
         self.success_rate = success_rate
         self.dos_rate = dos_rate
         self.distribution = distribution
         random.seed()


    def modify_distance(self,distance, ancher_id):
        """applies the attack distribution to the distance"""
        ## # TODO: AWGN
        if(ancher_id == '02' or ancher_id == '03'):
           distance = distance + 2
        elif (ancher_id == '01' or ancher_id =='04'):
            distance = distance - 2

        return(distance + self.distribution)

    def applies_attack_on_1sample(self,distance, ancher_id):
        """simulates the attack on one distance sample"""
        # checking that the probabilities are valid
        if (self.success_rate + self.dos_rate) > 1:
            raise Exception("The probabilities given are wrong (total > 1)")



        # random sampling for attack success & DoS
        random_number = random.random()

        SUCCESS = False
        DoS = False



        if (random_number) < self.success_rate:
            SUCCESS = True
        # random sampling for DoS
        elif (random_number) < self.dos_rate + self.success_rate:
            DoS = True



        if (SUCCESS):
            # modify distance
            modified_distance = self.modify_distance(distance, ancher_id)

        # check if it's a DoS
        elif (DoS):
            modified_distance = -1

        else:
            modified_distance = distance
        return(modified_distance)

class RTAttacks(AttackSimulation):
    """Attacks Simulation in real-time mode
    Sends simulated data to MQTT bus"""
    pass

class LogsAttacks(AttackSimulation):
    """Attacks Simulation on the LOGSFILE
    Creates a modified log with the simulated data"""
    def __init__(self,success_rate = 0,dos_rate = 0,distribution = 0,name = "Sneaky Attacker"):
         self.success_rate = success_rate
         self.dos_rate = dos_rate
         self.distribution = distribution

    def simulate_attack(self,logname_in,logname_out):
        """simulates the attack on the entire log"""

        with open(logname_in,'r') as log_in:
            try:
                log_out = open(logname_out,'w+')
            except:
                print("Could not create output log")

            for line in log_in:

                if line == "\n":
                    continue
                json_sample = json.loads(line)
                # getting the distance
                if "metadata" in json_sample:
                    log_out.write(line)
                else:
                    distance = json_sample["distance"]
                    if distance is None:
                        continue
                    modified_distance = self.applies_attack_on_1sample(distance, json_sample["anchorID"])
                    if (modified_distance) != -1:
                        # debug
                        print("distance read: " + str(distance))
                        print("modified distance : " + str(modified_distance))
                        # writing the modified distance in the json sample
                        json_sample["distance"] = modified_distance
                        json.dump(json_sample,log_out)
                        log_out.write("\n")
                        # if -1 is returned, it's a DoS
                        # not keeping the line ine the output log1 in that case
            log_out.close()








# Tests

# creating an Attack
#TODO: lire le dernier fichier déposé dans un répertoire sépcifique
LOGIN = "../Playback/2019-05-17__16h54m32s.json"
LOGOUT_FOLDER= '../PLAYBACK'
LOGOUT = LOGOUT_FOLDER + '/' + 'log1.json' #TODO: number or date in the filename
distance_shift = LogsAttacks(0.5,0.5,5,"Distance Shift")
distance_shift.simulate_attack(LOGIN,LOGOUT)
