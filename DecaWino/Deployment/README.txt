This directory contains a Python program for automating DecaWino programs deployment.
In teensy3 directory, simply launch python Deployment.py in command line.
The DecaWino nodes configuration is given in 'config.txt'. 
The IP addresses of the Raspberry as well as the DecaWino nodes plugged to each Raspberry should be specified in that file.
This prgram excecutes the following
1 Compilation of the binary file for each DecaWino from an unique .cpp program. Each binary as a unique ID, based on the ID specified in Config.txt.
2 Sending the hex files thourgh SSh to the Raspberry 
3 Flashing the DeaWino nodes remotely.

Note ino files can easily be adapted into .cpp file, the loop() and setup() functions should basically be fitted into a main function(). 