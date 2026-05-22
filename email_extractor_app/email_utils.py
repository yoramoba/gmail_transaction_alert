import html
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime


class EmailParser:
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def normalize_text(value):
        value = html.unescape(value or "")
        value = value.replace("\xa0", " ")
        value = value.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        value = re.sub(r"\s+", " ", value).strip()
        return value

    @classmethod
    def extract_body(cls, message):
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
                    html_body += cls.html_to_text(decoded_payload) + "\n"
        else:
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or "utf-8"
                decoded_payload = payload.decode(charset, errors="ignore")

                if message.get_content_type() == "text/html":
                    html_body += cls.html_to_text(decoded_payload)
                else:
                    plain_body += decoded_payload

        return plain_body.strip() or html_body.strip()

    @classmethod
    def make_body_preview(cls, body, max_length=500):
        return cls.normalize_text(body)[:max_length]

    @classmethod
    def extract_attachments(cls, message):
        attachment_names = []

        for part in message.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()

            if filename:
                filename = cls.decode_mime_header(filename)

            if "attachment" in content_disposition.lower() or filename:
                attachment_names.append(filename or "Unnamed attachment")

        return attachment_names

    @staticmethod
    def parse_email_date(email_date_header):
        try:
            email_datetime = parsedate_to_datetime(email_date_header)
            return email_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return email_date_header or ""

    @classmethod
    def email_matches_keyword(cls, subject, sender, recipient, cc, body, keyword):
        keyword = keyword.strip().lower()

        if not keyword:
            return True

        searchable_text = " ".join([
            subject or "",
            sender or "",
            recipient or "",
            cc or "",
            body or "",
        ]).lower()

        return keyword in searchable_text


class BankTransactionParser:
    @staticmethod
    def clean_source(source):
        source = EmailParser.normalize_text(source or "")
        source = re.sub(r"^Dear\s+Customer,?\s*", "", source, flags=re.IGNORECASE).strip()
        source = re.sub(r"\s+purchase$", "", source, flags=re.IGNORECASE).strip()
        source = re.sub(r"\s+transaction$", "", source, flags=re.IGNORECASE).strip()
        return source.strip(" .:-")

    @classmethod
    def parse(cls, body):
        text = EmailParser.normalize_text(body)

        if not text:
            return None

        patterns = [
            re.compile(
                r"(?:Dear\s+Customer,?\s*)?"
                r"(?P<description>.*?)\s+from\s+"
                r"(?P<card>[0-9Xx*\s]{6,30})\s+"
                r"AED\s*(?P<amount>[0-9,]+(?:\.\d{1,2})?)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:Dear\s+Customer,?\s*)?"
                r"(?P<description>.*?)\s+AED\s*(?P<amount>[0-9,]+(?:\.\d{1,2})?)",
                re.IGNORECASE,
            ),
        ]

        for pattern in patterns:
            match = pattern.search(text)
            if not match:
                continue

            source = cls.clean_source(match.group("description"))
            amount_raw = match.group("amount").replace(",", "")

            if not source:
                continue

            if source.lower() in {"your current balance is", "current balance is"}:
                continue

            try:
                amount = f"AED {float(amount_raw):.2f}"
            except ValueError:
                amount = f"AED {amount_raw}"

            return {"source": source, "amount": amount}

        return None

