#!/usr/bin/env python3
"""
Script to obtain Gmail OAuth2 credentials for the newsletter summarizer.

Usage:
    1. Download OAuth client credentials from Google Cloud Console
       (Create credentials -> OAuth client ID -> Desktop app)
    2. Save as 'client_secrets.json' in this directory
    3. Run: python get_gmail_token.py
    4. Complete the OAuth flow in your browser
    5. Copy the output JSON to AWS Secrets Manager

Required scopes:
    - gmail.readonly (read emails)
    - gmail.send (send digest)
"""

import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
    script_dir = Path(__file__).parent
    client_secrets_path = script_dir / "client_secrets.json"

    if not client_secrets_path.exists():
        print("Error: client_secrets.json not found!")
        print("\nTo get this file:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select or create a project")
        print("3. Enable the Gmail API")
        print("4. Go to Credentials -> Create Credentials -> OAuth client ID")
        print("5. Select 'Desktop app' as the application type")
        print("6. Download the JSON and save it as 'client_secrets.json' here")
        return

    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets_path),
        scopes=SCOPES,
    )

    print("Opening browser for authentication...")
    print("(If browser doesn't open, copy the URL from the terminal)")
    print()

    credentials = flow.run_local_server(port=8080)

    # Format credentials for storage
    creds_dict = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
    }

    print("\n" + "=" * 60)
    print("SUCCESS! Copy the following JSON to AWS Secrets Manager")
    print("=" * 60)
    print()
    print("Secret name: newsletter-summarizer/credentials")
    print("Add this as the 'gmail_credentials' field:")
    print()
    print(json.dumps(creds_dict, indent=2))
    print()

    # Also save locally for testing
    output_path = script_dir / "gmail_credentials.json"
    with open(output_path, "w") as f:
        json.dump(creds_dict, f, indent=2)

    print(f"Also saved to: {output_path}")
    print("(Delete this file after copying to Secrets Manager)")


if __name__ == "__main__":
    main()
