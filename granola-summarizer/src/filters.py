"""Meeting filter logic for granola summarizer."""

import re
from typing import Optional

from .config import FilterConfig


def should_skip_meeting(
    title: str,
    attendees: list[str],
    filters: FilterConfig,
) -> tuple[bool, Optional[str]]:
    """
    Determine if a meeting should be skipped based on filter rules.

    Args:
        title: Meeting title.
        attendees: List of attendee email addresses.
        filters: Filter configuration.

    Returns:
        Tuple of (should_skip, reason).
    """
    # Check title-based filters
    for skip_title in filters.skip_titles:
        if skip_title.lower() in title.lower():
            return True, f"Title matches skip pattern: {skip_title}"

    # Check if all attendees are internal (all @1984.vc)
    if attendees and _all_internal(attendees, filters.skip_internal_domains):
        return True, "All attendees are internal"

    # Check if meeting is with VCs
    if attendees and _is_vc_meeting(attendees, filters.skip_vc_patterns):
        return True, "Meeting appears to be with VCs"

    return False, None


def _all_internal(attendees: list[str], internal_domains: list[str]) -> bool:
    """Check if all attendees are from internal domains."""
    if not attendees:
        return False

    for attendee in attendees:
        email = _extract_email(attendee)
        if not email:
            continue

        is_internal = False
        for domain in internal_domains:
            if email.endswith(domain):
                is_internal = True
                break

        if not is_internal:
            return False

    return True


def _is_vc_meeting(attendees: list[str], vc_patterns: list[str]) -> bool:
    """Check if any attendee matches VC domain patterns."""
    for attendee in attendees:
        email = _extract_email(attendee)
        if not email:
            continue

        for pattern in vc_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return True

    return False


def _extract_email(attendee: str) -> Optional[str]:
    """Extract email address from attendee string."""
    # Handle formats like "Name <email@domain.com>" or just "email@domain.com"
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', attendee)
    return match.group(0).lower() if match else None
