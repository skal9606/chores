"""Lambda handler for newsletter summarizer."""

import json
import logging
import os
from datetime import datetime

from .config import load_config
from .gmail_client import GmailClient
from .rss_fetcher import fetch_rss_articles
from .summarizer import summarize_newsletters, format_summary_email

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.

    Args:
        event: Lambda event (from EventBridge or manual invoke).
        context: Lambda context.

    Returns:
        Response dictionary with statusCode and body.
    """
    logger.info("Starting newsletter summarization")
    logger.info(f"Event: {json.dumps(event)}")

    try:
        # Load configuration
        use_local = os.environ.get("USE_LOCAL_CONFIG", "false").lower() == "true"
        config = load_config(use_local=use_local)

        # Fetch emails from Gmail
        logger.info(f"Fetching emails from {len(config.gmail_senders)} senders")
        gmail_client = GmailClient(config.gmail_credentials)
        emails = gmail_client.fetch_emails_from_senders(
            senders=config.gmail_senders,
            hours_back=24,
        )
        logger.info(f"Found {len(emails)} emails")

        # Fetch RSS articles
        logger.info(f"Fetching articles from {len(config.substack_feeds)} RSS feeds")
        articles = fetch_rss_articles(
            feed_urls=config.substack_feeds,
            hours_back=24,
        )
        logger.info(f"Found {len(articles)} articles")

        # Check if we have any content
        if not emails and not articles:
            logger.info("No content found to summarize")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "No content found to summarize",
                    "emails": 0,
                    "articles": 0,
                }),
            }

        # Summarize content
        logger.info("Summarizing content with Claude")
        summary = summarize_newsletters(
            emails=emails,
            rss_articles=articles,
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
            summary=summary,
            email_count=len(emails),
            article_count=len(articles),
        )

        today = datetime.now().strftime("%B %d, %Y")
        subject = f"📬 Daily Newsletter Digest - {today}"

        success = gmail_client.send_email(
            to=config.destination_email,
            subject=subject,
            body_html=email_html,
        )

        if success:
            logger.info("Successfully sent digest email")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Newsletter digest sent successfully",
                    "emails": len(emails),
                    "articles": len(articles),
                    "destination": config.destination_email,
                }),
            }
        else:
            logger.error("Failed to send email")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to send email"}),
            }

    except Exception as e:
        logger.exception(f"Error in lambda handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def main():
    """Entry point for local testing."""
    # For local testing, set USE_LOCAL_CONFIG=true and provide env vars
    os.environ["USE_LOCAL_CONFIG"] = "true"

    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
