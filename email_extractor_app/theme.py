import tkinter as tk
from tkinter import ttk

from .config import COLORS


class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(root)

    def apply(self):
        self.root.configure(bg=COLORS["bg"])

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        font_family = "Segoe UI"
        default_font = (font_family, 10)

        self.style.configure(".", font=default_font, background=COLORS["bg"], foreground=COLORS["text"])
        self.style.configure("TLabel", background=COLORS["surface"], foreground=COLORS["text"])
        self.style.configure("Modern.TFrame", background=COLORS["bg"])
        self.style.configure("Surface.TFrame", background=COLORS["surface"])
        self.style.configure("Toolbar.TFrame", background=COLORS["bg"])
        self.style.configure("Header.TFrame", background=COLORS["header"], relief="flat")
        self.style.configure(
            "Title.TLabel",
            background=COLORS["header"],
            foreground="#ffffff",
            font=(font_family, 18, "bold"),
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=COLORS["header"],
            foreground="#d9fffb",
            font=(font_family, 9),
        )
        self.style.configure(
            "Muted.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["muted"],
            font=(font_family, 9),
        )
        self.style.configure(
            "Status.TLabel",
            background=COLORS["surface_alt"],
            foreground=COLORS["success"],
            font=(font_family, 9, "bold"),
            padding=(10, 5),
        )
        self._apply_cards(font_family)
        self._apply_inputs()
        self._apply_buttons()
        self._apply_notebook(font_family)
        self._apply_treeview(font_family)

    def _apply_cards(self, font_family):
        self.style.configure(
            "Card.TLabelframe",
            background=COLORS["surface"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            relief="solid",
            padding=12,
        )
        self.style.configure(
            "Card.TLabelframe.Label",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=(font_family, 11, "bold"),
        )

    def _apply_inputs(self):
        self.style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=(7, 4),
        )
        self.style.map("TEntry", bordercolor=[("focus", COLORS["primary"])])
        self.style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["muted"],
            padding=(7, 4),
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            bordercolor=[("focus", COLORS["primary"])],
        )

    def _apply_buttons(self):
        self.style.configure(
            "TButton",
            background="#ffffff",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            focusthickness=0,
            padding=(11, 6),
        )
        self.style.map(
            "TButton",
            background=[("active", "#f1f5f9"), ("pressed", "#e2e8f0"), ("disabled", "#f1f5f9")],
            foreground=[("disabled", "#98a2b3")],
        )
        self.style.configure(
            "Accent.TButton",
            background=COLORS["primary"],
            foreground="#ffffff",
            bordercolor=COLORS["primary"],
            padding=(14, 6),
        )
        self.style.map(
            "Accent.TButton",
            background=[
                ("active", COLORS["primary_hover"]),
                ("pressed", COLORS["primary_pressed"]),
                ("disabled", "#93c5fd"),
            ],
            foreground=[("disabled", "#eff6ff")],
        )
        self.style.configure(
            "Danger.TButton",
            background="#ffffff",
            foreground=COLORS["danger"],
            bordercolor="#fecaca",
            padding=(11, 6),
        )
        self.style.map(
            "Danger.TButton",
            background=[("active", "#fef2f2"), ("pressed", "#fee2e2")],
            foreground=[("active", COLORS["danger_hover"])],
        )

    def _apply_notebook(self, font_family):
        self.style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(0, 6, 0, 0))
        self.style.configure(
            "TNotebook.Tab",
            background="#e8eef7",
            foreground=COLORS["muted"],
            padding=(16, 8),
            font=(font_family, 10, "bold"),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["surface"]), ("active", "#f8fafc")],
            foreground=[("selected", COLORS["primary"]), ("active", COLORS["text"])],
        )

    def _apply_treeview(self, font_family):
        self.style.configure(
            "Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            rowheight=28,
            font=(font_family, 9),
        )
        self.style.configure(
            "Treeview.Heading",
            background="#e8eef7",
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            font=(font_family, 9, "bold"),
            padding=(8, 8),
        )
        self.style.map(
            "Treeview",
            background=[("selected", COLORS["selected"])],
            foreground=[("selected", COLORS["text"])],
        )
