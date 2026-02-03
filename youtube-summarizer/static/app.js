// DOM elements
const urlInput = document.getElementById('youtube-url');
const summarizeBtn = document.getElementById('summarize-btn');
const downloadBtn = document.getElementById('download-btn');
const btnText = summarizeBtn.querySelector('.btn-text');
const btnLoading = summarizeBtn.querySelector('.btn-loading');
const errorMessage = document.getElementById('error-message');
const result = document.getElementById('result');
const videoLink = document.getElementById('video-link');
const summaryContent = document.getElementById('summary-content');
const transcriptContent = document.getElementById('transcript-content');

// Store current video data for download
let currentVideoData = null;

// Event listeners (no inline handlers for CSP compliance)
summarizeBtn.addEventListener('click', summarize);
downloadBtn.addEventListener('click', downloadTranscript);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        summarize();
    }
});

// Escape HTML entities to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function summarize() {
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    // Show loading state
    setLoading(true);
    hideError();
    result.style.display = 'none';

    try {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!data.success) {
            showError(data.error || 'An error occurred');
            return;
        }

        // Validate video_id format (11 chars, alphanumeric + dash + underscore)
        if (!/^[a-zA-Z0-9_-]{11}$/.test(data.video_id)) {
            showError('Invalid video ID received');
            return;
        }

        // Store data for download
        currentVideoData = {
            video_id: data.video_id,
            transcript: data.transcript,
            summary: data.summary,
            url: url
        };

        // Display results - sanitize before rendering
        videoLink.href = `https://www.youtube.com/watch?v=${encodeURIComponent(data.video_id)}`;

        // Convert markdown to HTML, then sanitize with DOMPurify
        const rawHtml = formatMarkdown(data.summary);
        const sanitizedHtml = DOMPurify.sanitize(rawHtml, {
            ALLOWED_TAGS: ['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'br'],
            ALLOWED_ATTR: []  // No attributes allowed - prevents event handlers
        });
        summaryContent.innerHTML = sanitizedHtml;

        // Transcript uses textContent (already safe)
        transcriptContent.textContent = data.transcript;
        result.style.display = 'block';

    } catch (error) {
        showError('Failed to connect to server. Please try again.');
        console.error(error);
    } finally {
        setLoading(false);
    }
}

function downloadTranscript() {
    if (!currentVideoData) return;

    // Escape for markdown context
    const safeVideoId = currentVideoData.video_id.replace(/[^a-zA-Z0-9_-]/g, '');

    const markdown = `# YouTube Video Transcript

**Video URL:** https://www.youtube.com/watch?v=${safeVideoId}

---

## Summary

${currentVideoData.summary}

---

## Full Transcript

${currentVideoData.transcript}
`;

    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `youtube-transcript-${safeVideoId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function setLoading(loading) {
    summarizeBtn.disabled = loading;
    urlInput.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'inline-flex' : 'none';
}

function showError(message) {
    // Use textContent to prevent XSS in error messages
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function formatMarkdown(text) {
    // First, escape any HTML in the input to prevent XSS
    text = escapeHtml(text);

    // Process line by line for better control
    const lines = text.split('\n');
    let html = '';
    let inList = false;
    let listType = null;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Bold (using escaped ** markers)
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic (but not bullet points)
        line = line.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

        // Headers
        if (line.match(/^### (.+)$/)) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += line.replace(/^### (.+)$/, '<h4>$1</h4>');
        } else if (line.match(/^## (.+)$/)) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += line.replace(/^## (.+)$/, '<h3>$1</h3>');
        } else if (line.match(/^# (.+)$/)) {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += line.replace(/^# (.+)$/, '<h2>$1</h2>');
        }
        // Bullet points
        else if (line.match(/^[-*] (.+)$/)) {
            if (!inList || listType !== 'ul') {
                if (inList) html += '</ol>';
                html += '<ul>';
                inList = true;
                listType = 'ul';
            }
            html += line.replace(/^[-*] (.+)$/, '<li>$1</li>');
        }
        // Numbered lists
        else if (line.match(/^\d+\. (.+)$/)) {
            if (!inList || listType !== 'ol') {
                if (inList) html += '</ul>';
                html += '<ol>';
                inList = true;
                listType = 'ol';
            }
            html += line.replace(/^\d+\. (.+)$/, '<li>$1</li>');
        }
        // Empty line
        else if (line.trim() === '') {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += '<br>';
        }
        // Regular paragraph
        else {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += '<p>' + line + '</p>';
        }
    }

    // Close any open list
    if (inList) {
        html += listType === 'ul' ? '</ul>' : '</ol>';
    }

    return html;
}
