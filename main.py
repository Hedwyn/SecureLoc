if __name__ == "__main__":
    from pandac.PandaModules import load_prc_file
    configfiles = ["antialias.prc"]
    for prc in configfiles:
        load_prc_file(prc)
    from application import Application
    game_app = Application()
    game_app.run()
