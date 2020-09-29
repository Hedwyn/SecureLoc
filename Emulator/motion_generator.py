import random
from ips.core.parameters import *

class MotionGenerator:
    """Generates node displacements, either random or assetion-based"""
    @staticmethod
    def generate_random_speed(max_speed = MAX_SPEED):
        speed_norm = random.uniform(0, max_speed)


        speed_x = random.random()
        speed_y = random.random()
        speed_z = random.random()

        sign_x = random.choice([-1,1])
        sign_y = random.choice([-1,1])
        sign_z = random.choice([-1,1])


        speed_x = speed_x * speed_norm /(speed_x + speed_y + speed_z)
        speed_y = speed_y * speed_norm /(speed_x + speed_y + speed_z)
        speed_z = speed_z * speed_norm /(speed_x + speed_y + speed_z)
        return(sign_x * speed_x,sign_y * speed_y, sign_z * speed_z)

    def generate_random_speed_2D(max_speed = MAX_SPEED):
        speed_norm = random.uniform(0, max_speed)


        speed_x = random.random()
        speed_y = random.random()


        sign_x = random.choice([-1,1])
        sign_y = random.choice([-1,1])



        speed_x = speed_x * speed_norm /(speed_x + speed_y)
        speed_y = speed_y * speed_norm /(speed_x + speed_y)

        return(sign_x * speed_x,sign_y * speed_y, 0)
