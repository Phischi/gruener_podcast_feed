from __future__ import annotations

from email import policy
from email.parser import BytesParser
import imaplib

from .config import ImapConfig
from .newsletter import newsletter_from_message
from .models import Newsletter


def fetch_latest_matching_newsletter(config: ImapConfig) -> tuple[Newsletter, bytes]:
    mail = imaplib.IMAP4_SSL(config.host, config.port)
    try:
        mail.login(config.username, config.password)
        status, _ = mail.select(config.mailbox)
        if status != "OK":
            raise RuntimeError(f"Failed to select mailbox {config.mailbox}")

        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            raise RuntimeError("No messages found in mailbox")

        message_ids = data[0].split()
        for message_id in reversed(message_ids[-config.lookback_limit:]):
            status, raw_parts = mail.fetch(message_id, "(RFC822)")
            if status != "OK" or not raw_parts or not raw_parts[0]:
                continue
            raw_email = raw_parts[0][1]
            if not isinstance(raw_email, bytes):
                continue

            message = BytesParser(policy=policy.default).parsebytes(raw_email)
            subject = message.get("Subject", "")
            sender = message.get("From", "")

            if config.subject_prefix and not subject.startswith(config.subject_prefix):
                continue
            if config.from_filter and config.from_filter not in sender:
                continue

            return newsletter_from_message(message), raw_email

        raise RuntimeError("No matching newsletter email found")
    finally:
        try:
            mail.logout()
        except Exception:
            pass
