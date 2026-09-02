# region(python_imports)

from tkinter import messagebox as mb

# endregion

# region(project_imports)

# Nothing here yet

# endregion

# region(globals)

# Nothing here yet

# endregion

class messagebox:

# region(static_methods)

    @staticmethod
    def showinfo(title, message):
        mb.showinfo(title, message)

    @staticmethod
    def askyesno(title, message):
        return mb.askyesno(title, message)

    @staticmethod
    def showerror(title, message):
        mb.showerror(title, message)

# endregion