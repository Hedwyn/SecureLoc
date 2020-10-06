import os
import platform
OS =  platform.system() 
ARDUINO_INSTALL_DIR_NAME = "Arduino"
ARDUINO_SUBDIRS = ["drivers", "examples","tools","libraries"] ## a non exhaustive list of subdirs in Arduino folder
if OS == "Windows":
    topdir = "C:/"
if OS == "Linux":
    topdir = "/"


def list_subdirs(folder):

    return([f.name for f in os.scandir(folder) if f.is_dir()])

def step(dirpath):
    dirs = list_subdirs(dirpath)
    if ARDUINO_INSTALL_DIR_NAME in dirs:
        arduino_potential_path = dirpath + '/' + ARDUINO_INSTALL_DIR_NAME        
        subdirs = list_subdirs(arduino_potential_path)
        if all(d in subdirs for d in ARDUINO_SUBDIRS):
            return(arduino_potential_path)
    if dirs:
        # if there are subdirectories, searching recursively
        for d in dirs:
            child_path = dirpath + "/" + d
            print(child_path)
            try:
                step(child_path)
            except:
                print("Permission denied:" + child_path)


print(step(topdir))



