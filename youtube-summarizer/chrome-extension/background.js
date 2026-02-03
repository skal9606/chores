// Background service worker for YouTube Transcript Summarizer

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('YouTube Transcript Summarizer extension installed');
});

// Handle messages if needed for cross-origin requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'fetchWithCors') {
        fetch(request.url, request.options)
            .then(response => response.json())
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // Keep the message channel open for async response
    }
});
