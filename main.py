if __name__ == "__main__":
    from pandac.PandaModules import load_prc_file
    configfiles = ["antialias.prc"]
    for prc in configfiles:
        load_prc_file(prc)
    from application import Application
    from Menu import Menu
    from parameters import HEADLESS
    from threading import Thread
    menu = Menu()
    menu.setDaemon(True)
    menu.start()
    game_app = Application(menu)
    if not(HEADLESS):
        game_app.run()
