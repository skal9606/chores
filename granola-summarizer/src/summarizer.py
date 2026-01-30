"""Claude API summarization for meeting content."""

from datetime import datetime
from typing import Optional

import anthropic


def summarize_all_meetings(
    meetings: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Summarize multiple meetings in one API call.

    Args:
        meetings: List of meeting dictionaries from DynamoDB.
        api_key: Anthropic API key.
        model: Claude model to use.

    Returns:
        HTML-formatted summary string, or None if failed.
    """
    if not meetings:
        return None

    # Prepare content for all meetings
    meetings_content = []
    for i, meeting in enumerate(meetings, 1):
        title = meeting.get("title", "Untitled Meeting")
        attendees = meeting.get("attendees", [])
        notes = meeting.get("notes", "")
        transcript = meeting.get("transcript", "")

        attendee_str = ", ".join(attendees) if attendees else "Not specified"

        content = f"""
---
MEETING {i}: {title}
ATTENDEES: {attendee_str}

NOTES:
{notes or 'No notes available'}
"""
        if transcript:
            # Truncate transcript if too long (allow more for detailed summaries)
            max_transcript = 50000
            if len(transcript) > max_transcript:
                transcript = transcript[:max_transcript] + "\n[Truncated...]"
            content += f"\nTRANSCRIPT:\n{transcript}"

        content += "\n---"
        meetings_content.append(content)

    all_content = "\n".join(meetings_content)

    prompt = f"""You are creating detailed meeting records for a CRM/database. Preserve valuable information - don't reduce to executive bullet points.

You are processing {len(meetings)} meetings from today.

For EACH meeting, provide a record including:

1. **Meeting Context**: Who was there, what company/organization, purpose of the meeting (2-3 sentences)
2. **Discussion Overview**: Brief summary of main topics covered (3-5 bullet points max)
3. **Key Information**: Important facts, metrics, timelines, details mentioned (e.g., "50 employees", "Launch Q2", "$2M ARR") - be thorough here
4. **Decisions & Outcomes**: What was decided or agreed upon
5. **Action Items**: Specific next steps with owners if mentioned
6. **Open Questions**: Unresolved questions or topics to follow up on

Format your response as clean HTML. Use:
- <h2> for each meeting title
- <h3> for section headers within each meeting
- <ul><li> for bullet points
- <p> for paragraphs
- <strong> for emphasis on important items
- <hr> to separate meetings

Keep Discussion Overview brief. Put the detail in Key Information section instead.

Here are today's meetings:

{all_content}
"""

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        summary = response.content[0].text

        if not summary.strip().startswith("<"):
            summary = f"<div>{summary}</div>"

        return summary

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None


def format_digest_email(
    meetings: list[dict],
    summary: str,
    date: str,
) -> str:
    """
    Format the daily digest as a complete HTML email.

    Args:
        meetings: List of meeting dictionaries.
        summary: HTML summary content.
        date: Date string (YYYY-MM-DD).

    Returns:
        Complete HTML email body.
    """
    date_formatted = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d, %Y")
    meeting_count = len(meetings)

    meeting_list = "".join([
        f"<li>{m.get('title', 'Untitled')}</li>"
        for m in meetings
    ])

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
            border-left: 4px solid #4a4e69;
            padding-left: 15px;
        }}
        h3 {{
            color: #22223b;
            margin-top: 20px;
            font-size: 16px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 30px 0;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .toc {{
            background: #f5f5f5;
            padding: 15px 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .toc h3 {{
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .toc ul {{
            margin: 0;
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
    <h1>Daily Meeting Digest</h1>
    <p class="meta">{date_formatted} &bull; {meeting_count} meeting{"s" if meeting_count != 1 else ""}</p>

    <div class="toc">
        <h3>Today's Meetings</h3>
        <ul>
            {meeting_list}
        </ul>
    </div>

    {summary}

    <div class="footer">
        <p>This digest was automatically generated from Granola meeting notes using Claude AI.</p>
    </div>
</body>
</html>
"""


def summarize_meeting(
    title: str,
    attendees: list[str],
    notes: str,
    transcript: Optional[str],
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> Optional[str]:
    """
    Summarize meeting content using Claude API.

    Args:
        title: Meeting title.
        attendees: List of attendees.
        notes: Meeting notes from Granola.
        transcript: Full transcript (optional).
        api_key: Anthropic API key.
        model: Claude model to use.

    Returns:
        HTML-formatted summary string, or None if failed.
    """
    # Prepare content for summarization
    content = f"""MEETING TITLE: {title}

ATTENDEES: {', '.join(attendees) if attendees else 'Not specified'}

NOTES:
{notes or 'No notes available'}
"""

    if transcript:
        # Truncate transcript if too long
        max_transcript = 50000
        if len(transcript) > max_transcript:
            transcript = transcript[:max_transcript] + "\n\n[Transcript truncated...]"
        content += f"\nTRANSCRIPT:\n{transcript}"

    prompt = f"""You are a helpful assistant that creates concise meeting summaries.
Your goal is to extract the key information and action items from a meeting.

For this meeting, please provide:
1. A brief overview (2-3 sentences)
2. Key discussion points (bullet points)
3. Action items and next steps (if any)
4. Important decisions made (if any)

Focus on what matters most for follow-up. Be concise but comprehensive.

Format your response as clean HTML suitable for an email. Use:
- <h3> for section headers
- <ul><li> for bullet points
- <p> for paragraphs
- <strong> for emphasis on important items

Here is the meeting content:

{content}
"""

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
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
    title: str,
    attendees: list[str],
    summary: str,
) -> str:
    """
    Format the summary as a complete HTML email.

    Args:
        title: Meeting title.
        attendees: List of attendees.
        summary: HTML summary content.

    Returns:
        Complete HTML email body.
    """
    today = datetime.now().strftime("%A, %B %d, %Y")
    attendee_list = ', '.join(attendees) if attendees else 'Not specified'

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
            font-size: 24px;
        }}
        h2 {{
            color: #4a4e69;
            margin-top: 30px;
            font-size: 18px;
        }}
        h3 {{
            color: #22223b;
            margin-top: 20px;
            font-size: 16px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .attendees {{
            background: #f5f5f5;
            padding: 10px 15px;
            border-radius: 5px;
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
    <h1>{title}</h1>
    <p class="meta">{today}</p>
    <div class="attendees">
        <strong>Attendees:</strong> {attendee_list}
    </div>

    {summary}

    <div class="footer">
        <p>This summary was automatically generated from Granola meeting notes using Claude AI.</p>
    </div>
</body>
</html>
"""
