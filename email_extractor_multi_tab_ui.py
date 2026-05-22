import csv
import email
import html
import imaplib
import json
import os
import re
import sys
import threading
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


# --------------------------------------------------
# credentials.json format
# --------------------------------------------------
# Put credentials.json in the same folder as this script.
#
# Example:
# {
#   "imap_server": "imap.gmail.com",
#   "imap_port": 993,
#   "mailbox": "INBOX",
#   "login_email": "your-email@gmail.com",
#   "password": "your-16-character-app-password"
# }
#
# For Gmail, use a Gmail App Password, not your normal Gmail password.
# Keep credentials.json private and do not upload it to GitHub.


APP_ICON_ICO = "app_icon.ico"
APP_ICON_PNG = "app_icon.png"
APP_USER_MODEL_ID = "gmail_transaction_alert.email_extractor.multi_tab"
COLORS = {
    "bg": "#f6f8fb",
    "surface": "#ffffff",
    "surface_alt": "#eef4ff",
    "border": "#d8e0ea",
    "text": "#172033",
    "muted": "#667085",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_pressed": "#1e40af",
    "success": "#0f766e",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "row_alt": "#f9fbff",
    "selected": "#dbeafe"
}


def app_path(file_name):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, file_name)


def configure_windows_taskbar_icon():
    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # Taskbar metadata is best-effort; Tk can still run without it.
        pass


def configure_theme(root):
    root.configure(bg=COLORS["bg"])

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    font_family = "Segoe UI"
    default_font = (font_family, 10)

    style.configure(".", font=default_font, background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("TLabel", background=COLORS["surface"], foreground=COLORS["text"])
    style.configure("Modern.TFrame", background=COLORS["bg"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Toolbar.TFrame", background=COLORS["bg"])

    style.configure(
        "Header.TFrame",
        background=COLORS["text"],
        relief="flat"
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["text"],
        foreground="#ffffff",
        font=(font_family, 22, "bold")
    )
    style.configure(
        "Subtitle.TLabel",
        background=COLORS["text"],
        foreground="#cbd5e1",
        font=(font_family, 10)
    )
    style.configure(
        "Section.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=(font_family, 11, "bold")
    )
    style.configure(
        "Muted.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=(font_family, 9)
    )
    style.configure(
        "Status.TLabel",
        background=COLORS["surface_alt"],
        foreground=COLORS["success"],
        font=(font_family, 10, "bold"),
        padding=(12, 7)
    )

    style.configure(
        "Card.TLabelframe",
        background=COLORS["surface"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        relief="solid",
        padding=12
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=(font_family, 11, "bold")
    )

    style.configure(
        "TEntry",
        fieldbackground="#ffffff",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(8, 6)
    )
    style.map("TEntry", bordercolor=[("focus", COLORS["primary"])])

    style.configure(
        "TCombobox",
        fieldbackground="#ffffff",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        arrowcolor=COLORS["muted"],
        padding=(8, 5)
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#ffffff")],
        bordercolor=[("focus", COLORS["primary"])]
    )

    style.configure(
        "TButton",
        background="#ffffff",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        focusthickness=0,
        padding=(13, 8)
    )
    style.map(
        "TButton",
        background=[("active", "#f1f5f9"), ("pressed", "#e2e8f0"), ("disabled", "#f1f5f9")],
        foreground=[("disabled", "#98a2b3")]
    )
    style.configure(
        "Accent.TButton",
        background=COLORS["primary"],
        foreground="#ffffff",
        bordercolor=COLORS["primary"],
        padding=(16, 8)
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLORS["primary_hover"]), ("pressed", COLORS["primary_pressed"]), ("disabled", "#93c5fd")],
        foreground=[("disabled", "#eff6ff")]
    )
    style.configure(
        "Danger.TButton",
        background="#ffffff",
        foreground=COLORS["danger"],
        bordercolor="#fecaca",
        padding=(13, 8)
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#fef2f2"), ("pressed", "#fee2e2")],
        foreground=[("active", COLORS["danger_hover"])]
    )

    style.configure(
        "TNotebook",
        background=COLORS["bg"],
        borderwidth=0,
        tabmargins=(0, 6, 0, 0)
    )
    style.configure(
        "TNotebook.Tab",
        background="#e8eef7",
        foreground=COLORS["muted"],
        padding=(18, 10),
        font=(font_family, 10, "bold")
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["surface"]), ("active", "#f8fafc")],
        foreground=[("selected", COLORS["primary"]), ("active", COLORS["text"])]
    )

    style.configure(
        "Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        rowheight=30,
        font=(font_family, 9)
    )
    style.configure(
        "Treeview.Heading",
        background="#e8eef7",
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        font=(font_family, 9, "bold"),
        padding=(8, 8)
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["selected"])],
        foreground=[("selected", COLORS["text"])]
    )


# --------------------------------------------------
# Credentials Helper
# --------------------------------------------------

def load_credentials(file_path="credentials.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"{file_path} was not found. Create it in the same folder as this script."
        )

    with open(file_path, "r", encoding="utf-8") as file:
        credentials = json.load(file)

    required_fields = [
        "imap_server",
        "imap_port",
        "mailbox",
        "login_email",
        "password"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in credentials or credentials[field] in (None, "")
    ]

    if missing_fields:
        raise ValueError(
            "Missing fields in credentials.json: " + ", ".join(missing_fields)
        )

    return credentials


# --------------------------------------------------
# Email / IMAP Helpers
# --------------------------------------------------

def decode_mime_header(value):
    if not value:
        return ""

    decoded_parts = decode_header(value)
    result = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += part

    return result


def html_to_text(value):
    if not value:
        return ""

    value = re.sub(r"(?is)<script.*?>.*?</script>", " ", value)
    value = re.sub(r"(?is)<style.*?>.*?</style>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p>", "\n", value)
    value = re.sub(r"(?i)</div>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(value)


def normalize_text(value):
    value = html.unescape(value or "")
    value = value.replace("\xa0", " ")
    value = value.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_email_body(message):
    plain_body = ""
    html_body = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition.lower():
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            charset = part.get_content_charset() or "utf-8"
            decoded_payload = payload.decode(charset, errors="ignore")

            if content_type == "text/plain":
                plain_body += decoded_payload + "\n"
            elif content_type == "text/html":
                html_body += html_to_text(decoded_payload) + "\n"
    else:
        payload = message.get_payload(decode=True)
        if payload:
            charset = message.get_content_charset() or "utf-8"
            decoded_payload = payload.decode(charset, errors="ignore")

            if message.get_content_type() == "text/html":
                html_body += html_to_text(decoded_payload)
            else:
                plain_body += decoded_payload

    return plain_body.strip() or html_body.strip()


def make_body_preview(body, max_length=500):
    return normalize_text(body)[:max_length]


def extract_attachments(message):
    attachment_names = []

    for part in message.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        filename = part.get_filename()

        if filename:
            filename = decode_mime_header(filename)

        if "attachment" in content_disposition.lower() or filename:
            if filename:
                attachment_names.append(filename)
            else:
                attachment_names.append("Unnamed attachment")

    return attachment_names


def connect_imap(imap_server, imap_port, login_email, password):
    mail = imaplib.IMAP4_SSL(imap_server, int(imap_port))
    mail.login(login_email, password)
    return mail


def quote_imap_value(value):
    value = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{value}"'


def build_imap_search_criteria(from_email, to_email, subject, start_date, end_date):
    """
    IMAP date format is DD-Mon-YYYY.
    SINCE is inclusive.
    BEFORE is exclusive, so we use end_date + 1 day.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

    criteria = [
        f'SINCE "{start.strftime("%d-%b-%Y")}"',
        f'BEFORE "{end.strftime("%d-%b-%Y")}"'
    ]

    if from_email.strip():
        criteria.append(f'FROM {quote_imap_value(from_email.strip())}')

    if to_email.strip():
        criteria.append(f'TO {quote_imap_value(to_email.strip())}')

    if subject.strip():
        criteria.append(f'SUBJECT {quote_imap_value(subject.strip())}')

    return "(" + " ".join(criteria) + ")"


def parse_email_date(email_date_header):
    try:
        email_datetime = parsedate_to_datetime(email_date_header)
        return email_datetime.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return email_date_header or ""


# --------------------------------------------------
# Bank Transaction Parser
# --------------------------------------------------

def clean_bank_source(source):
    source = source or ""
    source = normalize_text(source)

    source = re.sub(r"^Dear\s+Customer,?\s*", "", source, flags=re.IGNORECASE).strip()
    source = re.sub(r"\s+purchase$", "", source, flags=re.IGNORECASE).strip()
    source = re.sub(r"\s+transaction$", "", source, flags=re.IGNORECASE).strip()
    source = source.strip(" .:-")

    return source


def parse_transaction_alert(body):
    text = normalize_text(body)

    if not text:
        return None

    patterns = [
        re.compile(
            r"(?:Dear\s+Customer,?\s*)?"
            r"(?P<description>.*?)\s+from\s+"
            r"(?P<card>[0-9Xx*\s]{6,30})\s+"
            r"AED\s*(?P<amount>[0-9,]+(?:\.\d{1,2})?)",
            re.IGNORECASE
        ),
        re.compile(
            r"(?:Dear\s+Customer,?\s*)?"
            r"(?P<description>.*?)\s+AED\s*(?P<amount>[0-9,]+(?:\.\d{1,2})?)",
            re.IGNORECASE
        )
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue

        source = clean_bank_source(match.group("description"))
        amount_raw = match.group("amount").replace(",", "")

        if not source:
            continue

        lower_source = source.lower()
        if lower_source in {"your current balance is", "current balance is"}:
            continue

        try:
            amount = f"AED {float(amount_raw):.2f}"
        except ValueError:
            amount = f"AED {amount_raw}"

        return {
            "source": source,
            "amount": amount
        }

    return None


# --------------------------------------------------
# Fetch Logic
# --------------------------------------------------

def email_matches_keyword(subject, sender, recipient, cc, body, keyword):
    keyword = keyword.strip().lower()

    if not keyword:
        return True

    searchable_text = " ".join([
        subject or "",
        sender or "",
        recipient or "",
        cc or "",
        body or ""
    ]).lower()

    return keyword in searchable_text


def fetch_general_emails_imap(
    credentials,
    from_email,
    to_email,
    subject,
    keyword,
    start_date,
    end_date,
    progress_callback=None
):
    mail = None

    try:
        if progress_callback:
            progress_callback("Connecting to IMAP server...")

        mail = connect_imap(
            credentials["imap_server"],
            credentials["imap_port"],
            credentials["login_email"],
            credentials["password"]
        )

        mailbox = str(credentials.get("mailbox", "INBOX")).strip() or "INBOX"

        if progress_callback:
            progress_callback(f"Opening mailbox: {mailbox}")

        status, _ = mail.select(mailbox)
        if status != "OK":
            raise RuntimeError(f"Could not open mailbox: {mailbox}")

        criteria = build_imap_search_criteria(
            from_email,
            to_email,
            subject,
            start_date,
            end_date
        )

        if progress_callback:
            progress_callback(f"Searching with criteria: {criteria}")

        status, data = mail.search(None, criteria)
        if status != "OK":
            raise RuntimeError("IMAP search failed.")

        message_ids = data[0].split()

        if progress_callback:
            progress_callback(f"Found {len(message_ids)} emails. Reading messages...")

        results = []

        for index, message_id in enumerate(message_ids, start=1):
            if progress_callback:
                progress_callback(f"Reading email {index} of {len(message_ids)}...")

            status, msg_data = mail.fetch(message_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            message = email.message_from_bytes(raw_email)

            email_subject = decode_mime_header(message.get("Subject", ""))
            sender = decode_mime_header(message.get("From", ""))
            recipient = decode_mime_header(message.get("To", ""))
            cc = decode_mime_header(message.get("Cc", ""))
            reply_to = decode_mime_header(message.get("Reply-To", ""))
            email_date_header = message.get("Date", "")
            message_id_header = message.get("Message-ID", "")

            body = extract_email_body(message)

            if not email_matches_keyword(email_subject, sender, recipient, cc, body, keyword):
                continue

            attachment_names = extract_attachments(message)

            results.append({
                "_selected": True,
                "email_date": parse_email_date(email_date_header),
                "from": sender,
                "to": recipient,
                "cc": cc,
                "reply_to": reply_to,
                "subject": email_subject,
                "body_preview": make_body_preview(body),
                "has_attachments": "Yes" if attachment_names else "No",
                "attachment_count": len(attachment_names),
                "attachment_names": "; ".join(attachment_names),
                "message_id": message_id_header
            })

        return results

    finally:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass


def fetch_bank_transactions_imap(
    credentials,
    from_email,
    subject,
    start_date,
    end_date,
    progress_callback=None
):
    mail = None

    try:
        if progress_callback:
            progress_callback("Connecting to IMAP server...")

        mail = connect_imap(
            credentials["imap_server"],
            credentials["imap_port"],
            credentials["login_email"],
            credentials["password"]
        )

        mailbox = str(credentials.get("mailbox", "INBOX")).strip() or "INBOX"

        if progress_callback:
            progress_callback(f"Opening mailbox: {mailbox}")

        status, _ = mail.select(mailbox)
        if status != "OK":
            raise RuntimeError(f"Could not open mailbox: {mailbox}")

        criteria = build_imap_search_criteria(
            from_email,
            "",
            subject,
            start_date,
            end_date
        )

        if progress_callback:
            progress_callback(f"Searching with criteria: {criteria}")

        status, data = mail.search(None, criteria)
        if status != "OK":
            raise RuntimeError("IMAP search failed.")

        message_ids = data[0].split()

        if progress_callback:
            progress_callback(f"Found {len(message_ids)} emails. Reading messages...")

        results = []

        for index, message_id in enumerate(message_ids, start=1):
            if progress_callback:
                progress_callback(f"Reading email {index} of {len(message_ids)}...")

            status, msg_data = mail.fetch(message_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            message = email.message_from_bytes(raw_email)

            email_subject = decode_mime_header(message.get("Subject", ""))
            sender = decode_mime_header(message.get("From", ""))
            email_date_header = message.get("Date", "")

            body = extract_email_body(message)
            parsed = parse_transaction_alert(body)
            body_preview = make_body_preview(body)

            if not parsed:
                results.append({
                    "_selected": False,
                    "email_date": parse_email_date(email_date_header),
                    "source": "NOT PARSED",
                    "amount": "NOT PARSED",
                    "status": "Failed to parse",
                    "subject": email_subject,
                    "from": sender,
                    "body_preview": body_preview
                })
                continue

            results.append({
                "_selected": True,
                "email_date": parse_email_date(email_date_header),
                "source": parsed["source"],
                "amount": parsed["amount"],
                "status": "Parsed",
                "subject": email_subject,
                "from": sender,
                "body_preview": body_preview
            })

        return results

    finally:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass


# --------------------------------------------------
# Reusable Results Tab
# --------------------------------------------------

class ResultsTab(ttk.Frame):
    def __init__(self, parent, app, tab_type):
        super().__init__(parent, padding=16, style="Modern.TFrame")
        self.app = app
        self.tab_type = tab_type
        self.results = []
        self.visible_indexes = []
        self.tree_item_to_index = {}

        if tab_type == "general":
            self.columns = (
                "select",
                "email_date",
                "from",
                "to",
                "cc",
                "reply_to",
                "subject",
                "body_preview",
                "has_attachments",
                "attachment_count",
                "attachment_names",
                "message_id"
            )
            self.export_filename = "general_emails_export.csv"
            self.export_fieldnames = [
                "email_date",
                "from",
                "to",
                "cc",
                "reply_to",
                "subject",
                "body_preview",
                "has_attachments",
                "attachment_count",
                "attachment_names",
                "message_id"
            ]
        else:
            self.columns = (
                "select",
                "email_date",
                "source",
                "amount",
                "status",
                "subject",
                "from",
                "body_preview"
            )
            self.export_filename = "bank_transactions_export.csv"
            self.export_fieldnames = [
                "email_date",
                "source",
                "amount",
                "status",
                "subject",
                "from",
                "body_preview"
            ]

        self.create_widgets()

    def create_widgets(self):
        filters_frame = ttk.LabelFrame(self, text="Email Search Filters", padding=14, style="Card.TLabelframe")
        filters_frame.pack(fill=tk.X, pady=(0, 12))

        if self.tab_type == "general":
            ttk.Label(filters_frame, text="From Contains:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
            self.from_email_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.from_email_var, width=34).grid(row=0, column=1, sticky="w", pady=4)

            ttk.Label(filters_frame, text="To Contains:").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=4)
            self.to_email_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.to_email_var, width=34).grid(row=0, column=3, sticky="w", pady=4)

            ttk.Label(filters_frame, text="Subject Contains:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
            self.subject_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.subject_var, width=34).grid(row=1, column=1, sticky="w", pady=4)

            ttk.Label(filters_frame, text="Keyword Anywhere:").grid(row=1, column=2, sticky="w", padx=(20, 8), pady=4)
            self.keyword_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.keyword_var, width=34).grid(row=1, column=3, sticky="w", pady=4)
        else:
            ttk.Label(filters_frame, text="From Email:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
            self.from_email_var = tk.StringVar(value="alerts@nbf.ae")
            ttk.Entry(filters_frame, textvariable=self.from_email_var, width=34).grid(row=0, column=1, sticky="w", pady=4)

            ttk.Label(filters_frame, text="Subject:").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=4)
            self.subject_var = tk.StringVar(value="Transaction Alert")
            ttk.Entry(filters_frame, textvariable=self.subject_var, width=34).grid(row=0, column=3, sticky="w", pady=4)

            self.to_email_var = tk.StringVar(value="")
            self.keyword_var = tk.StringVar(value="")

        ttk.Label(filters_frame, text="Start Date YYYY-MM-DD:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.start_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-01"))
        ttk.Entry(filters_frame, textvariable=self.start_date_var, width=20).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(filters_frame, text="End Date YYYY-MM-DD:").grid(row=2, column=2, sticky="w", padx=(20, 8), pady=4)
        self.end_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        ttk.Entry(filters_frame, textvariable=self.end_date_var, width=20).grid(row=2, column=3, sticky="w", pady=4)

        buttons_frame = ttk.Frame(self, style="Toolbar.TFrame")
        buttons_frame.pack(fill=tk.X, pady=(0, 12))

        self.run_button = ttk.Button(
            buttons_frame,
            text="Run Extraction",
            command=self.run_extraction,
            style="Accent.TButton"
        )
        self.run_button.pack(side=tk.LEFT)

        self.export_selected_button = ttk.Button(
            buttons_frame,
            text="Export Selected CSV",
            command=self.export_selected_csv,
            state=tk.DISABLED
        )
        self.export_selected_button.pack(side=tk.LEFT, padx=(8, 0))

        self.export_visible_button = ttk.Button(
            buttons_frame,
            text="Export Visible CSV",
            command=self.export_visible_csv,
            state=tk.DISABLED
        )
        self.export_visible_button.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(buttons_frame, text="Select All Visible", command=self.select_all_visible).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons_frame, text="Unselect All Visible", command=self.unselect_all_visible).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            buttons_frame,
            text="Clear Results",
            command=self.clear_results,
            style="Danger.TButton"
        ).pack(side=tk.LEFT, padx=(8, 0))

        result_filter_frame = ttk.LabelFrame(self, text="Results Search / Filters", padding=14, style="Card.TLabelframe")
        result_filter_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(result_filter_frame, text="Search in Results:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.result_search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(result_filter_frame, textvariable=self.result_search_var, width=42)
        search_entry.grid(row=0, column=1, sticky="w", pady=4)
        search_entry.bind("<KeyRelease>", lambda event: self.apply_result_filter())

        ttk.Label(result_filter_frame, text="Column:").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=4)
        self.result_column_var = tk.StringVar(value="All Columns")
        column_values = ["All Columns"] + [col for col in self.export_fieldnames]
        column_combo = ttk.Combobox(
            result_filter_frame,
            textvariable=self.result_column_var,
            values=column_values,
            width=24,
            state="readonly"
        )
        column_combo.grid(row=0, column=3, sticky="w", pady=4)
        column_combo.bind("<<ComboboxSelected>>", lambda event: self.apply_result_filter())

        if self.tab_type == "bank":
            ttk.Label(result_filter_frame, text="Status:").grid(row=0, column=4, sticky="w", padx=(20, 8), pady=4)
            self.status_filter_var = tk.StringVar(value="All")
            status_combo = ttk.Combobox(
                result_filter_frame,
                textvariable=self.status_filter_var,
                values=["All", "Parsed", "Failed to parse"],
                width=18,
                state="readonly"
            )
            status_combo.grid(row=0, column=5, sticky="w", pady=4)
            status_combo.bind("<<ComboboxSelected>>", lambda event: self.apply_result_filter())
        else:
            ttk.Label(result_filter_frame, text="Attachments:").grid(row=0, column=4, sticky="w", padx=(20, 8), pady=4)
            self.attachment_filter_var = tk.StringVar(value="All")
            attach_combo = ttk.Combobox(
                result_filter_frame,
                textvariable=self.attachment_filter_var,
                values=["All", "With Attachments", "Without Attachments"],
                width=20,
                state="readonly"
            )
            attach_combo.grid(row=0, column=5, sticky="w", pady=4)
            attach_combo.bind("<<ComboboxSelected>>", lambda event: self.apply_result_filter())

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(
            self,
            textvariable=self.status_var,
            style="Status.TLabel"
        ).pack(fill=tk.X, pady=(0, 10))

        table_frame = ttk.Frame(self, style="Surface.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings")
        self.tree.tag_configure("odd", background=COLORS["surface"])
        self.tree.tag_configure("even", background=COLORS["row_alt"])

        headings = {
            "select": "Select",
            "email_date": "Email Date",
            "from": "From",
            "to": "To",
            "cc": "Cc",
            "reply_to": "Reply-To",
            "subject": "Subject",
            "body_preview": "Body Preview",
            "has_attachments": "Has Attachments",
            "attachment_count": "Attachment Count",
            "attachment_names": "Attachment Names",
            "message_id": "Message-ID",
            "source": "Source",
            "amount": "Amount",
            "status": "Status"
        }

        widths = {
            "select": 70,
            "email_date": 155,
            "from": 300,
            "to": 300,
            "cc": 220,
            "reply_to": 220,
            "subject": 280,
            "body_preview": 480,
            "has_attachments": 120,
            "attachment_count": 120,
            "attachment_names": 280,
            "message_id": 260,
            "source": 240,
            "amount": 110,
            "status": 120
        }

        for column in self.columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")

        self.tree.column("select", width=70, anchor="center")
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<space>", self.toggle_selected_rows)

        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def validate_dates(self):
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Dates must be in YYYY-MM-DD format.")
            return None

        if start > end:
            messagebox.showerror("Validation Error", "Start Date cannot be after End Date.")
            return None

        return start_date, end_date

    def run_extraction(self):
        if not self.app.credentials:
            messagebox.showerror("Credentials Error", "credentials.json is not loaded.")
            return

        date_values = self.validate_dates()
        if not date_values:
            return

        start_date, end_date = date_values

        self.clear_results()
        self.run_button.config(state=tk.DISABLED)
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Running...")

        if self.tab_type == "general":
            args = (
                self.app.credentials,
                self.from_email_var.get().strip(),
                self.to_email_var.get().strip(),
                self.subject_var.get().strip(),
                self.keyword_var.get().strip(),
                start_date,
                end_date,
            )
            target = self.run_general_worker
        else:
            args = (
                self.app.credentials,
                self.from_email_var.get().strip(),
                self.subject_var.get().strip(),
                start_date,
                end_date,
            )
            target = self.run_bank_worker

        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def run_general_worker(
        self,
        credentials,
        from_email,
        to_email,
        subject,
        keyword,
        start_date,
        end_date
    ):
        try:
            results = fetch_general_emails_imap(
                credentials,
                from_email,
                to_email,
                subject,
                keyword,
                start_date,
                end_date,
                progress_callback=self.set_status_threadsafe
            )
            self.after(0, lambda: self.load_results(results))
        except Exception as exc:
            self.after(0, lambda: self.show_error(str(exc)))

    def run_bank_worker(
        self,
        credentials,
        from_email,
        subject,
        start_date,
        end_date
    ):
        try:
            results = fetch_bank_transactions_imap(
                credentials,
                from_email,
                subject,
                start_date,
                end_date,
                progress_callback=self.set_status_threadsafe
            )
            self.after(0, lambda: self.load_results(results))
        except Exception as exc:
            self.after(0, lambda: self.show_error(str(exc)))

    def set_status_threadsafe(self, message):
        self.after(0, lambda: self.status_var.set(message))

    def row_matches_result_filter(self, row):
        search_text = self.result_search_var.get().strip().lower()
        selected_column = self.result_column_var.get()

        if self.tab_type == "bank":
            status_filter = self.status_filter_var.get()
            if status_filter != "All" and row.get("status") != status_filter:
                return False
        else:
            attachment_filter = self.attachment_filter_var.get()
            if attachment_filter == "With Attachments" and row.get("has_attachments") != "Yes":
                return False
            if attachment_filter == "Without Attachments" and row.get("has_attachments") != "No":
                return False

        if not search_text:
            return True

        if selected_column == "All Columns":
            searchable = " ".join(str(row.get(field, "")) for field in self.export_fieldnames).lower()
        else:
            searchable = str(row.get(selected_column, "")).lower()

        return search_text in searchable

    def apply_result_filter(self):
        self.refresh_tree()

    def load_results(self, results):
        self.results = results
        self.refresh_tree()
        self.run_button.config(state=tk.NORMAL)

        if results:
            self.export_selected_button.config(state=tk.NORMAL)
            self.export_visible_button.config(state=tk.NORMAL)

        if self.tab_type == "bank":
            parsed_count = sum(1 for item in results if item.get("status") == "Parsed")
            failed_count = len(results) - parsed_count
            selected_count = self.get_selected_count()
            self.status_var.set(
                f"Completed. Total: {len(results)} | Parsed: {parsed_count} | Failed: {failed_count} | Selected: {selected_count}"
            )
        else:
            selected_count = self.get_selected_count()
            self.status_var.set(
                f"Completed. Total emails: {len(results)} | Selected: {selected_count}"
            )

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_item_to_index = {}
        self.visible_indexes = []

        for index, item in enumerate(self.results):
            if not self.row_matches_result_filter(item):
                continue

            self.visible_indexes.append(index)
            select_value = "[x]" if item.get("_selected") else "[ ]"

            values = [select_value]
            for column in self.columns[1:]:
                values.append(item.get(column, ""))

            row_tag = "even" if len(self.visible_indexes) % 2 == 0 else "odd"
            tree_item = self.tree.insert("", tk.END, values=tuple(values), tags=(row_tag,))
            self.tree_item_to_index[tree_item] = index

        self.update_status_selection_counts()

    def update_status_selection_counts(self):
        selected_count = self.get_selected_count()
        visible_count = len(self.visible_indexes)
        total_count = len(self.results)

        if total_count == 0:
            return

        current_text = self.status_var.get().split(" | Visible:")[0]
        current_text = current_text.split(" | Selected:")[0]
        self.status_var.set(
            f"{current_text} | Visible: {visible_count} | Selected: {selected_count}"
        )

    def get_selected_count(self):
        return sum(1 for row in self.results if row.get("_selected"))

    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)

        if column == "#1" and item_id:
            index = self.tree_item_to_index.get(item_id)
            if index is not None:
                self.results[index]["_selected"] = not self.results[index].get("_selected", False)
                self.refresh_tree()

    def toggle_selected_rows(self, event=None):
        selected_items = self.tree.selection()
        for item_id in selected_items:
            index = self.tree_item_to_index.get(item_id)
            if index is not None:
                self.results[index]["_selected"] = not self.results[index].get("_selected", False)
        self.refresh_tree()

    def select_all_visible(self):
        for index in self.visible_indexes:
            self.results[index]["_selected"] = True
        self.refresh_tree()

    def unselect_all_visible(self):
        for index in self.visible_indexes:
            self.results[index]["_selected"] = False
        self.refresh_tree()

    def export_selected_csv(self):
        rows = [row for row in self.results if row.get("_selected")]
        if not rows:
            messagebox.showinfo("No Rows Selected", "Please select at least one row to export.")
            return
        self.export_rows_to_csv(rows, self.export_filename)

    def export_visible_csv(self):
        rows = [self.results[index] for index in self.visible_indexes]
        if not rows:
            messagebox.showinfo("No Visible Rows", "There are no visible rows to export.")
            return
        self.export_rows_to_csv(rows, self.export_filename)

    def export_rows_to_csv(self, rows, default_filename):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename
        )

        if not file_path:
            return

        cleaned_rows = []
        for row in rows:
            cleaned_rows.append({field: row.get(field, "") for field in self.export_fieldnames})

        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.export_fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)

        messagebox.showinfo("Export Completed", f"CSV exported successfully:\n{file_path}")

    def clear_results(self):
        self.results = []
        self.visible_indexes = []
        self.tree_item_to_index = {}
        self.tree.delete(*self.tree.get_children())
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Ready.")

    def show_error(self, error_message):
        self.run_button.config(state=tk.NORMAL)
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Error occurred.")
        messagebox.showerror("Error", error_message)


# --------------------------------------------------
# Main Application
# --------------------------------------------------

class EmailExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Extractor")
        self.root.geometry("1500x820")
        self.root.minsize(1200, 700)

        self.credentials = {}
        self.icon_image = None

        configure_theme(self.root)
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
        main_frame = ttk.Frame(self.root, padding=16, style="Modern.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame, padding=(18, 16), style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 14))

        ttk.Label(
            header_frame,
            text="Email Extractor",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header_frame,
            text="General email search and bank transaction exports in one workspace",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(4, 0))

        login_frame = ttk.LabelFrame(
            main_frame,
            text="Login Loaded From credentials.json",
            padding=14,
            style="Card.TLabelframe"
        )
        login_frame.pack(fill=tk.X, pady=(0, 14))

        ttk.Label(login_frame, text="IMAP Server:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.imap_server_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.imap_server_var, width=28, state="readonly").grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(login_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=(20, 8), pady=4)
        self.imap_port_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.imap_port_var, width=8, state="readonly").grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(login_frame, text="Mailbox:").grid(row=0, column=4, sticky="w", padx=(20, 8), pady=4)
        self.mailbox_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.mailbox_var, width=20, state="readonly").grid(row=0, column=5, sticky="w", pady=4)

        ttk.Label(login_frame, text="Login Email:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.login_email_var = tk.StringVar(value="")
        ttk.Entry(login_frame, textvariable=self.login_email_var, width=42, state="readonly").grid(row=1, column=1, columnspan=2, sticky="w", pady=4)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=3, sticky="w", padx=(20, 8), pady=4)
        self.password_display_var = tk.StringVar(value="Loaded from file")
        ttk.Entry(login_frame, textvariable=self.password_display_var, width=35, show="*", state="readonly").grid(row=1, column=4, columnspan=2, sticky="w", pady=4)

        self.credentials_status_var = tk.StringVar(value="Loading credentials...")
        ttk.Label(login_frame, textvariable=self.credentials_status_var).grid(row=2, column=0, columnspan=6, sticky="w", pady=(6, 0))

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.general_tab = ResultsTab(self.notebook, self, "general")
        self.bank_tab = ResultsTab(self.notebook, self, "bank")

        self.notebook.add(self.general_tab, text="General")
        self.notebook.add(self.bank_tab, text="Bank Transactions")

    def load_credentials_to_screen(self):
        try:
            self.credentials = load_credentials("credentials.json")

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


if __name__ == "__main__":
    configure_windows_taskbar_icon()
    root = tk.Tk()
    app = EmailExtractorApp(root)
    root.mainloop()
