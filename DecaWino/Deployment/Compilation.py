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

@file Compilation.py
@author Baptiste Pestourie
@date 2019 March 1st
@brief Compilation menu for automated compilation & deployment
@see https://github.com/Hedwyn/SecureLoc
"""

from tkinter import *
import tkinter as tk
from tkinter.ttk import *
from tkinter import ttk
from Deployment import *
from threading import Thread
import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pipe
import sys
import serial.tools.list_ports
import platform

OS =  platform.system() # should return Linux, Darwin or Windows
SERIAL_ROOT = 'COM'
# CPU clock speed
CPU_SPEED = ["96 Mhz","120 Mhz","24 Mhz","48 Mhz","72 Mhz"]

if OS == 'Windows':
    # windows requires .exe
    WIN_EXTENSION = ".exe"
else:
    WIN_EXTENSION = ""
SHELL_ON = True
PROJECTS_DIR = "Projects"
SRCDIR = 'src'
HEADERDIR = 'header'
OBJDIR = 'obj'
CPPDIR = 'cpp'
BINDIR = 'bin'
PROJECT_SUBDIR = [SRCDIR, SRCDIR + '/' + HEADERDIR, SRCDIR + '/' + CPPDIR, OBJDIR, BINDIR]
COLUMNS_SIZE = 6


def shell_exec(menu,cmd):
    """Overrides shell_exec function from Deployment so the output is displayed in the console"""
    menu.console_display("override sucesss")
    menu.console_handler(cmd)


class CompilationMenu(Frame):
    """Graphical User Interface for compiling projects. Features: projects overview,
    project architecture generation, flashing interface, platform deployment with a single button"""

    def __init__(self):
        # tkinter initialization
        self.root = Tk()
        Frame.__init__(self,self.root)
        self.root.title("SecureLoc Deployment Interface")
        self.root.configure(background = "#ffffff")  # white background

        # styling
        style = ttk.Style()
        style.configure('Menu.TLabel', font = ('Copperplate Gothic Light', 18), paddy = 15)
        style.configure('W.TButton', font =('Linux Libertine', 13), width = 20, background = 'black',foreground = '#00214b', padding = 12)
        style.configure('Standard.TLabel',font = ('Calibri Light', 14), anchor = CENTER, width = 15, background = '#a2c0fc', paddx = 10)

        # variables
        self.project_name = tk.StringVar()
        self.cpu_speed = tk.StringVar()

        # logo
        logo = PhotoImage(file = "utils/SecurelocLogo_1_.ppm")

        # labels
        logo_lbl = ttk.Label(self.root, image = logo, background = 'white')
        platform_lbl = ttk.Label(self.root, text = "SecureLoc Deployment Interface", style = 'Menu.TLabel')
        projects_lbl = ttk.Label(self.root, text = "Projects", style = 'Standard.TLabel')
        new_project_lbl = ttk.Label(self.root, text = "New Project Name", style = 'Standard.TLabel')
        cpu_speed_lbl = ttk.Label(self.root, text = "CPU Frequency", style = 'Standard.TLabel')
        n_compile_lbl = ttk.Label(self.root, text = "#hex to generate:", style = 'Standard.TLabel')
        #console =  tk.Label(self.root, text = "Displaying random stuff", height = 10, width = 80)

        # Projects scrolling Menu
        projects_list = os.listdir('Projects')
        self.projects_scrollbar = ttk.Scrollbar(self.root)
        self.projects_listbox = Listbox(self.root, yscrollcommand= self.projects_scrollbar.set, font = ('Calibri Corps',11), background = '#fafafa')
        # inserting project names into Listbox
        for project in projects_list:
            self.projects_listbox.insert(END,project)

        # linking scrollbar to Listbox
        self.projects_scrollbar.config(command=self.projects_listbox.yview)

        # console
        self.console_scrollbar = ttk.Scrollbar(self.root)
        self.console = Listbox(self.root, yscrollcommand= self.projects_scrollbar.set, font = ('Calibri Corps',11), background = '#fafafa', height = 10, width = 100)
        # linking console scrollbar to Listbox
        self.console_scrollbar.config(command=self.projects_listbox.yview)
        # linking console output to menu
        Console.console = self

        # Serial devices
        self.hex_files_scrollbar = ttk.Scrollbar(self.root)
        self.hex_files = Listbox(self.root, yscrollcommand= self.projects_scrollbar.set, font = ('Calibri Corps',11), background = '#fafafa')
        # linking console scrollbar to Listbox
        self.hex_files_scrollbar.config(command=self.projects_listbox.yview)


        # buttons
        compile_btn = ttk.Button(self.root, text = "Compile", style = 'W.TButton', command = lambda: self.compile(self.projects_listbox.get(ACTIVE),self.cpu_speed.get()))
        n_compile_btn = ttk.Button(self.root, text = "n-Compile", style = 'W.TButton', command = lambda: self.n_compile(self.projects_listbox.get(ACTIVE),self.cpu_speed.get(), self.n_compile_entry.get()))
        clean_btn = ttk.Button(self.root, text = "Clean Project", style = 'W.TButton', command = lambda: self.clean(self.projects_listbox.get(ACTIVE)))
        build_btn = ttk.Button(self.root, text = "Build Arduino Libs",style = 'W.TButton',command = lambda: self.build(self.cpu_speed.get()))
        new_project = ttk.Button(self.root, text= "Create New Project", style = 'W.TButton', command = self.create_new_project)
        hex_btn = ttk.Button(self.root, text= "Scan Hex", style = 'W.TButton', command = self.get_available_hex)
        flash_btn = ttk.Button(self.root, text = "Flash", style = 'W.TButton', command = lambda: self.flash(self.hex_files.get(ACTIVE)))
        deployment_btn = ttk.Button(self.root, text = "Deployment", style = 'W.TButton', command = self.deployment)
        cancel_btn = ttk.Button(self.root, text = "Cancel", style = 'W.TButton', command = self.cancel)

        # spinbox for CPU frequency
        cpu_speed_spinbox = Spinbox(self.root, values=CPU_SPEED, textvariable=self.cpu_speed)

        # entries
        self.project_entry = Entry(self.root)
        self.n_compile_entry = Entry(self.root)

        # others
        self.current_cpu_speed = self.cpu_speed.get()

        # grid placement

        # Header
        platform_lbl.grid(row = 0, column = 0, columnspan = COLUMNS_SIZE - 1)
        logo_lbl.grid(row = 0, column = COLUMNS_SIZE - 1, pady = 6)

        # projects row
        projects_lbl.grid(row = 1, column = 0, rowspan = 2)
        self.projects_listbox.grid(row = 3, column = 0)
        new_project_lbl.grid(row = 4, column = 0)
        self.project_entry.grid(row = 5, column = 0, pady = 3)
        new_project.grid(row = 6, column = 0)
        clean_btn.grid(row = 7, column = 0, pady = 6)

        # menu commands
        build_btn.grid(row = 1, column = 1, rowspan = 2)
        compile_btn.grid(row = 1, column = 2, rowspan = 2, padx = 8)
        cancel_btn.grid(row = 1, column = 3, rowspan = 2, padx = 8)

        cpu_speed_lbl.grid(row = 1, column = 4)
        cpu_speed_spinbox.grid(row = 2, column = 4)

        hex_btn.grid(row = 1, column = 5, rowspan = 2)

        # console
        self.console.grid(row = 3, column = 1, columnspan = 4, pady = 5, padx = 5)

        # Right column -> Hex-related commands
        self.hex_files.grid(row = 3, column = 5)
        flash_btn.grid(row = 4, column = 5)
        n_compile_btn.grid(row = 5, column = 5, pady = 6)
        n_compile_lbl.grid(row = 4, column = 4)
        self.n_compile_entry.grid(row = 5, column = 4)
        deployment_btn.grid(row = 6, column = 5, pady = 6)




        # starting Menu
        self.root.mainloop()

    def exec_command(self,cmd, child_conn):
        """executes the given command and sends stdout to the pipe"""
        p = Popen(cmd, stdout = PIPE, stderr= STDOUT, shell = SHELL_ON)
        for line in iter(p.stdout.readline, b''):
            child_conn.send(line)


        p.stdout.close()
        p.wait()

    def console_display(self,msg):
        """displays a message on the menu console"""
        self.console.insert(END,msg)
        self.console.see(END)
        self.console.update()


    def console_handler(self, cmd = None,start_msg = None, end_msg = None):
        """Executes a command as a subprocess and redirects stdout to the menu console.
        Can display additional messages after and before command.
        If no command is given, displays only the messages in arguments"""
        if start_msg:
            self.console_display(start_msg)

        if cmd:
            # creating a pipe for the communication with the thread
            p, q = Pipe()
            t = Thread(target = self.exec_command, args = (cmd,q))
            t.start()
            while t.is_alive():
                if p.poll(0.1):
                    line = p.recv()
                    self.console_display(line.decode('utf-8'))
            t.join()
            p.close()
            q.close()




        if end_msg:
            self.console_display(end_msg)


    def clean(self, project_name):
        """Cleans the hex directory of the selected project"""
        self.console_handler("cd teensy3 && make clean PROJECTNAME=" + project_name)

        # refreshing hex listbox
        self.get_available_hex()

    def compile(self,project_name,cpu_speed):
        """Compiles the target project selcted in the projects scrollbar"""
        # checking if the CPU speed has changed
        if (cpu_speed != self.current_cpu_speed):
            self.build(cpu_speed)

        # cleaning previous files
        self.console_handler("cd teensy3 && make softclean PROJECTNAME=" + project_name)
        # compiling the project
        #self.console_handler("cd teensy3 && make PROJECTNAME=" + project_name, "Compiling " + project_name, "Done")
        compile_hex_file(project_name, binname = project_name)


        # updating cpu_speed
        self.current_cpu_speed = cpu_speed

        # refreshing hex listbox
        self.get_available_hex()

    def n_compile(self, project_name, cpu_speed, n):
        """Compiles n times the projects with successive ID's in {1,..., n}"""
        if (cpu_speed != self.current_cpu_speed):
            self.build(cpu_speed)

        # cleaning previous files
        self.console_handler("cd teensy3 && make softclean PROJECTNAME=" + project_name)
        # compiling the project
        self.console_display("Number of projects: " + n)
        compilation(int(n), project_name)

        # updating cpu_speed
        self.current_cpu_speed = cpu_speed

        # refreshing hex listbox
        self.get_available_hex()


    def build(self,cpu_speed):
        """Builds the Arduino libraries.
        Arduino libs have to be rebuilt if a different CPU frequency is chosen"""
        # cleaning previous built
        self.console_handler("cd teensy3 && make libclean","Building Arduino Libraries","Done")

        # converting CPU speed from MHz to kHz
        cpu_speed = cpu_speed[:2] + "000000"

        # building arduino libraries
        self.console_handler("cd teensy3 && make build CPU_SPEED=" + cpu_speed)

    def create_new_project(self):
        """Create a new project directory with a standard architecture"""
        project_name = self.project_entry.get()

        # clearing the project name entry
        self.project_entry.delete(0, 'end')

        project_path = PROJECTS_DIR + '/' + project_name
        if not(os.path.exists(project_path)):
            # creating  project directory
            os.mkdir(project_path)
            # creating the project tree
            for subdir in PROJECT_SUBDIR:
                # making subdir
                os.mkdir(project_path +'/' + subdir)
            # adding new project to projects listbox
            self.projects_listbox.insert(END,project_name)


        else:
            print("Could not proceed to project creation: project name already exists")

    def serial_scan(self):
        """Scans for open serial ports and appends found serial devices to serial devices scrollbar"""
        # deleting the current entries
        # TODO

        ports = list(serial.tools.list_ports.comports())
        for entry in [port.device for port in ports]:
            if entry.startswith('COM'):
                # appending to serial devives scrollbar
                self.hex_files.insert(END,entry)

    def get_available_hex(self):
        """Displays the available hex files for the selected project in the hex scrollbar"""
        project_name = self.projects_listbox.get(ACTIVE)
        hex_list = os.listdir(PROJECTS_DIR + '/' + project_name + '/' + BINDIR)

        # emptying Scrollbar
        self.hex_files.delete(0,END)

        # displaying hex list
        for entry in hex_list:
            if entry.endswith('.hex'):
                self.hex_files.insert(END,entry)

    def flash(self,serial_port = ''):
        """flashes the target serial port with the active project hex file"""
        try:
            # flashing
            self.console_display("flashing, press the teensy button")
            self.console_handler(BOOTLOADER + WIN_EXTENSION + ' -mmcu=mk20dx256 -s -v ' + PROJECTS_DIR + '/' + self.projects_listbox.get(ACTIVE) + '/' + BINDIR +'/' + self.hex_files.get(ACTIVE))
        except:
            self.console_display("Target serial device is disconnected")

    def deployment(self):
        """Deploys the chosen project on the platform. The ID's and keys are automaticcaly generated in the compiled files.
        Teensyduino's are remotely flashed by RPI. The config (IDs, IPs) can be changed in config.txt"""

        deploy_hex_files('config.txt',self.projects_listbox.get(ACTIVE))
        global_flash('config.txt')

    def cancel(self):
        """Cancel the currents process - sends Ctrl + C to terminal"""
        self.console_handler("\x03")

menu = CompilationMenu()
