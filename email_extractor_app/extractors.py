import email

from .email_utils import BankTransactionParser, EmailParser
from .imap_client import ImapClient


class BaseEmailExtractor:
    def __init__(self, credentials, progress_callback=None):
        self.credentials = credentials
        self.progress_callback = progress_callback

    def report(self, message):
        if self.progress_callback:
            self.progress_callback(message)

    def fetch_messages(self, from_email, to_email, subject, start_date, end_date):
        self.report("Connecting to IMAP server...")
        with ImapClient(self.credentials) as client:
            mailbox = client.select_mailbox()
            self.report(f"Opening mailbox: {mailbox}")

            criteria, message_ids = client.search(from_email, to_email, subject, start_date, end_date)
            self.report(f"Searching with criteria: {criteria}")
            self.report(f"Found {len(message_ids)} emails. Reading messages...")

            for index, message_id in enumerate(message_ids, start=1):
                self.report(f"Reading email {index} of {len(message_ids)}...")

                status, msg_data = client.fetch_message_without_changing_seen(message_id)
                if status != "OK":
                    continue

                yield email.message_from_bytes(msg_data[0][1])


class GeneralEmailExtractor(BaseEmailExtractor):
    def extract(self, from_email, to_email, subject, keyword, start_date, end_date):
        results = []

        for message in self.fetch_messages(from_email, to_email, subject, start_date, end_date):
            email_subject = EmailParser.decode_mime_header(message.get("Subject", ""))
            sender = EmailParser.decode_mime_header(message.get("From", ""))
            recipient = EmailParser.decode_mime_header(message.get("To", ""))
            cc = EmailParser.decode_mime_header(message.get("Cc", ""))
            reply_to = EmailParser.decode_mime_header(message.get("Reply-To", ""))
            email_date_header = message.get("Date", "")
            message_id_header = message.get("Message-ID", "")

            body = EmailParser.extract_body(message)

            if not EmailParser.email_matches_keyword(email_subject, sender, recipient, cc, body, keyword):
                continue

            attachment_names = EmailParser.extract_attachments(message)

            results.append({
                "_selected": True,
                "email_date": EmailParser.parse_email_date(email_date_header),
                "from": sender,
                "to": recipient,
                "cc": cc,
                "reply_to": reply_to,
                "subject": email_subject,
                "body_preview": EmailParser.make_body_preview(body),
                "has_attachments": "Yes" if attachment_names else "No",
                "attachment_count": len(attachment_names),
                "attachment_names": "; ".join(attachment_names),
                "message_id": message_id_header,
            })

        return results


class BankTransactionExtractor(BaseEmailExtractor):
    def extract(self, from_email, subject, start_date, end_date):
        results = []

        for message in self.fetch_messages(from_email, "", subject, start_date, end_date):
            email_subject = EmailParser.decode_mime_header(message.get("Subject", ""))
            sender = EmailParser.decode_mime_header(message.get("From", ""))
            email_date_header = message.get("Date", "")

            body = EmailParser.extract_body(message)
            parsed = BankTransactionParser.parse(body)
            body_preview = EmailParser.make_body_preview(body)

            if not parsed:
                results.append({
                    "_selected": False,
                    "email_date": EmailParser.parse_email_date(email_date_header),
                    "source": "NOT PARSED",
                    "amount": "NOT PARSED",
                    "status": "Failed to parse",
                    "subject": email_subject,
                    "from": sender,
                    "body_preview": body_preview,
                })
                continue

            results.append({
                "_selected": True,
                "email_date": EmailParser.parse_email_date(email_date_header),
                "source": parsed["source"],
                "amount": parsed["amount"],
                "status": "Parsed",
                "subject": email_subject,
                "from": sender,
                "body_preview": body_preview,
            })

        return results
