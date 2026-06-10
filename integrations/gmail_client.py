import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import GMAIL_ADDRESS, GMAIL_APP_PASSWORD


class GmailClient:
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(self):
        self.address = GMAIL_ADDRESS
        self.password = GMAIL_APP_PASSWORD

    SIGNATURE = "藤原 / tobira-webdesign.com"

    def _ensure_signature(self, body: str) -> str:
        # Remove any trailing newlines, then attach signature with NO leading newline.
        # Keeping it on the same line as the last sentence prevents Gmail from
        # treating it as a collapsible signature block.
        body = body.rstrip()
        if self.SIGNATURE in body:
            # Strip all newlines immediately before the signature
            body = re.sub(r'\n+藤原 / tobira-webdesign\.com', '藤原 / tobira-webdesign.com', body)
        else:
            body = body + "藤原 / tobira-webdesign.com"
        return body

    def send(self, to_email: str, subject: str, body: str, video_path=None) -> bool:
        body = self._ensure_signature(body)
        msg = MIMEMultipart()
        msg["From"] = f"藤原 <{self.address}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
            server.starttls()
            server.login(self.address, self.password)
            server.sendmail(self.address, to_email, msg.as_string())
        return True
