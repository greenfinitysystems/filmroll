# region(python_imports)

from ttkbootstrap.dialogs import Messagebox

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
        Messagebox.show_info(message, title)

    @staticmethod
    def askyesno(message, title):
        response = Messagebox.yesno(title, message)
        if response in ('Yes', 'yes', True):
            return True
        return False

    @staticmethod
    def showerror(message, title):
        Messagebox.show_error(title, message)

# endregion

