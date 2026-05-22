import csv
import re
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from ..config import COLORS
from ..extractors import BankTransactionExtractor, GeneralEmailExtractor


class ResultsTab(ttk.Frame):
    def __init__(self, parent, app, tab_type):
        super().__init__(parent, padding=12, style="Modern.TFrame")
        self.app = app
        self.tab_type = tab_type
        self.results = []
        self.visible_indexes = []
        self.tree_item_to_index = {}
        self.sort_column = None
        self.sort_reverse = False
        self.column_headings = {}

        if tab_type == "general":
            self.columns = (
                "select", "email_date", "from", "to", "cc", "reply_to", "subject",
                "body_preview", "has_attachments", "attachment_count", "attachment_names", "message_id",
            )
            self.export_filename = "general_emails_export.csv"
            self.export_fieldnames = [
                "email_date", "from", "to", "cc", "reply_to", "subject", "body_preview",
                "has_attachments", "attachment_count", "attachment_names", "message_id",
            ]
        else:
            self.columns = (
                "select", "email_date", "source", "amount", "status", "subject", "from", "body_preview",
            )
            self.export_filename = "bank_transactions_export.csv"
            self.export_fieldnames = [
                "email_date", "source", "amount", "status", "subject", "from", "body_preview",
            ]

        self.create_widgets()

    def create_widgets(self):
        self.rowconfigure(4, weight=1, minsize=230)
        self.columnconfigure(0, weight=1)

        filters_frame = ttk.LabelFrame(self, text="Email Search Filters", padding=10, style="Card.TLabelframe")
        filters_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._create_search_filters(filters_frame)

        buttons_frame = ttk.Frame(self, style="Toolbar.TFrame")
        buttons_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._create_action_buttons(buttons_frame)

        result_filter_frame = ttk.LabelFrame(self, text="Results Search / Filters", padding=10, style="Card.TLabelframe")
        result_filter_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self._create_result_filters(result_filter_frame)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").grid(
            row=3, column=0, sticky="ew", pady=(0, 8)
        )

        self._create_results_table()

    def _create_search_filters(self, filters_frame):
        if self.tab_type == "general":
            ttk.Label(filters_frame, text="From Contains:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
            self.from_email_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.from_email_var, width=28).grid(row=0, column=1, sticky="w", pady=3)

            ttk.Label(filters_frame, text="To Contains:").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=3)
            self.to_email_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.to_email_var, width=28).grid(row=0, column=3, sticky="w", pady=3)

            ttk.Label(filters_frame, text="Subject Contains:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
            self.subject_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.subject_var, width=28).grid(row=1, column=1, sticky="w", pady=3)

            ttk.Label(filters_frame, text="Keyword Anywhere:").grid(row=1, column=2, sticky="w", padx=(18, 8), pady=3)
            self.keyword_var = tk.StringVar(value="")
            ttk.Entry(filters_frame, textvariable=self.keyword_var, width=28).grid(row=1, column=3, sticky="w", pady=3)
        else:
            ttk.Label(filters_frame, text="From Email:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
            self.from_email_var = tk.StringVar(value="alerts@nbf.ae")
            ttk.Entry(filters_frame, textvariable=self.from_email_var, width=28).grid(row=0, column=1, sticky="w", pady=3)

            ttk.Label(filters_frame, text="Subject:").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=3)
            self.subject_var = tk.StringVar(value="Transaction Alert")
            ttk.Entry(filters_frame, textvariable=self.subject_var, width=28).grid(row=0, column=3, sticky="w", pady=3)

            self.to_email_var = tk.StringVar(value="")
            self.keyword_var = tk.StringVar(value="")

        ttk.Label(filters_frame, text="Start Date YYYY-MM-DD:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
        self.start_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-01"))
        ttk.Entry(filters_frame, textvariable=self.start_date_var, width=18).grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(filters_frame, text="End Date YYYY-MM-DD:").grid(row=2, column=2, sticky="w", padx=(18, 8), pady=3)
        self.end_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        ttk.Entry(filters_frame, textvariable=self.end_date_var, width=18).grid(row=2, column=3, sticky="w", pady=3)

    def _create_action_buttons(self, buttons_frame):
        self.run_button = ttk.Button(
            buttons_frame, text="Run Extraction", command=self.run_extraction, style="Accent.TButton"
        )
        self.run_button.pack(side=tk.LEFT)

        self.export_selected_button = ttk.Button(
            buttons_frame, text="Export Selected CSV", command=self.export_selected_csv, state=tk.DISABLED
        )
        self.export_selected_button.pack(side=tk.LEFT, padx=(8, 0))

        self.export_visible_button = ttk.Button(
            buttons_frame, text="Export Visible CSV", command=self.export_visible_csv, state=tk.DISABLED
        )
        self.export_visible_button.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(buttons_frame, text="Select All Visible", command=self.select_all_visible).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons_frame, text="Unselect All Visible", command=self.unselect_all_visible).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            buttons_frame, text="Clear Results", command=self.clear_results, style="Danger.TButton"
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _create_result_filters(self, result_filter_frame):
        ttk.Label(result_filter_frame, text="Search in Results:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        self.result_search_var = tk.StringVar(value="")
        search_entry = ttk.Entry(result_filter_frame, textvariable=self.result_search_var, width=34)
        search_entry.grid(row=0, column=1, sticky="w", pady=3)
        search_entry.bind("<KeyRelease>", lambda event: self.apply_result_filter())

        ttk.Label(result_filter_frame, text="Column:").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=3)
        self.result_column_var = tk.StringVar(value="All Columns")
        column_combo = ttk.Combobox(
            result_filter_frame,
            textvariable=self.result_column_var,
            values=["All Columns"] + [col for col in self.export_fieldnames],
            width=22,
            state="readonly",
        )
        column_combo.grid(row=0, column=3, sticky="w", pady=3)
        column_combo.bind("<<ComboboxSelected>>", lambda event: self.apply_result_filter())

        if self.tab_type == "bank":
            ttk.Label(result_filter_frame, text="Status:").grid(row=0, column=4, sticky="w", padx=(18, 8), pady=3)
            self.status_filter_var = tk.StringVar(value="All")
            filter_combo = ttk.Combobox(
                result_filter_frame,
                textvariable=self.status_filter_var,
                values=["All", "Parsed", "Failed to parse"],
                width=16,
                state="readonly",
            )
        else:
            ttk.Label(result_filter_frame, text="Attachments:").grid(row=0, column=4, sticky="w", padx=(18, 8), pady=3)
            self.attachment_filter_var = tk.StringVar(value="All")
            filter_combo = ttk.Combobox(
                result_filter_frame,
                textvariable=self.attachment_filter_var,
                values=["All", "With Attachments", "Without Attachments"],
                width=18,
                state="readonly",
            )

        filter_combo.grid(row=0, column=5, sticky="w", pady=3)
        filter_combo.bind("<<ComboboxSelected>>", lambda event: self.apply_result_filter())

    def _create_results_table(self):
        table_frame = ttk.Frame(self, style="Surface.TFrame")
        table_frame.grid(row=4, column=0, sticky="nsew")

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", height=12)
        self.tree.tag_configure("odd", background=COLORS["surface"])
        self.tree.tag_configure("even", background=COLORS["row_alt"])

        self.column_headings = {
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
            "status": "Status",
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
            "status": 120,
        }

        for column in self.columns:
            self.tree.heading(
                column,
                text=self.column_headings[column],
                command=lambda selected_column=column: self.sort_by_column(selected_column),
            )
            self.tree.column(column, width=widths[column], anchor="w")

        self.tree.column("select", width=70, anchor="center")
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.show_selected_row_details)
        self.tree.bind("<space>", self.toggle_selected_rows)
        self.tree.bind("<MouseWheel>", self.on_tree_mousewheel)

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

        self.clear_results()
        self.run_button.config(state=tk.DISABLED)
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Running...")

        thread = threading.Thread(target=self.run_worker, args=date_values, daemon=True)
        thread.start()

    def run_worker(self, start_date, end_date):
        try:
            if self.tab_type == "general":
                extractor = GeneralEmailExtractor(self.app.credentials, self.set_status_threadsafe)
                results = extractor.extract(
                    self.from_email_var.get().strip(),
                    self.to_email_var.get().strip(),
                    self.subject_var.get().strip(),
                    self.keyword_var.get().strip(),
                    start_date,
                    end_date,
                )
            else:
                extractor = BankTransactionExtractor(self.app.credentials, self.set_status_threadsafe)
                results = extractor.extract(
                    self.from_email_var.get().strip(),
                    self.subject_var.get().strip(),
                    start_date,
                    end_date,
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

    def get_sort_value(self, row, column):
        if column == "select":
            return 1 if row.get("_selected") else 0

        value = row.get(column, "")

        if column == "email_date":
            try:
                return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.min

        if column == "amount":
            amount_text = re.sub(r"[^0-9.]", "", str(value))
            try:
                return float(amount_text)
            except ValueError:
                return -1

        if column == "attachment_count":
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        return str(value or "").casefold()

    def sort_by_column(self, column):
        if not self.results:
            return

        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        self.results.sort(key=lambda row: self.get_sort_value(row, column), reverse=self.sort_reverse)
        self.refresh_tree()
        self.update_column_headings()

    def update_column_headings(self):
        for column in self.columns:
            label = self.column_headings[column]
            if column == self.sort_column:
                label += " DESC" if self.sort_reverse else " ASC"
            self.tree.heading(
                column,
                text=label,
                command=lambda selected_column=column: self.sort_by_column(selected_column),
            )

    def load_results(self, results):
        self.results = results
        self.refresh_tree()
        self.run_button.config(state=tk.NORMAL)

        if results:
            self.export_selected_button.config(state=tk.NORMAL)
            self.export_visible_button.config(state=tk.NORMAL)

        selected_count = self.get_selected_count()
        if self.tab_type == "bank":
            parsed_count = sum(1 for item in results if item.get("status") == "Parsed")
            failed_count = len(results) - parsed_count
            self.status_var.set(
                f"Completed. Total: {len(results)} | Parsed: {parsed_count} | Failed: {failed_count} | Selected: {selected_count}"
            )
        else:
            self.status_var.set(f"Completed. Total emails: {len(results)} | Selected: {selected_count}")

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_item_to_index = {}
        self.visible_indexes = []

        for index, item in enumerate(self.results):
            if not self.row_matches_result_filter(item):
                continue

            self.visible_indexes.append(index)
            values = ["[x]" if item.get("_selected") else "[ ]"]
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
        self.status_var.set(f"{current_text} | Visible: {visible_count} | Selected: {selected_count}")

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

    def on_tree_mousewheel(self, event):
        self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_selected_row_details(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            selected_items = self.tree.selection()
            item_id = selected_items[0] if selected_items else ""

        index = self.tree_item_to_index.get(item_id)
        if index is not None:
            self.show_row_details_window(self.results[index])

    def show_row_details_window(self, row):
        window = tk.Toplevel(self)
        window.title("Email Details")
        window.geometry("900x700")
        window.minsize(720, 520)
        window.configure(bg=COLORS["bg"])
        window.transient(self.winfo_toplevel())

        container = ttk.Frame(window, padding=18, style="Modern.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container, padding=(18, 14), style="Header.TFrame")
        header.pack(fill=tk.X, pady=(0, 12))

        title = row.get("subject") or row.get("source") or "Email Details"
        ttk.Label(header, text=str(title)[:110], style="Title.TLabel").pack(anchor="w")

        subtitle_parts = [str(row.get("email_date", "")).strip(), str(row.get("from", "")).strip()]
        subtitle = "  |  ".join(part for part in subtitle_parts if part)
        ttk.Label(header, text=subtitle or "Email row details", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        self._create_details_metadata(container, row)
        self._create_details_body(container, row)

        button_frame = ttk.Frame(container, style="Toolbar.TFrame")
        button_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(button_frame, text="Close", command=window.destroy, style="Accent.TButton").pack(side=tk.RIGHT)

        window.grab_set()
        window.focus_set()

    def _create_details_metadata(self, container, row):
        message_card = ttk.LabelFrame(container, text="Email Message", padding=14, style="Card.TLabelframe")
        message_card.pack(fill=tk.X, pady=(0, 12))
        message_card.columnconfigure(1, weight=1)

        meta_rows = [
            ("From", row.get("from", "")),
            ("To", row.get("to", "")),
            ("Cc", row.get("cc", "")),
            ("Reply-To", row.get("reply_to", "")),
            ("Date", row.get("email_date", "")),
        ]

        meta_index = 0
        for label, value in meta_rows:
            if not value:
                continue
            ttk.Label(message_card, text=f"{label}:", style="Muted.TLabel").grid(
                row=meta_index, column=0, sticky="nw", padx=(0, 10), pady=3
            )
            tk.Label(
                message_card,
                text=str(value),
                bg=COLORS["surface"],
                fg=COLORS["text"],
                anchor="w",
                justify=tk.LEFT,
                wraplength=720,
                font=("Segoe UI", 10),
            ).grid(row=meta_index, column=1, sticky="ew", pady=3)
            meta_index += 1

        chip_frame = ttk.Frame(message_card, style="Surface.TFrame")
        chip_frame.grid(row=meta_index, column=0, columnspan=2, sticky="w", pady=(10, 0))

        if self.tab_type == "bank":
            chip_values = [("Source", row.get("source", "")), ("Amount", row.get("amount", "")), ("Status", row.get("status", ""))]
        else:
            chip_values = [("Attachments", row.get("has_attachments", "")), ("Count", row.get("attachment_count", ""))]

        for label, value in chip_values:
            if not value:
                continue
            tk.Label(
                chip_frame,
                text=f"{label}: {value}",
                bg=COLORS["surface_alt"],
                fg=COLORS["text"],
                padx=10,
                pady=5,
                font=("Segoe UI", 9, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 8))

    def _create_details_body(self, container, row):
        body_frame = ttk.LabelFrame(container, text="Message Preview", padding=12, style="Card.TLabelframe")
        body_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        body_frame.rowconfigure(0, weight=1)
        body_frame.columnconfigure(0, weight=1)

        body_text = tk.Text(
            body_frame,
            wrap="word",
            bg=COLORS["surface"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            font=("Segoe UI", 10),
            height=10,
        )
        body_scroll_y = ttk.Scrollbar(body_frame, orient=tk.VERTICAL, command=body_text.yview)
        body_text.configure(yscrollcommand=body_scroll_y.set)
        body_text.grid(row=0, column=0, sticky="nsew")
        body_scroll_y.grid(row=0, column=1, sticky="ns")

        body_preview = row.get("body_preview", "")
        body_text.insert("1.0", body_preview or "No message preview available.")
        body_text.config(state=tk.DISABLED)

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
            initialfile=default_filename,
        )

        if not file_path:
            return

        cleaned_rows = [{field: row.get(field, "") for field in self.export_fieldnames} for row in rows]

        with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.export_fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_rows)

        messagebox.showinfo("Export Completed", f"CSV exported successfully:\n{file_path}")

    def clear_results(self):
        self.results = []
        self.visible_indexes = []
        self.tree_item_to_index = {}
        self.sort_column = None
        self.sort_reverse = False
        self.tree.delete(*self.tree.get_children())
        self.update_column_headings()
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Ready.")

    def show_error(self, error_message):
        self.run_button.config(state=tk.NORMAL)
        self.export_selected_button.config(state=tk.DISABLED)
        self.export_visible_button.config(state=tk.DISABLED)
        self.status_var.set("Error occurred.")
        messagebox.showerror("Error", error_message)
