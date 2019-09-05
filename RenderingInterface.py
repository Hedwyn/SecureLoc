from parameters import HEADLESS
import sys
if HEADLESS:
    from RenderingStub import *
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
        import utils
        # no need for stub if we're sucessful so far, importing the Rendering module
        #stubbing = False
        from Rendering import *
    except:
        # if 3D packages are missing
        print("Some Panda 3D engine packages are missing. Check your installation. Forcing Headless mode")
        try:
            from direct.task import Task
        except:
            print("You need to install at least Task module from Panda 3D to run the localization engine.")
            sys.exit(0)

        # if task module is found
        print("forcing Headless mode")
        from RenderingStub import *




# if stubbing:
#     from RenderingStub import *
# else:
#     from Rendering import *
