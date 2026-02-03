"""Flask application for YouTube Transcript Summarizer."""

import re
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from transcript_client import fetch_transcript
from summarizer import summarize_transcript

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Content Security Policy - strict policy to prevent XSS
    # Allow DOMPurify from cdnjs for sanitization
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Enable HSTS (only on HTTPS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Control referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Restrict browser features
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    return response


def validate_video_id(video_id):
    """Validate YouTube video ID format (11 alphanumeric chars + dash + underscore)."""
    if not video_id:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    """Summarize a YouTube video transcript.

    Expects JSON body with:
        - url: YouTube video URL

    Returns JSON with:
        - success: bool
        - video_id: str (if successful)
        - transcript: str (if successful)
        - summary: str (if successful)
        - error: str (if failed)
    """
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "error": "Missing 'url' in request body."
        }), 400

    url = data["url"].strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "URL cannot be empty."
        }), 400

    # Basic URL validation - reject obviously malicious patterns
    if len(url) > 500:
        return jsonify({
            "success": False,
            "error": "URL too long."
        }), 400

    # Fetch transcript
    transcript_result = fetch_transcript(url)

    if not transcript_result["success"]:
        return jsonify(transcript_result), 400

    # Validate video ID format
    video_id = transcript_result.get("video_id", "")
    if not validate_video_id(video_id):
        return jsonify({
            "success": False,
            "error": "Invalid video ID."
        }), 400

    # Summarize transcript
    summary_result = summarize_transcript(transcript_result["transcript"])

    if not summary_result["success"]:
        return jsonify({
            "success": False,
            "video_id": video_id,
            "error": summary_result["error"]
        }), 500

    return jsonify({
        "success": True,
        "video_id": video_id,
        "transcript": transcript_result["transcript"],
        "summary": summary_result["summary"]
    })


@app.route("/transcript", methods=["POST"])
def get_transcript():
    """Get just the transcript for a YouTube video (no summarization).

    Expects JSON body with:
        - url: YouTube video URL

    Returns JSON with:
        - success: bool
        - video_id: str (if successful)
        - transcript: str (if successful)
        - error: str (if failed)
    """
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "error": "Missing 'url' in request body."
        }), 400

    url = data["url"].strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "URL cannot be empty."
        }), 400

    # Basic URL validation
    if len(url) > 500:
        return jsonify({
            "success": False,
            "error": "URL too long."
        }), 400

    # Fetch transcript only
    transcript_result = fetch_transcript(url)

    if not transcript_result["success"]:
        return jsonify(transcript_result), 400

    # Validate video ID format
    video_id = transcript_result.get("video_id", "")
    if not validate_video_id(video_id):
        return jsonify({
            "success": False,
            "error": "Invalid video ID."
        }), 400

    return jsonify({
        "success": True,
        "video_id": video_id,
        "transcript": transcript_result["transcript"]
    })


@app.route("/privacy")
def privacy():
    """Serve the privacy policy page."""
    return render_template("privacy.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
