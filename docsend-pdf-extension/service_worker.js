// Docsend to PDF Service Worker
// Orchestrates slide capture and PDF generation

// Import PDF generation library
importScripts('lib/pdf-lib.min.js');

const TIMING = {
  slideTransitionDelay: 800,
  screenshotCooldown: 500,
  networkTimeout: 15000
};

let activeCapture = null;

/**
 * Fetch image as ArrayBuffer with retry logic
 */
async function fetchImageWithRetry(url, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        credentials: 'include'
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '2');
        await delay(retryAfter * 1000 * attempt);
        continue;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.arrayBuffer();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await delay(1000 * attempt);
    }
  }
}

/**
 * Delay helper
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Capture visible tab as screenshot
 */
async function captureScreenshot(tabId) {
  return new Promise((resolve, reject) => {
    chrome.tabs.captureVisibleTab(null, {
      format: 'png',
      quality: 100
    }, (dataUrl) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(dataUrl);
      }
    });
  });
}

/**
 * Convert data URL to ArrayBuffer
 */
function dataUrlToArrayBuffer(dataUrl) {
  const base64 = dataUrl.split(',')[1];
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Send message to content script
 */
async function sendToContentScript(tabId, message) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

/**
 * Send progress update to popup
 */
function sendProgressUpdate(current, total) {
  chrome.runtime.sendMessage({
    type: 'PROGRESS_UPDATE',
    current,
    total
  }).catch(() => {
    // Popup might be closed, ignore
  });
}

/**
 * Send completion message to popup
 */
function sendComplete() {
  chrome.runtime.sendMessage({
    type: 'CAPTURE_COMPLETE'
  }).catch(() => {});
}

/**
 * Send error message to popup
 */
function sendError(error) {
  chrome.runtime.sendMessage({
    type: 'CAPTURE_ERROR',
    error: error.message || String(error)
  }).catch(() => {});
}

/**
 * Try to fetch slide URLs via API method
 */
async function fetchSlideUrlsViaApi(tabId, totalSlides) {
  try {
    const response = await sendToContentScript(tabId, {
      type: 'FETCH_SLIDE_URLS',
      totalSlides
    });

    if (response.urls && response.urls.length === totalSlides) {
      return response.urls;
    }
  } catch (error) {
    console.log('API method failed, will use screenshot fallback:', error);
  }
  return null;
}

/**
 * Capture slides via screenshot method (fallback)
 */
async function captureViaScreenshots(tabId, totalSlides) {
  const screenshots = [];

  // Go to first slide
  await sendToContentScript(tabId, { type: 'GO_TO_SLIDE', slideNumber: 1 });
  await delay(TIMING.slideTransitionDelay);

  for (let i = 1; i <= totalSlides; i++) {
    sendProgressUpdate(i, totalSlides);

    // Capture screenshot
    const dataUrl = await captureScreenshot(tabId);
    screenshots.push(dataUrlToArrayBuffer(dataUrl));

    if (i < totalSlides) {
      // Navigate to next slide
      await sendToContentScript(tabId, { type: 'GO_TO_NEXT_SLIDE' });
      await delay(TIMING.slideTransitionDelay);
      // Respect rate limit
      await delay(TIMING.screenshotCooldown);
    }
  }

  return screenshots;
}

/**
 * Fetch images from URLs
 */
async function fetchImagesFromUrls(urls) {
  const images = [];

  for (let i = 0; i < urls.length; i++) {
    sendProgressUpdate(i + 1, urls.length);
    const imageData = await fetchImageWithRetry(urls[i]);
    images.push(imageData);
  }

  return images;
}

/**
 * Generate PDF from image data
 */
async function generatePdf(imageDataArray) {
  const { PDFDocument } = PDFLib;
  const pdfDoc = await PDFDocument.create();

  for (const imageData of imageDataArray) {
    // Determine image type and embed
    const bytes = new Uint8Array(imageData);
    let image;

    // Check PNG signature
    if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47) {
      image = await pdfDoc.embedPng(imageData);
    } else {
      // Assume JPEG
      image = await pdfDoc.embedJpg(imageData);
    }

    // Add page sized to image dimensions
    const page = pdfDoc.addPage([image.width, image.height]);

    // Draw image to fill the page
    page.drawImage(image, {
      x: 0,
      y: 0,
      width: image.width,
      height: image.height
    });
  }

  return await pdfDoc.save();
}

/**
 * Trigger download of PDF
 */
async function downloadPdf(pdfBytes, filename) {
  // Create blob URL
  const blob = new Blob([pdfBytes], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);

  // Sanitize filename
  const safeName = filename
    .replace(/[<>:"/\\|?*]/g, '')
    .replace(/\s+/g, '-')
    .substring(0, 100) || 'docsend-presentation';

  // Trigger download
  await chrome.downloads.download({
    url: url,
    filename: `${safeName}.pdf`,
    saveAs: true
  });

  // Cleanup blob URL after a delay
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

/**
 * Main capture workflow
 */
async function startCapture(tabId, totalSlides) {
  if (activeCapture) {
    sendError(new Error('A capture is already in progress'));
    return;
  }

  activeCapture = { tabId, totalSlides };

  try {
    // Get document title for filename
    const titleResponse = await sendToContentScript(tabId, { type: 'GET_DOCUMENT_TITLE' });
    const documentTitle = titleResponse.title || 'docsend-presentation';

    let imageDataArray;

    // Try API method first
    const urls = await fetchSlideUrlsViaApi(tabId, totalSlides);

    if (urls) {
      // API method succeeded - fetch images from URLs
      console.log('Using API method');
      imageDataArray = await fetchImagesFromUrls(urls);
    } else {
      // Fall back to screenshot method
      console.log('Using screenshot fallback');
      imageDataArray = await captureViaScreenshots(tabId, totalSlides);
    }

    // Generate PDF
    sendProgressUpdate(totalSlides, totalSlides);
    const pdfBytes = await generatePdf(imageDataArray);

    // Download
    await downloadPdf(pdfBytes, documentTitle);

    sendComplete();

  } catch (error) {
    console.error('Capture failed:', error);
    sendError(error);
  } finally {
    activeCapture = null;
  }
}

// Message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'START_CAPTURE') {
    startCapture(message.tabId, message.totalSlides);
    sendResponse({ started: true });
    return true;
  }

  if (message.type === 'FETCH_PROGRESS') {
    // Forward progress from content script to popup
    sendProgressUpdate(message.current, message.total);
    return true;
  }
});

console.log('Docsend to PDF: Service worker loaded');
