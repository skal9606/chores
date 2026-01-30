const States = {
  READY: 'ready-state',
  PROGRESS: 'progress-state',
  COMPLETE: 'complete-state',
  ERROR: 'error-state',
  NOT_DOCSEND: 'not-docsend-state',
  AUTH_REQUIRED: 'auth-required-state'
};

let currentTabId = null;
let slideCount = 0;

function showState(stateName) {
  Object.values(States).forEach(state => {
    document.getElementById(state).classList.add('hidden');
  });
  document.getElementById(stateName).classList.remove('hidden');
}

function updateProgress(current, total) {
  const percent = Math.round((current / total) * 100);
  document.getElementById('progress-fill').style.width = `${percent}%`;
  document.getElementById('progress-text').textContent = `Slide ${current} of ${total}`;
}

function showError(message) {
  document.getElementById('error-message').textContent = message;
  showState(States.ERROR);
}

async function initPopup() {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTabId = tab.id;

    // Check if on Docsend
    if (!tab.url || !tab.url.includes('docsend.com/view/')) {
      showState(States.NOT_DOCSEND);
      return;
    }

    // Request slide info from content script
    const response = await chrome.tabs.sendMessage(currentTabId, { type: 'GET_SLIDE_INFO' });

    if (response.authRequired) {
      showState(States.AUTH_REQUIRED);
      return;
    }

    if (response.error) {
      showError(response.error);
      return;
    }

    slideCount = response.totalSlides;
    document.getElementById('slide-info').textContent = `Detected ${slideCount} slides`;
    document.getElementById('download-btn').disabled = false;
    showState(States.READY);

  } catch (error) {
    // Content script not loaded yet
    if (error.message?.includes('Receiving end does not exist')) {
      showError('Please refresh the Docsend page and try again.');
    } else {
      showError('Could not connect to Docsend page.');
    }
  }
}

async function startDownload() {
  showState(States.PROGRESS);
  updateProgress(0, slideCount);

  try {
    // Send message to service worker to start capture
    chrome.runtime.sendMessage({
      type: 'START_CAPTURE',
      tabId: currentTabId,
      totalSlides: slideCount
    });
  } catch (error) {
    showError(error.message || 'Failed to start download.');
  }
}

// Listen for progress updates from service worker
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'PROGRESS_UPDATE') {
    updateProgress(message.current, message.total);
  } else if (message.type === 'CAPTURE_COMPLETE') {
    showState(States.COMPLETE);
  } else if (message.type === 'CAPTURE_ERROR') {
    showError(message.error);
  }
});

// Event listeners
document.getElementById('download-btn').addEventListener('click', startDownload);
document.getElementById('download-again-btn').addEventListener('click', () => {
  showState(States.READY);
  startDownload();
});
document.getElementById('retry-btn').addEventListener('click', () => {
  showState(States.READY);
  initPopup();
});

// Initialize
document.addEventListener('DOMContentLoaded', initPopup);
