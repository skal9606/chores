"""Webhook Lambda handler - receives Zapier webhooks and stores meetings."""

import json
import logging
import os

from .config import load_config
from .filters import should_skip_meeting
from .storage import store_meeting

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point for Zapier webhook.
    Stores meetings in DynamoDB for later processing.

    Expected webhook payload from Zapier:
    {
        "title": "Meeting title",
        "attendees": ["email1@domain.com", "email2@domain.com"],
        "notes": "Meeting notes...",
        "transcript": "Full transcript..." (optional)
    }
    """
    logger.info("Received webhook request")

    try:
        # Parse the webhook payload
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body

        logger.info(f"Payload: {json.dumps(payload, default=str)[:500]}")

        # Extract meeting data
        title = payload.get("title", "Untitled Meeting")
        attendees = payload.get("attendees", [])
        notes = payload.get("notes", "")
        transcript = payload.get("transcript")

        # Handle attendees as string or list
        if isinstance(attendees, str):
            attendees = [a.strip() for a in attendees.split(",") if a.strip()]

        logger.info(f"Meeting: {title}")
        logger.info(f"Attendees: {attendees}")

        # Load configuration for filters
        use_local = os.environ.get("USE_LOCAL_CONFIG", "false").lower() == "true"
        config = load_config(use_local=use_local)

        # Apply filters
        should_skip, reason = should_skip_meeting(title, attendees, config.filters)

        if should_skip:
            logger.info(f"Skipping meeting: {reason}")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Meeting skipped",
                    "reason": reason,
                    "title": title,
                }),
            }

        # Store meeting in DynamoDB
        meeting_id = store_meeting(
            title=title,
            attendees=attendees,
            notes=notes,
            transcript=transcript,
        )

        logger.info(f"Stored meeting {meeting_id}: {title}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Meeting stored for daily digest",
                "meeting_id": meeting_id,
                "title": title,
            }),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON payload"}),
        }
    except Exception as e:
        logger.exception(f"Error in webhook handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
