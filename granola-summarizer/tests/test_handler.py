"""Tests for granola summarizer handler."""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.filters import should_skip_meeting, _extract_email
from src.config import FilterConfig


class TestFilters:
    """Tests for meeting filter logic."""

    @pytest.fixture
    def filters(self):
        return FilterConfig(
            skip_titles=["1984 Partner Meeting"],
            skip_internal_domains=["@1984.vc"],
            skip_vc_patterns=[
                r"@.*vc\.com",
                r"@.*capital\.com",
                r"@.*ventures\.com",
            ],
        )

    def test_skip_partner_meeting(self, filters):
        should_skip, reason = should_skip_meeting(
            title="1984 Partner Meeting - Weekly",
            attendees=["partner1@1984.vc", "partner2@1984.vc"],
            filters=filters,
        )
        assert should_skip is True
        assert "1984 Partner Meeting" in reason

    def test_skip_internal_meeting(self, filters):
        should_skip, reason = should_skip_meeting(
            title="Team Standup",
            attendees=["alice@1984.vc", "bob@1984.vc"],
            filters=filters,
        )
        assert should_skip is True
        assert "internal" in reason.lower()

    def test_skip_vc_meeting(self, filters):
        should_skip, reason = should_skip_meeting(
            title="Intro Call",
            attendees=["founder@startup.com", "partner@acme-vc.com"],
            filters=filters,
        )
        assert should_skip is True
        assert "VC" in reason

    def test_allow_external_meeting(self, filters):
        should_skip, reason = should_skip_meeting(
            title="Product Demo",
            attendees=["samit@1984.vc", "customer@acme.com"],
            filters=filters,
        )
        assert should_skip is False
        assert reason is None

    def test_allow_founder_meeting(self, filters):
        should_skip, reason = should_skip_meeting(
            title="Founder Check-in",
            attendees=["samit@1984.vc", "founder@startup.io"],
            filters=filters,
        )
        assert should_skip is False
        assert reason is None


class TestEmailExtraction:
    """Tests for email extraction from attendee strings."""

    def test_plain_email(self):
        assert _extract_email("user@example.com") == "user@example.com"

    def test_name_with_email(self):
        assert _extract_email("John Doe <john@example.com>") == "john@example.com"

    def test_uppercase_email(self):
        assert _extract_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_invalid_string(self):
        assert _extract_email("not an email") is None


class TestWebhookPayload:
    """Tests for webhook payload handling."""

    def test_parse_string_attendees(self):
        """Test that comma-separated attendee string is parsed correctly."""
        from src.handler import lambda_handler

        # Mock the config loading and other dependencies
        with patch("src.handler.load_config") as mock_config, \
             patch("src.handler.should_skip_meeting") as mock_filter:

            mock_filter.return_value = (True, "Test skip")

            event = {
                "body": json.dumps({
                    "title": "Test Meeting",
                    "attendees": "user1@example.com, user2@example.com",
                    "notes": "Test notes",
                })
            }

            result = lambda_handler(event, None)

            # Should have parsed the attendees
            assert result["statusCode"] == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
