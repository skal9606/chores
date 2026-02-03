"""Flask application for YouTube Transcript Summarizer."""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from transcript_client import fetch_transcript
from summarizer import summarize_transcript

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension


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

    # Fetch transcript
    transcript_result = fetch_transcript(url)

    if not transcript_result["success"]:
        return jsonify(transcript_result), 400

    # Summarize transcript
    summary_result = summarize_transcript(transcript_result["transcript"])

    if not summary_result["success"]:
        return jsonify({
            "success": False,
            "video_id": transcript_result["video_id"],
            "error": summary_result["error"]
        }), 500

    return jsonify({
        "success": True,
        "video_id": transcript_result["video_id"],
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

    # Fetch transcript only
    transcript_result = fetch_transcript(url)

    if not transcript_result["success"]:
        return jsonify(transcript_result), 400

    return jsonify({
        "success": True,
        "video_id": transcript_result["video_id"],
        "transcript": transcript_result["transcript"]
    })


@app.route("/privacy")
def privacy():
    """Serve the privacy policy page."""
    return render_template("privacy.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
