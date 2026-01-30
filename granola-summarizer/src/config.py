"""Configuration loading for granola summarizer."""

import json
import os
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError


@dataclass
class FilterConfig:
    """Filter configuration for meetings."""
    skip_titles: list[str]
    skip_internal_domains: list[str]
    skip_vc_patterns: list[str]


@dataclass
class Config:
    """Application configuration."""
    destination_emails: list[str]
    filters: FilterConfig
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
    Load configuration from settings.json and secrets.

    Args:
        config_path: Path to settings.json. Defaults to config/settings.json.
        use_local: If True, load secrets from environment variables instead of AWS.
    """
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "settings.json")

    with open(config_path) as f:
        settings = json.load(f)

    filters = FilterConfig(
        skip_titles=settings.get("filters", {}).get("skip_titles", []),
        skip_internal_domains=settings.get("filters", {}).get("skip_internal_domains", []),
        skip_vc_patterns=settings.get("filters", {}).get("skip_vc_patterns", []),
    )

    if use_local:
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        gmail_credentials_str = os.environ.get("GMAIL_CREDENTIALS", "{}")
        gmail_credentials = json.loads(gmail_credentials_str)
    else:
        secrets = get_secret("granola-summarizer/credentials")
        anthropic_api_key = secrets.get("anthropic_api_key", "")
        gmail_credentials = secrets.get("gmail_credentials", {})

    return Config(
        destination_emails=settings.get("destination_emails", []),
        filters=filters,
        anthropic_api_key=anthropic_api_key,
        gmail_credentials=gmail_credentials,
    )
