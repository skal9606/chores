# YouTube Transcript Summarizer

A web app and Chrome extension that fetches YouTube video transcripts and summarizes them using Claude AI to extract key learnings.

## Features

- **Web App**: Paste any YouTube URL to get a summary
- **Chrome Extension**: Summarize videos directly from YouTube
- **Markdown Download**: Download full transcript + summary as .md file
- Extracts transcripts using the free `youtube-transcript-api`
- Summarizes content with Claude AI focusing on:
  - Main topic and thesis
  - Key learnings (bullet points)
  - Notable quotes or insights
  - Actionable takeaways

## Setup

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Anthropic API key:
   ```bash
   echo 'ANTHROPIC_API_KEY=your-api-key-here' > .env
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open http://localhost:5001 in your browser

### Chrome Extension (Local)

1. Make sure the Flask app is running
2. Open `chrome://extensions/` in Chrome
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `chrome-extension/` folder
6. Navigate to any YouTube video and click the extension icon

### Cloud Deployment (Render)

1. Push this repo to GitHub
2. Go to [Render](https://render.com) and create a new Web Service
3. Connect your GitHub repo
4. Set environment variable: `ANTHROPIC_API_KEY`
5. Deploy

After deploying, update the Chrome extension settings with your Render URL.

## API Endpoints

### `POST /summarize`
Fetch transcript and generate summary.

**Request:**
```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

**Response:**
```json
{
  "success": true,
  "video_id": "VIDEO_ID",
  "transcript": "full transcript text...",
  "summary": "markdown summary..."
}
```

### `POST /transcript`
Fetch transcript only (no summarization).

**Request:**
```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

**Response:**
```json
{
  "success": true,
  "video_id": "VIDEO_ID",
  "transcript": "full transcript text..."
}
```

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- Just the video ID itself

## Tech Stack

- **Backend**: Python + Flask
- **Transcript**: `youtube-transcript-api` (free, no API key needed)
- **Summarization**: Anthropic Claude API (claude-sonnet-4)
- **Frontend**: HTML/CSS/JS (no framework)
- **Extension**: Chrome Manifest V3

## Limitations

- Only works with videos that have transcripts/captions enabled
- Very long transcripts are truncated to ~100KB
- Requires an Anthropic API key
