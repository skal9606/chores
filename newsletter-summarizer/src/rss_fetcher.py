"""RSS feed fetcher for Substack newsletters."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from time import mktime

import feedparser


def parse_published_date(entry: dict) -> Optional[datetime]:
    """Parse the published date from an RSS entry."""
    # Try published_parsed first
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)

    # Try updated_parsed
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)

    return None


def fetch_rss_articles(
    feed_urls: list[str],
    hours_back: int = 24,
    timeout: int = 30,
) -> list[dict]:
    """
    Fetch articles from RSS feeds published within the time window.

    Args:
        feed_urls: List of RSS feed URLs.
        hours_back: How many hours back to look for articles.
        timeout: Request timeout in seconds.

    Returns:
        List of article dictionaries with 'title', 'author', 'date', 'content', 'link'.
    """
    articles = []
    cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)

    for feed_url in feed_urls:
        try:
            feed = feedparser.parse(feed_url, request_headers={
                "User-Agent": "NewsletterSummarizer/1.0"
            })

            if feed.bozo and not feed.entries:
                print(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
                continue

            feed_title = feed.feed.get("title", "Unknown Feed")

            for entry in feed.entries:
                published = parse_published_date(entry)

                if published is None:
                    # If no date, include it (assume recent)
                    pass
                elif published < cutoff_time:
                    # Skip old articles
                    continue

                # Extract content
                content = ""

                # Try content:encoded first (full content)
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].get("value", "")

                # Fall back to summary
                if not content and hasattr(entry, "summary"):
                    content = entry.summary

                # Fall back to description
                if not content and hasattr(entry, "description"):
                    content = entry.description

                articles.append({
                    "title": entry.get("title", "Untitled"),
                    "author": entry.get("author", feed_title),
                    "date": published.isoformat() if published else "",
                    "content": content,
                    "link": entry.get("link", ""),
                    "feed": feed_title,
                })

        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            continue

    return articles
