import paho.mqtt.client as mqtt
from anchor import Anchor
import math
import json
from movingentity import MovingEntity
import time
from parameters import *
from Attacks import Attack

DEFAULT_ATTACK_CONFIG_FILE = "attacks_config.json"

class Simulator:

    def __init__(self, mqttc = None):
        self.fictive_anchors = []
        self.fictive_tags = []
        self.mqttc = mqttc
        self.attacks = {}

    @staticmethod
    def get_distance(pos1,pos2):
        """ returns the distance between pos1 and pos2"""

        (x1,y1,z1) = pos1
        (x2,y2,z2) = pos2

        distance = math.sqrt(pow( (x1 - x2), 2) + pow( (y1 - y2), 2) +  pow( (z1 - z2), 2) )
        return(distance)

    def emulate_anchor(self, anchor, tag):
        """emulates the behaviour of a virtual anchor, sending fictive frames to MQTT broker"""
        anchorID = anchor.name
        anchorPos = (anchor.x, anchor.y, anchor.z)
        tagID = tag.name
        tagPos = tag.get_current_pos()
        distance = Simulator.get_distance(tagPos, anchorPos)
        #print(anchor.name[14:16] + "/" + tag.name[13:16] + "/" + str(distance))

        # publishing fictive data
        self.mqttc.publish(ROOT + "0" + anchorID + "/" + tagID[14:16] + "/distance", distance )


    def emulate_all_fictive_anchors(self,tag):
        """emulates the behaviour of all the virtual anchors registered"""
        for anchor in self.fictive_anchors:
            self.emulate_anchor(anchor, tag)


    def send_log_as_MQTT_frame(self, dataset):
        """sends a given log in the MQTT bus at the proper topic"""
        anchorID = dataset['anchorID']
        tagID = dataset['botID']
        distance = dataset['distance']
        if anchorID and tagID and distance:
            self.mqttc.publish(ROOT + anchorID + "/" + tagID[14:16] + "/distance", distance )

    def configure_attacks(self, config_file = DEFAULT_ATTACK_CONFIG_FILE):
        """Creates the attack objects defined in the attacks config file"""
        with open(config_file) as f:
            for line in f:
                attack_config = json.loads(line)
                # try:
                self.attacks[attack_config['name']] = Attack(
                attack_config['success_rate'],
                attack_config['dos_rate'],
                attack_config['distance_distrib']
                )
                # except:
                #     print("Missing parameter in the attack config file")





if __name__ == "__main__":
    # starting mqtt client
    # mqttc = mqtt.Client()
    # mqttc.connect(HOST, PORT, 60)
    # mqttc.loop_start()
    # a1 = Anchor(0,0,0,'a1')
    # a2 = Anchor(1,1,0, 'a2')
    # t1 = MovingEntity('t1')
    # t1.set_position((2,2,2))
    # emulate_anchor(mqttc, a1, t1)
    # time.sleep(10)
    pos1 = (0,0,0)
    pos2 = (1,1,1)
    Simulator.get_distance(pos1,pos2)

    sim = Simulator()
    sim.configure_attacks()
    print(sim.attacks)
