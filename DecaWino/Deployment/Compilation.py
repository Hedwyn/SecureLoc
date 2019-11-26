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

SERIAL_ROOT = 'COM'
# CPU clock speed
CPU_SPEED = ["24 Mhz","48 Mhz","72 Mhz","96 Mhz","120 Mhz"]
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
        # tkinter initilization
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

        # Serial devices
        self.serial_devices_scrollbar = ttk.Scrollbar(self.root)
        self.serial_devices = Listbox(self.root, yscrollcommand= self.projects_scrollbar.set, font = ('Calibri Corps',11), background = '#fafafa')
        # linking console scrollbar to Listbox
        self.serial_devices_scrollbar.config(command=self.projects_listbox.yview)


        # buttons
        compile_btn = ttk.Button(self.root, text = "Compile", style = 'W.TButton', command = lambda: self.compile(self.projects_listbox.get(ACTIVE),self.cpu_speed.get()))
        build_btn = ttk.Button(self.root, text = "Build Arduino Libs",style = 'W.TButton',command = lambda: self.build(self.cpu_speed.get()))
        new_project = ttk.Button(self.root, text= "Create New Project", style = 'W.TButton', command = self.create_new_project)
        serial_scan = ttk.Button(self.root, text= "Scan", style = 'W.TButton', command = self.serial_scan)
        flash_btn = ttk.Button(self.root, text = "Flash", style = 'W.TButton', command = lambda: self.flash(self.serial_devices.get(ACTIVE)))
        deployment_btn = ttk.Button(self.root, text = "Deployment", style = 'W.TButton', command = self.deployment)
        cancel_btn = ttk.Button(self.root, text = "Cancel", style = 'W.TButton', command = self.cancel)

        # spinbox for CPU frequency
        cpu_speed_spinbox = Spinbox(self.root, values=CPU_SPEED, textvariable=self.cpu_speed)

        # entries
        self.project_entry = Entry(self.root)

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

        # menu commands
        build_btn.grid(row = 1, column = 1, rowspan = 2)
        compile_btn.grid(row = 1, column = 2, rowspan = 2, padx = 8)
        cancel_btn.grid(row = 1, column = 3, rowspan = 2, padx = 8)

        cpu_speed_lbl.grid(row = 1, column = 4)
        cpu_speed_spinbox.grid(row = 2, column = 4)

        serial_scan.grid(row = 1, column = 5, rowspan = 2)

        # console
        self.console.grid(row = 3, column = 1, columnspan = 4, pady = 5, padx = 5)

        # serial devices listboc
        self.serial_devices.grid(row = 3, column = 5)
        flash_btn.grid(row = 4, column = 5)
        deployment_btn.grid(row = 5, column = 5, pady = 6)



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


    def compile(self,project_name,cpu_speed):
        """Compiles the target project selcted in the projects scrollbar"""
        # checking if the CPU speed has changed
        if (cpu_speed != self.current_cpu_speed):
            self.build(cpu_speed)

        # cleaning previous files
        self.console_handler("cd teensy3 && make softclean PROJECTNAME=" + project_name)
        # compiling the project
        self.console_handler("cd teensy3 && make PROJECTNAME=" + project_name, "Compiling " + project_name, "Done")



        # updating cpu_speed
        self.current_cpu_speed = cpu_speed


    def build(self,cpu_speed):
        """Builds the Arduino libraries.
        Arduino libs have to be rebuilt if a different CPU frequency is chosen"""
        # cleaning previous built
        self.console_handler("cd teensy3 && make clean","Building Arduino Libraries","Done")

        # converting CPU speed from MHz to kHz
        cpu_speed = cpu_speed[:2] + "000000"

        # building arduino libraries
        self.console_handler("cd teensy3 && make CPU_SPEED=" + cpu_speed)

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
            print("Could not prcoeed to project creation: project name already exists")

    def serial_scan(self):
        """Scans for open serial ports and appends found serial devices to serial devices scrollbar"""
        # deleting the current entries
        # TODO

        ports = list(serial.tools.list_ports.comports())
        for entry in [port.device for port in ports]:
            if entry.startswith('COM'):
                # appending to serial devives scrollbar
                self.serial_devices.insert(END,entry)

    def flash(self,serial_port = ''):
        """flashes the target serial port with the active project hex file"""
        try:
            # flashing
            self.console_display("flashing, press the teensy button")
            self.console_handler('teensy_loader_cli.exe -mmcu=mk20dx256 -s -v ' + PROJECTS_DIR + '/' + self.projects_listbox.get(ACTIVE) + '/' + BINDIR +'/' + self.projects_listbox.get(ACTIVE) + '.hex')
        except:
            self.console_display("Target serial device is disconnected")

    def deployment(self):
        """Deploys the chosen project on the platform. The ID's and keys are automaticcaly generated in the compiled files.
        Teensyduino's are remotely flashed by RPI. The config (IDs, IPs) can be changed in config.txt"""
        Console.console = self
        deploy_hex_files('config2.txt',self.projects_listbox.get(ACTIVE))
        global_flash('config2.txt')

    def cancel(self):
        """Cancel the currents process - sends Ctrl + C to terminal"""
        self.console_handler("\x03")

menu = CompilationMenu()
