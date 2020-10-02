# Teensyduino Core Library
# http://www.pjrc.com/teensy/
# Copyright (c) 2017 PJRC.COM, LLC.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# 1. The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# 2. If the Software is incorporated into a build system that allows
# selection among a list of target devices, then similar target
# devices manufactured by PJRC.COM must be included in the list of
# target devices and selectable in the same manner.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# set your MCU type here, or make command line `make MCU=MK20DX256`
MCU=MK20DX256
CPU_SPEED = 72000000 #default
#MCU=MKL26Z64
#MCU=MK64FX512
#MCU=MK66FX1M0
PROJECTNAME= Anchor
BINNAME= $(PROJECTNAME)
PROJECTSDIR= ../Projects
PROJECTPATH= $(PROJECTSDIR)/$(PROJECTNAME)
# make it lower case
LOWER_MCU := $(subst A,a,$(subst B,b,$(subst C,c,$(subst D,d,$(subst E,e,$(subst F,f,$(subst G,g,$(subst H,h,$(subst I,i,$(subst J,j,$(subst K,k,$(subst L,l,$(subst M,m,$(subst N,n,$(subst O,o,$(subst P,p,$(subst Q,q,$(subst R,r,$(subst S,s,$(subst T,t,$(subst U,u,$(subst V,v,$(subst W,w,$(subst X,x,$(subst Y,y,$(subst Z,z,$(MCU)))))))))))))))))))))))))))
MCU_LD = $(LOWER_MCU).ld

PROJECTS_SUBDIRS = $(sort $(dir $(wildcard $(PROJECTSDIR)/*/)))


TARGET = main

# anchor ID should be given in args of make command. Default value 1
NODE_ID = 1
NB_ANCHORS = 4

# Those that specify a NO_ARDUINO environment variable will
# be able to use this Makefile with no Arduino dependency.
# Please note that if ARDUINOPATH was set, it will override
# the NO_ARDUINO behaviour.
#NO_ARDUINO = 1
ifndef NO_ARDUINO
# Path to your arduino installation
ARDUINOPATH ?= ../../../../..
endif

# configurable options
OPTIONS = -DF_CPU=$(CPU_SPEED) -DUSB_SERIAL -DLAYOUT_US_ENGLISH -DUSING_MAKEFILE -DNODE_ID=$(NODE_ID) -DNB_ANCHORS=$(NB_ANCHORS)

# options needed by many Arduino libraries to configure for Teensy 3.x
OPTIONS += -D__$(MCU)__ -DARDUINO=10805 -DTEENSYDUINO=141

# use "cortex-m4" for Teensy 3.x
# use "cortex-m0plus" for Teensy LC
CPUARCH = cortex-m4
#CPUARCH = cortex-m0plus


# Other Makefiles and project templates for Teensy 3.x:
#
# https://github.com/apmorton/teensy-template
# https://github.com/xxxajk/Arduino_Makefile_master
# https://github.com/JonHylands/uCee


#************************************************************************
# Location of Teensyduino utilities, Toolchain, and Arduino Libraries.
# To use this makefile without Arduino, copy the resources from these
# locations and edit the pathnames.  The rest of Arduino is not needed.
#************************************************************************

ifdef ARDUINOPATH


# path location for Teensy Loader, teensy_post_compile and teensy_reboot (on Linux)
#TOOLSPATH = $(abspath $(ARDUINOPATH)/hardware/tools)
TOOLSPATH  = "C:\Program Files (x86)\Arduino\hardware\tools"
# path location for Arduino libraries (currently not used)
#LIBRARYPATH = $(abspath $(ARDUINOPATH)/libraries)
LIBRARYPATH = "C:\Users\pestourb\Documents\Arduino\libraries\AES-master"
# path location for the arm-none-eabi compiler
#COMPILERPATH = $(abspath $(ARDUINOPATH)/hardware/tools/arm/bin)
COMPILERPATH = "C:\Program Files (x86)\Arduino\hardware\tools\arm\bin"

else
# Default to the normal GNU/Linux compiler path if NO_ARDUINO
# and ARDUINOPATH was not set.
COMPILERPATH ?= /usr/bin

endif

#************************************************************************
# Settings below this point usually do not need to be edited
#************************************************************************
OBJ_DEPENDENCIES = $(addsuffix $(SRCDIR)/$(HEADERDIR), $(addprefix -I, $(PROJECTS_SUBDIRS)))
#OBJ_DEPENDENCIES = -I../PROJECTS/PKCE/src/header
INCLUDE = -I$(LIBS_H_PATH) -I$(PROJECTS_H_PATH)
# CPPFLAGS = compiler options for C and C++
CPPFLAGS = -Wall -g -Os -mcpu=$(CPUARCH) -mthumb -MMD -MP $(OPTIONS) -I. -I $(LIBRARYPATH) $(INCLUDE)  -I "C:\Program Files (x86)\Arduino\hardware\teensy\avr\libraries\SPI" -I "C:\WinAVR-20100110\avr32\include"

# compiler options for C++ only
CXXFLAGS = -std=gnu++14 -felide-constructors -fno-exceptions -fno-rtti

# compiler options for C only
CFLAGS =

# linker options
LDFLAGS = -Os  -Wl,--gc-sections,--defsym=__rtc_localtime=0 --specs=nano.specs -mcpu=$(CPUARCH) -mthumb -T$(MCU_LD)

# additional libraries to link
LIBS = -lm


# names for the compiler programs
CC = $(COMPILERPATH)/arm-none-eabi-gcc
CXX = $(COMPILERPATH)/arm-none-eabi-g++
OBJCOPY = $(COMPILERPATH)/arm-none-eabi-objcopy
SIZE = $(COMPILERPATH)/arm-none-eabi-size

# Project subdirectories
BINDIR = bin
OBJDIR = obj
SRCDIR = src
HEADERDIR = header
CPPDIR = cpp

# automatically create lists of the sources and objects
# Arduino Libs
LIBS_H_PATH = $(SRCDIR)/$(HEADERDIR)
LIBSPATH = $(SRCDIR)/$(CPPDIR)
LIBS_C_FILES := $(wildcard $(LIBSPATH)/*.c)
LIBS_CPP_FILES := $(wildcard $(LIBSPATH)/*.cpp)
LIBS_OBJS_FILES = $(notdir $(LIBS_C_FILES:.c=.o)) $(notdir $(LIBS_CPP_FILES:.cpp=.o))
LIBS_OBJS = $(foreach obj,$(LIBS_OBJS_FILES),$(OBJDIR)/$(obj) )

# Project files
PROJECTS_H_PATH = $(PROJECTPATH)/$(SRCDIR)/$(HEADERDIR)
PROJECT_C_FILES :=  $(wildcard $(PROJECTPATH)/$(SRCDIR)/$(CPPDIR)/*.c)
PROJECT_CPP_FILES :=  $(wildcard $(PROJECTPATH)/$(SRCDIR)/$(CPPDIR)/*.cpp)
PROJECT_OBJS_FILES = $(notdir $(PROJECT_CPP_FILES:.cpp=.o))
PROJECT_OBJS = $(foreach obj,$(PROJECT_OBJS_FILES),$(PROJECTPATH)/$(OBJDIR)/$(obj) )
OTHER_PROJECTS_OBJS_FILES :=



# global list of object files
#OBJS = $(foreach obj,$(LIBS_OBJS),$(OBJDIR)/$(obj)) $(foreach obj,$(PROJECT_OBJS),$(PROJECTPATH)/$(OBJDIR)/$(obj))
OBJS = $(LIBS_OBJS) $(PROJECT_OBJS)



# the actual makefile rules (all .o files built by GNU make's default implicit rules)

all: $(BINNAME).hex

$(BINNAME).hex: $(PROJECTPATH)/$(BINDIR)/$(PROJECTNAME).elf
	$(SIZE) $<
	$(OBJCOPY) -O ihex -R .eeprom $< $(PROJECTPATH)/$(BINDIR)/$@
ifneq (,$(wildcard $(TOOLSPATH)))
	@echo compiling dependencies
	$(TOOLSPATH)/teensy_post_compile -file=$(basename $@) -path=$(shell pwd) -tools=$(TOOLSPATH)
	-$(TOOLSPATH)/teensy_reboot
endif


${OBJDIR}/%.o:	$(SRCDIR)/$(CPPDIR)/%.cpp
	@echo $@
	@echo compiling arduino libs objects file
	@echo $<
	$(CXX) $(LDFLAGS) $(CPPFLAGS) $(CXXFLAGS) -c $< -o $@

${OBJDIR}/%.o:	$(SRCDIR)/$(CPPDIR)/%.c
	@echo $@
	@echo compiling arduino libs objects file
	@echo $<
	$(CC) $(LDFLAGS) $(CPPFLAGS) $(CFLAGS)  -c $< -o $@

${PROJECTPATH}/${OBJDIR}/%.o:	$(PROJECTPATH)/$(SRCDIR)/$(CPPDIR)/%.cpp
	@echo $@
	@echo compiling projects objects file
	@echo $<
	$(CXX) $(LDFLAGS) $(CPPFLAGS) $(CXXFLAGS) $(OBJ_DEPENDENCIES) -c $< -o $@


${PROJECTPATH}/${OBJDIR}/%.o:	$(PROJECTPATH)/$(SRCDIR)/$(CPPDIR)/%.c
	@echo $@
	@echo compiling projects objects file
	@echo $<
	$(CC) $(LDFLAGS) $(CPPFLAGS) $(CFLAGS) $(OBJ_DEPENDENCIES)  -c $< -o $@


${PROJECTPATH}/${BINDIR}/$(PROJECTNAME).elf: $(OBJS) $(MCU_LD)
	@echo making elf file
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(OTHER_PROJECTS_OBJS_FILES) $(LIBS)

build: $(LIBS_OBJS)
	@echo Arduino libraries built

# compiler generated dependency info
# -include $(OBJS:.o=.d)
# -include $(PROJECT_OBJS:.o=.d)

libclean:
	@echo cleaning previous built
	rm -f  *.o *.d *.hex *.elf $(OBJDIR)/*.o  $(OBJDIR)/*.d
	rm -f $(PROJECTPATH)/$(OBJDIR)/*.o $(PROJECTPATH)/$(OBJDIR)/*.d $(PROJECTPATH)/$(BINDIR)/*.elf $(PROJECTPATH)/$(BINDIR)/*.hex

clean:
	rm -f $(PROJECTPATH)/$(OBJDIR)/*.o
	rm -f $(PROJECTPATH)/$(OBJDIR)/*.d
	rm -f $(PROJECTPATH)/$(BINDIR)/*.elf
	rm -f $(PROJECTPATH)/$(BINDIR)/*.hex


# does not remove hex files
softclean:
	rm -f $(PROJECTPATH)/$(OBJDIR)/*.o
	rm -f $(PROJECTPATH)/$(OBJDIR)/*.d
	rm -f $(PROJECTPATH)/$(BINDIR)/*.elf



test:
	@echo  $(OTHER_PROJECTS_OBJS_FILES)
