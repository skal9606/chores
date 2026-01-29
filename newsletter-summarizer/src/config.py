"""Configuration loading for newsletter summarizer."""

import json
import os
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError


@dataclass
class Config:
    """Application configuration."""
    gmail_senders: list[str]
    substack_feeds: list[str]
    destination_email: str
    source_gmail: str
    anthropic_api_key: str
    gmail_credentials: dict


def get_secret(secret_name: str, region: str = "us-west-2") -> dict:
    """Retrieve secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret {secret_name}: {e}")


def load_config(config_path: Optional[str] = None, use_local: bool = False) -> Config:
    """
    Load configuration from sources.json and secrets.

    Args:
        config_path: Path to sources.json. Defaults to config/sources.json.
        use_local: If True, load secrets from environment variables instead of AWS.
    """
    if config_path is None:
        # Look for config relative to this file's location
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "sources.json")

    with open(config_path) as f:
        sources = json.load(f)

    if use_local:
        # Load from environment variables for local testing
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        gmail_credentials_str = os.environ.get("GMAIL_CREDENTIALS", "{}")
        gmail_credentials = json.loads(gmail_credentials_str)
    else:
        # Load from AWS Secrets Manager
        secrets = get_secret("newsletter-summarizer/credentials")
        anthropic_api_key = secrets.get("anthropic_api_key", "")
        gmail_credentials = secrets.get("gmail_credentials", {})

    return Config(
        gmail_senders=sources.get("gmail_senders", []),
        substack_feeds=sources.get("substack_feeds", []),
        destination_email=sources.get("destination_email", ""),
        source_gmail=sources.get("source_gmail", ""),
        anthropic_api_key=anthropic_api_key,
        gmail_credentials=gmail_credentials,
    )
