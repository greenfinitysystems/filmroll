import ttkbootstrap as tb
import multiprocessing
from ui.mainwindow import FilmrollGUI

# main application
def main():
    root = tb.Window(themename="flatly")
    FilmrollGUI(root)
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    FilmrollGUI.show_splash(main)
