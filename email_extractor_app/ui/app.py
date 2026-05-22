import os
import tkinter as tk
from tkinter import messagebox, ttk

from ..config import APP_ICON_ICO, APP_ICON_PNG, app_path
from ..credentials import CredentialsLoader
from ..theme import ThemeManager
from .results_tab import ResultsTab


class EmailExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Extractor")
        self.root.geometry("1500x860")
        self.root.minsize(980, 620)

        self.credentials = {}
        self.icon_image = None
        self.credentials_loader = CredentialsLoader()

        ThemeManager(self.root).apply()
        self.set_app_icon()
        self.create_widgets()
        self.load_credentials_to_screen()

    def set_app_icon(self):
        try:
            ico_path = app_path(APP_ICON_ICO)
            png_path = app_path(APP_ICON_PNG)

            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                self.icon_image = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, self.icon_image)
        except Exception:
            # Icon is optional. The application still runs if the icon file is invalid or missing.
            pass

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=12, style="Modern.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_header(main_frame)
        self.create_credentials_panel(main_frame)
        self.create_tabs(main_frame)

    def create_header(self, parent):
        header_frame = ttk.Frame(parent, padding=(16, 11), style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Email Extractor", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header_frame,
            text="General email search and bank transaction exports in one workspace",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def create_credentials_panel(self, parent):
        login_frame = ttk.LabelFrame(
            parent,
            text="Login Loaded From credentials.json",
            padding=10,
            style="Card.TLabelframe",
        )
        login_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(login_frame, text="IMAP Server:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        self.imap_server_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.imap_server_var, width=24, state="readonly").grid(
            row=0, column=1, sticky="w", pady=3
        )

        ttk.Label(login_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=3)
        self.imap_port_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.imap_port_var, width=8, state="readonly").grid(
            row=0, column=3, sticky="w", pady=3
        )

        ttk.Label(login_frame, text="Mailbox:").grid(row=0, column=4, sticky="w", padx=(18, 8), pady=3)
        self.mailbox_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.mailbox_var, width=18, state="readonly").grid(
            row=0, column=5, sticky="w", pady=3
        )

        ttk.Label(login_frame, text="Login Email:").grid(row=0, column=6, sticky="w", padx=(18, 8), pady=3)
        self.login_email_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.login_email_var, width=32, state="readonly").grid(
            row=0, column=7, sticky="w", pady=3
        )

        ttk.Label(login_frame, text="Password:").grid(row=0, column=8, sticky="w", padx=(18, 8), pady=3)
        self.password_display_var = tk.StringVar(value="Loaded from file")
        ttk.Entry(login_frame, textvariable=self.password_display_var, width=18, show="*", state="readonly").grid(
            row=0, column=9, sticky="w", pady=3
        )

        self.credentials_status_var = tk.StringVar(value="Loading credentials...")
        ttk.Label(login_frame, textvariable=self.credentials_status_var, style="Muted.TLabel").grid(
            row=1, column=0, columnspan=10, sticky="w", pady=(4, 0)
        )

    def create_tabs(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.general_tab = ResultsTab(self.notebook, self, "general")
        self.bank_tab = ResultsTab(self.notebook, self, "bank")

        self.notebook.add(self.general_tab, text="General")
        self.notebook.add(self.bank_tab, text="Bank Transactions")

    def load_credentials_to_screen(self):
        try:
            self.credentials = self.credentials_loader.load()

            self.imap_server_var.set(str(self.credentials["imap_server"]))
            self.imap_port_var.set(str(self.credentials["imap_port"]))
            self.mailbox_var.set(str(self.credentials["mailbox"]))
            self.login_email_var.set(str(self.credentials["login_email"]))
            self.password_display_var.set("********")
            self.credentials_status_var.set("credentials.json loaded successfully.")
        except Exception as exc:
            self.credentials = {}
            self.general_tab.run_button.config(state=tk.DISABLED)
            self.bank_tab.run_button.config(state=tk.DISABLED)
            self.credentials_status_var.set("credentials.json could not be loaded.")
            messagebox.showerror("Credentials Error", str(exc))

