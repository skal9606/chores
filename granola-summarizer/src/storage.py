"""DynamoDB storage for meetings."""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key


def get_table():
    """Get DynamoDB table resource."""
    dynamodb = boto3.resource("dynamodb")
    table_name = os.environ.get("MEETINGS_TABLE", "granola-meetings")
    return dynamodb.Table(table_name)


def store_meeting(
    title: str,
    attendees: list[str],
    notes: str,
    transcript: Optional[str] = None,
    date: Optional[str] = None,
) -> str:
    """
    Store a meeting in DynamoDB.

    Args:
        title: Meeting title.
        attendees: List of attendees.
        notes: Meeting notes.
        transcript: Optional transcript.
        date: Optional date override (YYYY-MM-DD). Defaults to today.

    Returns:
        The meeting_id.
    """
    table = get_table()

    if date is None:
        # Use PST timezone for date
        from datetime import timezone
        pst = timezone(timedelta(hours=-8))
        date = datetime.now(pst).strftime("%Y-%m-%d")

    meeting_id = str(uuid.uuid4())

    # TTL: expire after 7 days
    ttl = int((datetime.now() + timedelta(days=7)).timestamp())

    item = {
        "date": date,
        "meeting_id": meeting_id,
        "title": title,
        "attendees": attendees,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
        "ttl": ttl,
    }

    if transcript:
        item["transcript"] = transcript

    table.put_item(Item=item)

    return meeting_id


def get_meetings_for_date(date: Optional[str] = None) -> list[dict]:
    """
    Get all meetings for a specific date.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today (PST).

    Returns:
        List of meeting dictionaries.
    """
    table = get_table()

    if date is None:
        from datetime import timezone
        pst = timezone(timedelta(hours=-8))
        date = datetime.now(pst).strftime("%Y-%m-%d")

    response = table.query(
        KeyConditionExpression=Key("date").eq(date)
    )

    return response.get("Items", [])


def delete_meeting(date: str, meeting_id: str) -> None:
    """Delete a meeting from DynamoDB."""
    table = get_table()
    table.delete_item(
        Key={
            "date": date,
            "meeting_id": meeting_id,
        }
    )


def delete_meetings_for_date(date: str) -> int:
    """
    Delete all meetings for a specific date.

    Args:
        date: Date in YYYY-MM-DD format.

    Returns:
        Number of meetings deleted.
    """
    meetings = get_meetings_for_date(date)

    for meeting in meetings:
        delete_meeting(date, meeting["meeting_id"])

    return len(meetings)
