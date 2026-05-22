import tkinter as tk

from .config import configure_windows_taskbar_icon
from .ui.app import EmailExtractorApp


def main():
    configure_windows_taskbar_icon()
    root = tk.Tk()
    EmailExtractorApp(root)
    root.mainloop()
