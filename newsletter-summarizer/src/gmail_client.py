"""Gmail API client for fetching and sending emails."""

import base64
import re
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials_dict: dict):
        """
        Initialize Gmail client with OAuth credentials.

        Args:
            credentials_dict: OAuth2 credentials dictionary containing:
                - token
                - refresh_token
                - token_uri
                - client_id
                - client_secret
        """
        self.credentials = Credentials(
            token=credentials_dict.get("token"),
            refresh_token=credentials_dict.get("refresh_token"),
            token_uri=credentials_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=credentials_dict.get("client_id"),
            client_secret=credentials_dict.get("client_secret"),
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

    def fetch_emails_from_senders(
        self,
        senders: list[str],
        hours_back: int = 24,
    ) -> list[dict]:
        """
        Fetch emails from specified senders within the time window.

        Args:
            senders: List of sender email addresses.
            hours_back: How many hours back to search.

        Returns:
            List of email dictionaries with 'subject', 'from', 'date', 'body'.
        """
        if not senders:
            return []

        # Build query for multiple senders
        sender_queries = " OR ".join([f"from:{sender}" for sender in senders])

        # Calculate date filter
        after_date = datetime.now() - timedelta(hours=hours_back)
        after_timestamp = int(after_date.timestamp())

        query = f"({sender_queries}) after:{after_timestamp}"

        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=50,
            ).execute()
        except Exception as e:
            print(f"Error fetching email list: {e}")
            return []

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            try:
                email_data = self._get_email_content(msg["id"])
                if email_data:
                    emails.append(email_data)
            except Exception as e:
                print(f"Error fetching email {msg['id']}: {e}")
                continue

        return emails

    def _get_email_content(self, message_id: str) -> Optional[dict]:
        """Fetch and parse a single email by ID."""
        message = self.service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

        headers = message.get("payload", {}).get("headers", [])

        subject = ""
        sender = ""
        date = ""

        for header in headers:
            name = header.get("name", "").lower()
            if name == "subject":
                subject = header.get("value", "")
            elif name == "from":
                sender = header.get("value", "")
            elif name == "date":
                date = header.get("value", "")

        # Extract body
        body = self._extract_body(message.get("payload", {}))

        if not body:
            return None

        return {
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body,
        }

    def _extract_body(self, payload: dict) -> str:
        """Extract plain text body from email payload."""
        body_text = ""

        # Check for direct body data
        if "body" in payload and payload["body"].get("data"):
            body_text = base64.urlsafe_b64decode(
                payload["body"]["data"]
            ).decode("utf-8", errors="ignore")

        # Check for parts (multipart emails)
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")

                if mime_type == "text/plain":
                    if part.get("body", {}).get("data"):
                        body_text = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8", errors="ignore")
                        break
                elif mime_type == "text/html":
                    if part.get("body", {}).get("data"):
                        html_content = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8", errors="ignore")
                        body_text = self._html_to_text(html_content)
                elif mime_type.startswith("multipart/"):
                    # Recursively extract from nested parts
                    nested_body = self._extract_body(part)
                    if nested_body:
                        body_text = nested_body
                        break

        return body_text.strip()

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "head", "meta"]):
            element.decompose()

        # Get text and clean up whitespace
        text = soup.get_text(separator="\n")

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)

        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body_html: HTML body content.
            body_text: Plain text body (optional, derived from HTML if not provided).

        Returns:
            True if sent successfully, False otherwise.
        """
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject

        # Add plain text version
        if body_text is None:
            body_text = self._html_to_text(body_html)

        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")

        message.attach(part1)
        message.attach(part2)

        # Encode the message
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        try:
            self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message},
            ).execute()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
