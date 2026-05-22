import imaplib
from datetime import datetime, timedelta


class ImapClient:
    def __init__(self, credentials):
        self.credentials = credentials
        self.mail = None

    def __enter__(self):
        self.mail = imaplib.IMAP4_SSL(
            self.credentials["imap_server"],
            int(self.credentials["imap_port"]),
        )
        self.mail.login(self.credentials["login_email"], self.credentials["password"])
        return self

    def __exit__(self, exc_type, exc, traceback):
        if not self.mail:
            return

        try:
            self.mail.close()
        except Exception:
            pass

        try:
            self.mail.logout()
        except Exception:
            pass

    def select_mailbox(self):
        mailbox = str(self.credentials.get("mailbox", "INBOX")).strip() or "INBOX"
        status, _ = self.mail.select(mailbox)
        if status != "OK":
            raise RuntimeError(f"Could not open mailbox: {mailbox}")
        return mailbox

    def search(self, from_email, to_email, subject, start_date, end_date):
        criteria = self.build_search_criteria(from_email, to_email, subject, start_date, end_date)
        status, data = self.mail.search(None, criteria)
        if status != "OK":
            raise RuntimeError("IMAP search failed.")
        return criteria, data[0].split()

    def fetch_message_without_changing_seen(self, message_id):
        was_seen = self.get_message_seen_state(message_id)
        status, msg_data = self.mail.fetch(message_id, "(BODY.PEEK[])")
        self.restore_message_seen_state(message_id, was_seen)
        return status, msg_data

    def get_message_seen_state(self, message_id):
        status, data = self.mail.fetch(message_id, "(FLAGS)")
        if status != "OK" or not data:
            return None

        flags_text = " ".join(
            item.decode("utf-8", errors="ignore") if isinstance(item, bytes) else str(item)
            for item in data
        )
        return "\\Seen" in flags_text

    def restore_message_seen_state(self, message_id, was_seen):
        if was_seen is None:
            return

        try:
            if was_seen:
                self.mail.store(message_id, "+FLAGS", "\\Seen")
            else:
                self.mail.store(message_id, "-FLAGS", "\\Seen")
        except Exception:
            pass

    @classmethod
    def build_search_criteria(cls, from_email, to_email, subject, start_date, end_date):
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        criteria = [
            f'SINCE "{start.strftime("%d-%b-%Y")}"',
            f'BEFORE "{end.strftime("%d-%b-%Y")}"',
        ]

        if from_email.strip():
            criteria.append(f'FROM {cls.quote_value(from_email.strip())}')

        if to_email.strip():
            criteria.append(f'TO {cls.quote_value(to_email.strip())}')

        if subject.strip():
            criteria.append(f'SUBJECT {cls.quote_value(subject.strip())}')

        return "(" + " ".join(criteria) + ")"

    @staticmethod
    def quote_value(value):
        value = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{value}"'

