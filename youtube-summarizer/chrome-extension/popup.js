// Default backend URL - your deployed Render instance
const DEFAULT_BACKEND_URL = 'https://youtube-summarizer-vuui.onrender.com';

let currentVideoId = null;
let currentVideoData = null;

// DOM elements
const notYoutubeDiv = document.getElementById('not-youtube');
const videoDetectedDiv = document.getElementById('video-detected');
const currentVideoIdSpan = document.getElementById('current-video-id');
const summarizeBtn = document.getElementById('summarize-btn');
const downloadBtn = document.getElementById('download-btn');
const btnText = summarizeBtn.querySelector('.btn-text');
const btnLoading = summarizeBtn.querySelector('.btn-loading');
const errorMessage = document.getElementById('error-message');
const resultDiv = document.getElementById('result');
const summaryContent = document.getElementById('summary-content');
const backendUrlInput = document.getElementById('backend-url');
const saveSettingsBtn = document.getElementById('save-settings');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Load saved backend URL
    const stored = await chrome.storage.sync.get(['backendUrl']);
    if (stored.backendUrl) {
        backendUrlInput.value = stored.backendUrl;
    } else {
        backendUrlInput.value = DEFAULT_BACKEND_URL;
    }

    // Check current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab.url && tab.url.includes('youtube.com/watch')) {
        const videoId = extractVideoId(tab.url);
        if (videoId && validateVideoId(videoId)) {
            currentVideoId = videoId;
            currentVideoIdSpan.textContent = videoId;
            videoDetectedDiv.style.display = 'block';
            notYoutubeDiv.style.display = 'none';
        } else {
            showNotYoutube();
        }
    } else {
        showNotYoutube();
    }
});

// Event listeners
summarizeBtn.addEventListener('click', summarize);
downloadBtn.addEventListener('click', downloadTranscript);
saveSettingsBtn.addEventListener('click', saveSettings);

function showNotYoutube() {
    notYoutubeDiv.style.display = 'block';
    videoDetectedDiv.style.display = 'none';
}

// Validate video ID format (11 alphanumeric + dash + underscore)
function validateVideoId(videoId) {
    return /^[a-zA-Z0-9_-]{11}$/.test(videoId);
}

function extractVideoId(url) {
    const patterns = [
        /[?&]v=([a-zA-Z0-9_-]{11})/,
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,
        /embed\/([a-zA-Z0-9_-]{11})/
    ];

    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && validateVideoId(match[1])) return match[1];
    }
    return null;
}

function getBackendUrl() {
    return backendUrlInput.value.trim() || DEFAULT_BACKEND_URL;
}

// Escape HTML entities to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Simple HTML sanitizer - only allows safe tags
function sanitizeHtml(html) {
    const allowedTags = ['h2', 'h3', 'h4', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'br'];
    const tagPattern = /<\/?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>/gi;

    return html.replace(tagPattern, (match, tagName) => {
        const lowerTag = tagName.toLowerCase();
        if (allowedTags.includes(lowerTag)) {
            // Only allow the tag itself, strip all attributes
            if (match.startsWith('</')) {
                return `</${lowerTag}>`;
            } else {
                return `<${lowerTag}>`;
            }
        }
        // Remove disallowed tags entirely
        return '';
    });
}

async function summarize() {
    if (!currentVideoId || !validateVideoId(currentVideoId)) return;

    setLoading(true);
    hideError();
    resultDiv.style.display = 'none';

    try {
        const backendUrl = getBackendUrl();
        const response = await fetch(`${backendUrl}/summarize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: `https://www.youtube.com/watch?v=${currentVideoId}` })
        });

        const data = await response.json();

        if (!data.success) {
            showError(data.error || 'An error occurred');
            return;
        }

        // Validate returned video ID
        if (!validateVideoId(data.video_id)) {
            showError('Invalid response from server');
            return;
        }

        // Store data for download
        currentVideoData = {
            video_id: data.video_id,
            transcript: data.transcript,
            summary: data.summary
        };

        // Display summary with XSS protection
        const rawHtml = formatMarkdown(data.summary);
        const sanitizedHtml = sanitizeHtml(rawHtml);
        summaryContent.innerHTML = sanitizedHtml;
        resultDiv.style.display = 'block';
        downloadBtn.disabled = false;

    } catch (error) {
        showError('Failed to connect to server. Check your backend URL in settings.');
        console.error(error);
    } finally {
        setLoading(false);
    }
}

function downloadTranscript() {
    if (!currentVideoData) return;

    // Sanitize video ID for filename
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

    chrome.downloads.download({
        url: url,
        filename: `youtube-transcript-${safeVideoId}.md`,
        saveAs: true
    });
}

async function saveSettings() {
    const url = backendUrlInput.value.trim();
    await chrome.storage.sync.set({ backendUrl: url });
    saveSettingsBtn.textContent = 'Saved!';
    setTimeout(() => {
        saveSettingsBtn.textContent = 'Save';
    }, 1500);
}

function setLoading(loading) {
    summarizeBtn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'inline-flex' : 'none';
}

function showError(message) {
    // Use textContent to prevent XSS
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function formatMarkdown(text) {
    // First, escape any HTML in the input to prevent XSS
    text = escapeHtml(text);

    const lines = text.split('\n');
    let html = '';
    let inList = false;
    let listType = null;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // Bold
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic
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
            html += line.replace(/^# (.+)$/, '<h3>$1</h3>');
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
        }
        // Regular paragraph
        else {
            if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
            html += '<p>' + line + '</p>';
        }
    }

    if (inList) {
        html += listType === 'ul' ? '</ul>' : '</ol>';
    }

    return html;
}
