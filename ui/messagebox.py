# region(python_imports)

import logging
from typing import Any
from ttkbootstrap.dialogs import Messagebox, MessageDialog

# endregion

# region(project_imports)

# There is nothing here

# endregion

# region(globals)

logwriter = logging.getLogger(__name__)

# endregion

class MessageBox:

# region(static_methods)

    @staticmethod
    def showinfo(title: str, message: str, parent: Any=None) -> None:
        MessageBox._show_dialog(
            title=title,
            message=message,
            parent=parent,
            icon="info-circle-fill",
            buttons=["OK:primary"]
        )

    @staticmethod
    def showwarning(title: str, message: str, parent: Any=None) -> None:
        MessageBox._show_dialog(
            title=title,
            message=message,
            parent=parent,
            icon="exclamation-triangle-fill",
            buttons=["OK:warning"]
        )

    @staticmethod
    def showerror(title: str, message: str, parent: Any=None) -> None:
        MessageBox._show_dialog(
            title=title,
            message=message,
            parent=parent,
            icon="exclamation-octagon-fill",
            buttons=["OK:danger"]
        )

    @staticmethod
    def askyesno(title: str, message: str, parent: Any=None) -> bool:
        result = MessageBox._show_dialog(
            title=title,
            message=message,
            parent=parent,
            icon="question-circle-fill",
            buttons=[
                "Yes:primary",
                "No:secondary"
            ]
        )

        return result in ('Yes', 'yes', True)

# endregion

# region (private_methods)

    @staticmethod
    def _show_dialog(title, message, parent=None, icon=None, buttons=None):
        """
        Show a ttkbootstrap MessageDialog centered over the parent window.
        This is implemented here rather than using Messagebox.show_xxx()
        because on Windows, ttkbootstrap 2.2.2 may reposition a transient
        Toplevel when it is deiconified. We therefore apply the final
        geometry after the window has been mapped.
        """
        try:
            # No parent: let ttkbootstrap handle the dialog normally.
            if parent is None:
                if buttons is None:
                    return Messagebox.show_info(message=message, title=title, icon=icon)
                dialog = MessageDialog(message=message, title=title, buttons=buttons, icon=icon)
                return dialog.show()

            # Create the themed dialog.
            dialog = MessageDialog(message=message, title=title, parent=parent, buttons=buttons or ["OK:primary"], icon=icon)
            dialog.build()
            dialog._toplevel.deiconify()
            dialog._toplevel.update_idletasks()

            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            dialog_width = dialog._toplevel.winfo_width()
            dialog_height = dialog._toplevel.winfo_height()

            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2

            # IMPORTANT:
            # Apply the position after deiconify(), because Windows can
            # reposition a transient Toplevel during deiconify().
            dialog._toplevel.geometry(f"+{x}+{y}")
            dialog._toplevel.update_idletasks()

            # Modal behavior.
            dialog._toplevel.grab_set()
            dialog._toplevel.wait_window()

            return dialog._result

        except Exception as e:
            logwriter.debug(f"MessageBox._show_dialog() - error: {e}")
            return None

# endregion

