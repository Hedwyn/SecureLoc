import random
from matplotlib import pyplot as plt

ARRAY_SIZE = 200
axes = []

def gen_rme(average, std):
    vector = []
    for i in range(ARRAY_SIZE):
        vector.append(random.gauss(average,std))
    return(vector)

def draw(vector, figure, color = 'blue'):
    global axes
    axes.append(figure.add_subplot(111))
    #ax1.set_color('blue')
    time = [0.1 * t for t in range(ARRAY_SIZE)]
    axes[-1].plot(time[:], vector[:], color = color)



if __name__=='__main__':
    rme_normal = gen_rme(0.5, 0.1)
    rme_complex = gen_rme(1.8,0.2)
    rme_attack = gen_rme(1.2,0.15)
    figure = plt.figure()
    draw(rme_normal,figure, 'blue')
    draw(rme_complex,figure, 'green')
    draw(rme_attack,figure, 'red')
    axes[-1].set_xlabel('Time (s)')
    axes[-1].set_ylabel('RME (m)')
    plt.show()
