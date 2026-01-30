"""Gmail API client for sending emails."""

import base64
import re
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
