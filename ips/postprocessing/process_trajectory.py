"""****************************************************************************
Copyright (C) 2017-2020 LCIS Laboratory - Baptiste Pestourie

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

@file process_trajectory.py
@author Baptiste Pestourie
@date 2018 February 1st
@brief Extract trajectory from the most recent log
@see https://github.com/Hedwyn/SecureLoc
"""

import json
import sys
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

FILE = 'C:/Users/pestourb/Documents/GitHub/SecureLoc/DecaWino/Arduino/DelayedACKATK/Evaluation/Logs/2019-05-02__10h28m09s.json'
def extract_trajectory(file):
    x = []
    y = []
    z = []
    with open(file,'r') as f:
        for line in f:
            sample = json.loads(line)
            x.append(sample['x'])
            y.append(sample['y'])
            z.append(sample['z'])
    return(x,y,z)


def display_trajectory(file, min, max ):

    (x,y,z) = extract_trajectory(file)
    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111, projection = '3d')
    ax1.set_title("Trajectory")
    ax1.plot(x[min:max],y[min:max],z[min:max])
    ax1.set_xlim3d([0.0, 2.0])
    ax1.set_ylim3d([0.0, 5.0])
    ax1.set_zlim3d([0.0, 1])
    plt.show()


display_trajectory(FILE,10,250)
