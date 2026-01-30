"""Digest Lambda handler - runs daily, summarizes all meetings, sends email."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from .config import load_config
from .gmail_client import GmailClient
from .storage import get_meetings_for_date, delete_meetings_for_date
from .summarizer import summarize_all_meetings, format_digest_email

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point for daily digest.
    Reads all meetings from DynamoDB, summarizes them, sends one email.
    """
    logger.info("Starting daily meeting digest")

    try:
        # Load configuration
        use_local = os.environ.get("USE_LOCAL_CONFIG", "false").lower() == "true"
        config = load_config(use_local=use_local)

        # Get today's date in PST
        pst = timezone(timedelta(hours=-8))
        today = datetime.now(pst).strftime("%Y-%m-%d")

        logger.info(f"Fetching meetings for {today}")

        # Get all meetings for today
        meetings = get_meetings_for_date(today)

        if not meetings:
            logger.info("No meetings to summarize today")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "No meetings to summarize",
                    "date": today,
                }),
            }

        logger.info(f"Found {len(meetings)} meetings to summarize")

        # Summarize all meetings
        summary = summarize_all_meetings(
            meetings=meetings,
            api_key=config.anthropic_api_key,
        )

        if not summary:
            logger.error("Failed to generate summary")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to generate summary"}),
            }

        # Format and send email
        email_html = format_digest_email(
            meetings=meetings,
            summary=summary,
            date=today,
        )

        gmail_client = GmailClient(config.gmail_credentials)

        today_formatted = datetime.strptime(today, "%Y-%m-%d").strftime("%B %d, %Y")
        subject = f"Daily Meeting Digest - {today_formatted}"

        # Send to all configured recipients
        successful_sends = []
        failed_sends = []

        for email in config.destination_emails:
            logger.info(f"Sending digest to {email}")
            success = gmail_client.send_email(
                to=email,
                subject=subject,
                body_html=email_html,
            )
            if success:
                successful_sends.append(email)
            else:
                failed_sends.append(email)

        if successful_sends:
            logger.info(f"Successfully sent daily digest to {successful_sends}")

            # Clean up processed meetings
            deleted = delete_meetings_for_date(today)
            logger.info(f"Cleaned up {deleted} meetings from DynamoDB")

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Daily digest sent successfully",
                    "meetings_count": len(meetings),
                    "date": today,
                    "destinations": successful_sends,
                    "failed": failed_sends,
                }),
            }
        else:
            logger.error("Failed to send email to any recipient")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to send email to any recipient"}),
            }

    except Exception as e:
        logger.exception(f"Error in digest handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def main():
    """Entry point for local testing."""
    os.environ["USE_LOCAL_CONFIG"] = "true"
    os.environ["MEETINGS_TABLE"] = "granola-meetings"

    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
