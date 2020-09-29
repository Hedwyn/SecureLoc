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

@file sound.py
@author Baptiste Pestourie
@date 2019 November 1st
@brief Sound library for the measurements mode - sound signals used when measurements are starting/finishing
@see https://github.com/Hedwyn/SecureLoc
"""


from threading import Thread
from multiprocessing import Process
import pyaudio
import numpy as np
import math
import time


freq_dict = {'C':32.70,'D':36.71,'E':41.20,'F':43.65,'G':49.00,'A':55.00,'B':61.74} # frequencies of C1, D1, etc
semitone_coeff = 1.059




class Sound:
    """Allows generating customs sounds"""
    def __init__(self,frequency,duration):

        self.frequency = frequency
        self.duration = duration
        #self.start()

    def start(self):
        #self.run()
        t = Thread(target = self.run)
        t.start()

    def run(self):
        """ plays the melody"""
        p = pyaudio.PyAudio()

        volume = 0.1    # range [0.0, 1.0]
        fs = 44100      # sampling rate, Hz, must be integer
        duration = self.duration   # in seconds, may be float
        f = self.frequency       # sine frequency, Hz, may be float

        # generate samples, note conversion to float32 array
        #samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)
        samples = (volume * (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)).tobytes()
        # for paFloat32 sample values must be in range [-1.0, 1.0]
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=fs,
                        output=True)

        # play. May repeat with different volume values (if done interactively)
        stream.write(samples)

        stream.stop_stream()
        stream.close()

        p.terminate()



class Melody:
    def __init__(self,notes,tempo = 120):

        self.melody = []
        for note in notes:

            duration = note[1] * (60 / tempo)

            frequency = self.note_to_frequency(note[0])

            #frequency = note

            self.melody.append(Sound(float(frequency),float(duration) ))

    def run(self):
        """ plays the notes programmed"""
        for sound in self.melody:
            sound.start()
            time.sleep(sound.duration)

    def note_to_frequency(self,note):
        """ converts a note name to a frequency"""
        if (len(note)== 2):
            # natural note
            name = note[0]
            octave = int(note[1])

            frequency = freq_dict[name] * pow(2, octave - 1)
        elif (len(note)== 3):

            # altered note
            name = note[0]
            alteration = note[1]
            octave = int(note[2])
            frequency = freq_dict[name] * pow(2, octave - 1)

            if (alteration == '#'):
                frequency = frequency  * semitone_coeff
            elif (alteration == 'b'):
                frequency = frequency / semitone_coeff
        return(frequency)







    def start(self):
        #self.run()
        t = Thread(target = self.run)
        t.start()


if __name__ == "__main__":
    # Testing
    score = [('E4',0.66),
             ('G#4',0.33),
             ('A4',0.33),
             ('B4',0.66),
             ('G#4',0.33),
             ('B4',1.0)
             ]

    melody = Melody(score,120)
    melody.start()
##    for i in range(4):
##        sound = Sound(220 * (i +1), 1 )
##        sound.start()
##        time.sleep(2)
