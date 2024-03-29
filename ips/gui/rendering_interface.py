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

@file rendering_interface.py
@author Baptiste Pestourie
@date 2019 July 1st
@brief Middleware for the rendering engine
@see https://github.com/Hedwyn/SecureLoc
"""

## subpackages
from ips.core.parameters import HEADLESS

## other libraries
import sys
if HEADLESS:
    from ips.gui.rendering_stub import *
    try:
        from direct.task import Task
    except:
        print("You need to install at least Task module from Panda 3D to run the localization engine.")
        sys.exit(0)

else:
    # checking if Panda 3D packages are installed
    try:
        # trying to import 3D engines packages
        from panda3d.core import *
        from direct.showbase.ShowBase import ShowBase

    except IOError:
        # if 3D packages are missing
        print("Some Panda 3D engine packages are missing. Check your installation. Forcing Headless mode")
        try:
            from direct.task import Task
        except:
            print("You need to install at least Task module from Panda 3D to run the localization engine.")
            sys.exit(0)

        # if task module is found
        print("forcing Headless mode")
        from ips.gui.rendering_stub import *

    # if panda 3D's imports are successful
    import ips.gui.utils
    # no need for stub if we're sucessful so far, importing the Rendering module
    from ips.gui.rendering import *




# if stubbing:
#     from RenderingStub import *
# else:
#     from Rendering import *
