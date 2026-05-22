import json
import os


class CredentialsLoader:
    REQUIRED_FIELDS = [
        "imap_server",
        "imap_port",
        "mailbox",
        "login_email",
        "password",
    ]

    def __init__(self, file_path="credentials.json"):
        self.file_path = file_path

    def load(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"{self.file_path} was not found. Create it in the same folder as this script."
            )

        with open(self.file_path, "r", encoding="utf-8") as file:
            credentials = json.load(file)

        missing_fields = [
            field for field in self.REQUIRED_FIELDS
            if field not in credentials or credentials[field] in (None, "")
        ]

        if missing_fields:
            raise ValueError(
                "Missing fields in credentials.json: " + ", ".join(missing_fields)
            )

        return credentials

