import multiprocessing
from ui.mainwindow import FilmrollGUI

if __name__ == "__main__":
    multiprocessing.freeze_support()
    FilmrollGUI.run()
