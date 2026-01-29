"""Claude API summarization for newsletter content."""

from typing import Optional

import anthropic
from bs4 import BeautifulSoup


def clean_html_content(html: str) -> str:
    """Strip HTML tags and clean up content for summarization."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator="\n")

    # Clean up whitespace
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def prepare_content_for_summarization(
    emails: list[dict],
    rss_articles: list[dict],
    max_chars: int = 100000,
) -> str:
    """
    Prepare newsletter content for Claude summarization.

    Args:
        emails: List of email dictionaries.
        rss_articles: List of RSS article dictionaries.
        max_chars: Maximum character limit for content.

    Returns:
        Formatted string of all newsletter content.
    """
    sections = []
    total_chars = 0

    # Add emails
    for email in emails:
        if total_chars >= max_chars:
            break

        section = f"""
---
EMAIL FROM: {email['from']}
SUBJECT: {email['subject']}
DATE: {email['date']}

{email['body'][:10000]}
---
"""
        sections.append(section)
        total_chars += len(section)

    # Add RSS articles
    for article in rss_articles:
        if total_chars >= max_chars:
            break

        content = clean_html_content(article['content'])[:10000]

        section = f"""
---
ARTICLE: {article['title']}
FROM: {article['author']} ({article['feed']})
DATE: {article['date']}
LINK: {article['link']}

{content}
---
"""
        sections.append(section)
        total_chars += len(section)

    return "\n".join(sections)


def summarize_newsletters(
    emails: list[dict],
    rss_articles: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Summarize newsletter content using Claude API.

    Args:
        emails: List of email dictionaries.
        rss_articles: List of RSS article dictionaries.
        api_key: Anthropic API key.
        model: Claude model to use.

    Returns:
        HTML-formatted summary string, or None if failed.
    """
    if not emails and not rss_articles:
        return None

    content = prepare_content_for_summarization(emails, rss_articles)

    prompt = f"""You are a helpful assistant that summarizes daily newsletters and articles.
Your goal is to create a concise, well-organized digest that captures the key insights
and important information from the day's content.

IMPORTANT: Summarize each newsletter/article separately. Each summary section MUST have a header
that clearly identifies the source newsletter (e.g., "Lenny's Newsletter", "Stratechery",
"Bloomberg", "The Generalist", etc.). Do NOT group content by theme - keep each newsletter's
summary in its own distinct section.

For each newsletter/article:
1. Use the newsletter name as the section header
2. Identify the main topic or thesis
3. Extract 2-3 key takeaways or insights
4. Note any actionable items or important dates/events

Format your response as clean HTML suitable for an email digest. Use:
- <h2> for the newsletter/source name (e.g., "Lenny's Newsletter", "Stratechery")
- <h3> for the article title or subject if relevant
- <ul><li> for key points
- <p> for any additional context
- <a href="..."> for links to original articles when available

Keep the summary concise but informative. The reader should be able to quickly understand
what's important from each newsletter today.

Here is the content to summarize:

{content}
"""

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        summary = response.content[0].text

        # Wrap in basic HTML structure if not already wrapped
        if not summary.strip().startswith("<"):
            summary = f"<div>{summary}</div>"

        return summary

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None


def format_summary_email(
    summary: str,
    email_count: int,
    article_count: int,
) -> str:
    """
    Format the summary as a complete HTML email.

    Args:
        summary: HTML summary content.
        email_count: Number of emails summarized.
        article_count: Number of RSS articles summarized.

    Returns:
        Complete HTML email body.
    """
    from datetime import datetime

    today = datetime.now().strftime("%A, %B %d, %Y")

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 2px solid #4a4e69;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #4a4e69;
            margin-top: 30px;
        }}
        h3 {{
            color: #22223b;
            margin-top: 20px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        a {{
            color: #4a4e69;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 0.85em;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>📬 Daily Newsletter Digest</h1>
    <p class="meta">{today} • {email_count} emails, {article_count} articles</p>

    {summary}

    <div class="footer">
        <p>This digest was automatically generated by Newsletter Summarizer using Claude AI.</p>
    </div>
</body>
</html>
"""
