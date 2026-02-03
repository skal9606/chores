"""Claude API summarization for YouTube transcripts."""

import os
from anthropic import Anthropic

# Maximum transcript size (100KB like newsletter-summarizer)
MAX_TRANSCRIPT_SIZE = 100 * 1024

SUMMARY_PROMPT = """Summarize this YouTube video transcript. Extract:

1. **Main Topic & Thesis**: What is this video about? What's the central argument or message?

2. **Key Learnings** (bullet points): What are the most important takeaways?

3. **Notable Quotes or Insights**: Any memorable statements or unique perspectives?

4. **Actionable Takeaways**: What can someone do with this information?

Keep the summary concise but comprehensive. Focus on insights that would be valuable for a venture capitalist interested in technology, startups, and business trends.

Here's the transcript:

{transcript}"""


def summarize_transcript(transcript: str) -> dict:
    """Summarize a YouTube transcript using Claude API.

    Args:
        transcript: The full transcript text

    Returns:
        dict with keys:
            - success: bool
            - summary: str (if successful)
            - error: str (if failed)
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "ANTHROPIC_API_KEY environment variable not set."
        }

    # Truncate transcript if too long
    if len(transcript) > MAX_TRANSCRIPT_SIZE:
        transcript = transcript[:MAX_TRANSCRIPT_SIZE] + "\n\n[Transcript truncated due to length...]"

    try:
        client = Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT.format(transcript=transcript)
                }
            ]
        )

        summary = message.content[0].text

        return {
            "success": True,
            "summary": summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate summary: {str(e)}"
        }


if __name__ == "__main__":
    # Quick test
    test_transcript = "This is a test transcript about technology and startups."
    result = summarize_transcript(test_transcript)
    print(result)
