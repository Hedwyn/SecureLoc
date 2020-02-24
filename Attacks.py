"""****************************************************************************
Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, in version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************

@file Attacks.py
@author Baptiste Pestourie
@date 2019 November 1st
@brief Abstract reprsentation of an attack - used for attacks simulation in the 3D engine
@see https://github.com/Hedwyn/SecureLoc
"""

import random
from jsonLogs import dataset

class Attack:
    """An attack is represented by three parameters:
        - Success rate, i.e., probability that the attack generates modifies the distance output
        - DoS rate, i.e., probability that the attack denies a given sample
        - Distance distribution, i.e., in case of distance how the distance will be modified. This is given as a probabilistic distribution
        """

    def __init__(self, success_rate, dos_rate, distance_distribution):
        #self.name = None
        self.success_rate = success_rate
        self.dos_rate = dos_rate
        self.distance_distribution = distance_distribution
        self.offset = 0 # used for distance_distribution
        self.targets = [] # anchor or tag IDs

        # seed init, default to system time
        random.seed()

    def apply(self, data):
        """Simulates the effect of an attack on a dataset. True if dataset if kept, false otherwise"""
        print("Applying attack ")
        rand_float = random.random()
        # Dos Case
        if rand_float < self.dos_rate:
            ret = False

        # Success case
        elif rand_float < self.dos_rate + self.success_rate:
            # modifying distance
            data.distance = self.distance_distribution_apply(data.distance)
            ret = True
            print("Attack succeeded, new distance :" + str(data.distance))

        # Fail case
        else:
            ret = True

        return(ret)

    def distance_distribution_apply(self, distance):
        """applies the distance distribution of the attack on the current distance of the sample"""
        return(distance + self.offset)


if __name__ == "__main__":
    # testing random lib
    data = dataset(distance = 1.5)
    some_attack = Attack(0.8,0.1, 1)
    while(some_attack.apply(data)):
        print(data.distance)
