if __name__ == "__main__":
    from panda3d.core import load_prc_file
  
    import ips
    from ips.core.application import Application
    from ips.gui.menu import Menu
    from ips.core.parameters import HEADLESS
    
    from threading import Thread
    menu = Menu()
    menu.setDaemon(True)
    menu.start()
    game_app = Application(menu)
    if not(HEADLESS):
        game_app.run()
