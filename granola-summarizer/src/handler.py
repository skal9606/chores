"""Lambda handler for granola meeting summarizer."""

import json
import logging
import os
from datetime import datetime

from .config import load_config
from .filters import should_skip_meeting
from .gmail_client import GmailClient
from .summarizer import summarize_meeting, format_summary_email

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point for Zapier webhook.

    Expected webhook payload from Zapier:
    {
        "title": "Meeting title",
        "attendees": ["email1@domain.com", "email2@domain.com"],
        "notes": "Meeting notes...",
        "transcript": "Full transcript..." (optional)
    }

    Args:
        event: Lambda event from API Gateway.
        context: Lambda context.

    Returns:
        Response dictionary with statusCode and body.
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

        # Load configuration
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

        # Summarize the meeting
        logger.info("Summarizing meeting with Claude")
        summary = summarize_meeting(
            title=title,
            attendees=attendees,
            notes=notes,
            transcript=transcript,
            api_key=config.anthropic_api_key,
        )

        if not summary:
            logger.error("Failed to generate summary")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to generate summary"}),
            }

        # Format and send email
        logger.info(f"Sending summary to {config.destination_email}")
        email_html = format_summary_email(
            title=title,
            attendees=attendees,
            summary=summary,
        )

        gmail_client = GmailClient(config.gmail_credentials)
        today = datetime.now().strftime("%B %d")
        subject = f"Meeting Summary: {title} ({today})"

        success = gmail_client.send_email(
            to=config.destination_email,
            subject=subject,
            body_html=email_html,
        )

        if success:
            logger.info("Successfully sent meeting summary email")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Meeting summary sent successfully",
                    "title": title,
                    "destination": config.destination_email,
                }),
            }
        else:
            logger.error("Failed to send email")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to send email"}),
            }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON payload"}),
        }
    except Exception as e:
        logger.exception(f"Error in lambda handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def main():
    """Entry point for local testing."""
    os.environ["USE_LOCAL_CONFIG"] = "true"

    # Sample test event
    test_event = {
        "body": json.dumps({
            "title": "Product Sync with Acme Corp",
            "attendees": ["john@acme.com", "jane@example.com"],
            "notes": "Discussed product roadmap and integration timeline.",
            "transcript": None,
        })
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
