import matplotlib.pyplot as plt
import matplotlib as mpl
import random

plt.style.use('C:/Users/pestourb/Documents/Plateforme src/matplotlib-master/lib/matplotlib/mpl-data/stylelib/custom.mplstyle')
font = {'fontname':'Century Gothic', 'size' : 16}
ratio = 1.83
noise = 0.2

def plot(reply_time, std):
    fig = plt.figure()
    axe = fig.add_subplot(111)
    axe.set_xlabel('Reply time (ms)', **font)
    axe.set_ylabel('Standard deviation (ns)', **font)
    axe.scatter(reply_time, std, s = 50, marker = '^', c= '#0d0d85')
    plt.show()
    


def generate_arrays():
    reply_time = [0.23]
    for i in range(3):
        reply_time.append(0.4 + 0.2 * i)
    for i in range(20):
        reply_time.append(1 + 0.5 * i)
        
    std = [x * ratio + random.gauss(0, noise) for x in reply_time]
    return(reply_time, std)


rep, std = generate_arrays()
plot(rep,std)