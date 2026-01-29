# Daily Newsletter Summarizer

An AWS Lambda function that automatically fetches newsletters from Gmail and Substack RSS feeds, summarizes them using Claude AI, and sends a daily digest email.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  EventBridge    │────▶│  AWS Lambda     │
│  (Daily 7am PT) │     │  (Python 3.11)  │
└─────────────────┘     └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────┐    ┌──────────────────┐
│  Gmail API    │    │  Substack RSS     │    │  Claude API      │
│  (read emails)│    │  (feedparser)     │    │  (summarize)     │
└───────────────┘    └───────────────────┘    └──────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 ▼
                        ┌───────────────┐
                        │  Gmail API    │
                        │  (send email) │
                        └───────────────┘
```

## Setup

### 1. Configure Newsletter Sources

Edit `config/sources.json`:

```json
{
  "gmail_senders": [
    "newsletter@stratechery.com",
    "dan@tldrnewsletter.com"
  ],
  "substack_feeds": [
    "https://stratechery.com/feed",
    "https://www.lennysnewsletter.com/feed"
  ],
  "destination_email": "samit@1984.vc",
  "source_gmail": "your-gmail@gmail.com"
}
```

### 2. Set Up Gmail OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials JSON
6. Run the OAuth flow to get refresh token (see `scripts/get_gmail_token.py`)

### 3. Store Secrets in AWS Secrets Manager

Create a secret named `newsletter-summarizer/credentials` with:

```json
{
  "anthropic_api_key": "sk-ant-...",
  "gmail_credentials": {
    "token": "...",
    "refresh_token": "...",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "...apps.googleusercontent.com",
    "client_secret": "..."
  }
}
```

### 4. Deploy with SAM

```bash
# Install dependencies
pip install -r requirements.txt

# Build and deploy
sam build
sam deploy --guided
```

## Local Development

### Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

### Run Tests

```bash
pytest tests/ -v
```

### Test Locally

Set environment variables:

```bash
export USE_LOCAL_CONFIG=true
export ANTHROPIC_API_KEY=sk-ant-...
export GMAIL_CREDENTIALS='{"token":"...","refresh_token":"...","client_id":"...","client_secret":"..."}'
```

Then run:

```bash
python -m src.handler
```

Or use SAM CLI:

```bash
sam local invoke NewsletterSummarizerFunction
```

## Configuration

### Schedule

Default: Daily at 7am Pacific Time (14:00 UTC)

To change, modify the `ScheduleExpression` parameter in `template.yaml` or pass during deployment:

```bash
sam deploy --parameter-overrides ScheduleExpression="cron(0 15 * * ? *)"
```

### Content Limits

- Maximum 100 emails processed per run
- Maximum 100KB of content sent to Claude
- Individual email/article content truncated at 10KB

## Troubleshooting

### No emails found

- Verify sender addresses match exactly (check Gmail for actual sender)
- Check the 24-hour window - run manually to test

### OAuth errors

- Refresh token may have expired - rerun OAuth flow
- Ensure Gmail API is enabled in Google Cloud Console

### Lambda timeout

- Default timeout is 5 minutes
- Increase in `template.yaml` if processing many newsletters

## Files

```
newsletter-summarizer/
├── src/
│   ├── __init__.py
│   ├── handler.py          # Lambda entry point
│   ├── gmail_client.py     # Gmail API wrapper
│   ├── rss_fetcher.py      # Substack RSS fetching
│   ├── summarizer.py       # Claude API summarization
│   └── config.py           # Config loading
├── config/
│   └── sources.json        # Newsletter sources
├── tests/
│   └── test_handler.py
├── requirements.txt
├── template.yaml           # SAM template
└── README.md
```
