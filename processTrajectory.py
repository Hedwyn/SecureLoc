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
