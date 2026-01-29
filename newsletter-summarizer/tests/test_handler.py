"""Tests for newsletter summarizer."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.rss_fetcher import fetch_rss_articles, parse_published_date
from src.summarizer import clean_html_content, prepare_content_for_summarization


class TestRssFetcher:
    """Tests for RSS fetching functionality."""

    def test_clean_html_content(self):
        """Test HTML to text conversion."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <h1>Hello World</h1>
            <p>This is a <strong>test</strong> paragraph.</p>
            <script>alert('bad');</script>
        </body>
        </html>
        """
        result = clean_html_content(html)

        assert "Hello World" in result
        assert "This is a test paragraph" in result
        assert "alert" not in result
        assert "<script>" not in result

    def test_prepare_content_for_summarization(self):
        """Test content preparation for Claude."""
        emails = [
            {
                "from": "test@example.com",
                "subject": "Test Email",
                "date": "2024-01-15",
                "body": "This is the email body.",
            }
        ]
        articles = [
            {
                "title": "Test Article",
                "author": "John Doe",
                "feed": "Test Feed",
                "date": "2024-01-15",
                "link": "https://example.com/article",
                "content": "<p>Article content here.</p>",
            }
        ]

        result = prepare_content_for_summarization(emails, articles)

        assert "test@example.com" in result
        assert "Test Email" in result
        assert "Test Article" in result
        assert "John Doe" in result

    def test_prepare_content_respects_max_chars(self):
        """Test that content preparation respects character limits."""
        emails = [
            {
                "from": "test@example.com",
                "subject": "Test",
                "date": "2024-01-15",
                "body": "x" * 1000,
            }
            for _ in range(100)
        ]

        result = prepare_content_for_summarization(emails, [], max_chars=5000)

        assert len(result) < 10000  # Should be limited


class TestSummarizer:
    """Tests for summarization functionality."""

    @patch("src.summarizer.anthropic.Anthropic")
    def test_summarize_newsletters(self, mock_anthropic):
        """Test Claude API summarization."""
        from src.summarizer import summarize_newsletters

        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<h2>Summary</h2><p>Test summary</p>")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        emails = [{"from": "test@test.com", "subject": "Test", "date": "", "body": "Content"}]

        result = summarize_newsletters(emails, [], api_key="test-key")

        assert result is not None
        assert "Summary" in result

    def test_summarize_newsletters_empty_content(self):
        """Test that empty content returns None."""
        from src.summarizer import summarize_newsletters

        result = summarize_newsletters([], [], api_key="test-key")

        assert result is None


class TestIntegration:
    """Integration tests (require mocking external services)."""

    @patch("src.handler.GmailClient")
    @patch("src.handler.fetch_rss_articles")
    @patch("src.handler.summarize_newsletters")
    @patch("src.handler.load_config")
    def test_lambda_handler_success(
        self,
        mock_config,
        mock_summarize,
        mock_rss,
        mock_gmail,
    ):
        """Test successful Lambda execution."""
        from src.handler import lambda_handler

        # Setup mocks
        mock_config.return_value = MagicMock(
            gmail_senders=["test@test.com"],
            substack_feeds=["https://test.com/feed"],
            destination_email="dest@test.com",
            anthropic_api_key="test-key",
            gmail_credentials={},
        )

        mock_gmail_instance = MagicMock()
        mock_gmail_instance.fetch_emails_from_senders.return_value = [
            {"from": "test@test.com", "subject": "Test", "date": "", "body": "Content"}
        ]
        mock_gmail_instance.send_email.return_value = True
        mock_gmail.return_value = mock_gmail_instance

        mock_rss.return_value = []
        mock_summarize.return_value = "<h2>Summary</h2>"

        # Execute
        result = lambda_handler({}, None)

        assert result["statusCode"] == 200
        assert "Newsletter digest sent successfully" in result["body"]

    @patch("src.handler.GmailClient")
    @patch("src.handler.fetch_rss_articles")
    @patch("src.handler.load_config")
    def test_lambda_handler_no_content(
        self,
        mock_config,
        mock_rss,
        mock_gmail,
    ):
        """Test Lambda execution with no content."""
        from src.handler import lambda_handler

        mock_config.return_value = MagicMock(
            gmail_senders=[],
            substack_feeds=[],
            destination_email="dest@test.com",
            anthropic_api_key="test-key",
            gmail_credentials={},
        )

        mock_gmail_instance = MagicMock()
        mock_gmail_instance.fetch_emails_from_senders.return_value = []
        mock_gmail.return_value = mock_gmail_instance

        mock_rss.return_value = []

        result = lambda_handler({}, None)

        assert result["statusCode"] == 200
        assert "No content found" in result["body"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
