// Docsend Content Script
// Handles slide detection, navigation, and image URL extraction

/**
 * Check if there's a visible email gate blocking access
 * Only returns true if there's clearly an email form visible and no slides
 */
function isAuthRequired() {
  // Look for visible email input that's actually displayed
  const emailInput = document.querySelector('input[type="email"]');
  if (emailInput) {
    const style = getComputedStyle(emailInput);
    const rect = emailInput.getBoundingClientRect();
    // Check if it's actually visible
    if (style.display !== 'none' && style.visibility !== 'hidden' && rect.height > 0) {
      return true;
    }
  }

  // Check for common gate/prompt containers that are visible
  const gateSelectors = [
    '#link-auth-wall',
    '[data-testid="visitor-auth"]',
    '.visitor-gate',
    '.email-gate',
    '#visitor-form'
  ];

  for (const selector of gateSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      const style = getComputedStyle(el);
      if (style.display !== 'none' && style.visibility !== 'hidden') {
        return true;
      }
    }
  }

  return false;
}

/**
 * Get slide count and current position
 */
function getSlideInfo() {
  // Method 1: Parse the page label element (e.g., "1 / 24" or "1 of 24")
  const pageLabelSelectors = [
    '.page-label',
    '[class*="page-label"]',
    '[class*="pageLabel"]',
    '[class*="PageLabel"]',
    '[class*="page-number"]',
    '[class*="pageNumber"]',
    '[class*="slide-counter"]',
    '[class*="pagination"]',
    '[data-testid*="page"]'
  ];

  for (const selector of pageLabelSelectors) {
    const el = document.querySelector(selector);
    if (el) {
      const text = el.textContent;
      const match = text.match(/(\d+)\s*(?:\/|of|\/\s*)\s*(\d+)/i);
      if (match) {
        return {
          current: parseInt(match[1]),
          total: parseInt(match[2])
        };
      }
    }
  }

  // Method 2: Search all text for "X of Y" or "X / Y" pattern
  const bodyText = document.body.innerText;
  const pagePatterns = bodyText.match(/\b(\d+)\s*(?:\/|of)\s*(\d+)\b/i);
  if (pagePatterns) {
    const current = parseInt(pagePatterns[1]);
    const total = parseInt(pagePatterns[2]);
    // Sanity check - total should be reasonable for a presentation
    if (total >= 1 && total <= 500 && current >= 1 && current <= total) {
      return { current, total };
    }
  }

  // Method 3: Count thumbnail/page elements
  const thumbnailSelectors = [
    '[class*="thumbnail"]',
    '[class*="page-thumb"]',
    '[class*="sidebar"] [class*="page"]',
    '[data-page]',
    '[data-slide]',
    '[class*="nav-item"]'
  ];

  for (const selector of thumbnailSelectors) {
    const thumbnails = document.querySelectorAll(selector);
    if (thumbnails.length > 1) {
      return { current: 1, total: thumbnails.length };
    }
  }

  // Method 4: Try to find data in script tags (some SPAs store data there)
  const scripts = document.querySelectorAll('script:not([src])');
  for (const script of scripts) {
    const content = script.textContent;
    // Look for page count in JSON-like structures
    const pageCountMatch = content.match(/"(?:pageCount|page_count|totalPages|total_pages|numPages)":\s*(\d+)/);
    if (pageCountMatch) {
      return { current: 1, total: parseInt(pageCountMatch[1]) };
    }
  }

  // Method 5: Check for images that look like slides
  const slideImages = document.querySelectorAll('img[src*="page"], img[src*="slide"], [class*="document"] img');
  if (slideImages.length === 1) {
    // Single slide visible - try to get count from elsewhere or assume at least 1
    console.log('Docsend to PDF: Found slide image, but cannot determine total count');
  }

  return null;
}

/**
 * Get the base URL for API requests
 */
function getBaseUrl() {
  // Remove trailing slash and any hash/query params
  return window.location.href.split('#')[0].split('?')[0].replace(/\/$/, '');
}

/**
 * Fetch image URL for a specific slide from the page_data endpoint
 */
async function fetchSlideImageUrl(slideNumber) {
  const baseUrl = getBaseUrl();
  const endpoint = `${baseUrl}/page_data/${slideNumber}`;

  try {
    const response = await fetch(endpoint, {
      credentials: 'include',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // The imageUrl might be in different fields depending on Docsend version
    return data.imageUrl || data.image_url || data.url || data.src;
  } catch (error) {
    console.error(`Failed to fetch slide ${slideNumber}:`, error);
    return null;
  }
}

/**
 * Fetch all slide image URLs
 */
async function fetchAllSlideUrls(totalSlides, onProgress) {
  const urls = [];

  for (let i = 1; i <= totalSlides; i++) {
    const url = await fetchSlideImageUrl(i);
    if (url) {
      urls.push(url);
    } else {
      // If API method fails, return null to signal fallback needed
      return null;
    }

    if (onProgress) {
      onProgress(i, totalSlides);
    }
  }

  return urls;
}

/**
 * Navigate to a specific slide
 */
function goToSlide(slideNumber) {
  // Method 1: Click on thumbnail
  const thumbnail = document.querySelector(`[data-page="${slideNumber}"], [data-slide="${slideNumber}"]`);
  if (thumbnail) {
    thumbnail.click();
    return true;
  }

  // Method 2: Use URL hash
  const url = new URL(window.location.href);
  url.hash = `page=${slideNumber}`;
  window.history.pushState({}, '', url);
  window.dispatchEvent(new HashChangeEvent('hashchange'));

  return true;
}

/**
 * Navigate to next slide using keyboard event
 */
function goToNextSlide() {
  document.dispatchEvent(new KeyboardEvent('keydown', {
    key: 'ArrowRight',
    code: 'ArrowRight',
    keyCode: 39,
    which: 39,
    bubbles: true
  }));
}

/**
 * Wait for slide to fully load
 */
function waitForSlideLoad() {
  return new Promise((resolve) => {
    // Check for loading indicators
    const checkLoaded = () => {
      const loader = document.querySelector('.loading-indicator, .spinner, [class*="loading"]');
      if (!loader || getComputedStyle(loader).display === 'none' || getComputedStyle(loader).visibility === 'hidden') {
        // Also wait for main image to load
        const slideImg = document.querySelector('[class*="slide"] img, [class*="page"] img, .document-page img');
        if (slideImg) {
          if (slideImg.complete) {
            resolve();
            return;
          }
          slideImg.addEventListener('load', () => resolve(), { once: true });
          // Fallback timeout in case image is already loaded but complete is false
          setTimeout(resolve, 500);
          return;
        }
        resolve();
        return;
      }
      requestAnimationFrame(checkLoaded);
    };

    // Fallback timeout
    setTimeout(resolve, 2000);
    checkLoaded();
  });
}

/**
 * Get document title for filename
 */
function getDocumentTitle() {
  // Try various selectors for document title
  const titleEl = document.querySelector(
    '[class*="document-title"], [class*="doc-title"], h1, [class*="header"] h2'
  );

  if (titleEl) {
    return titleEl.textContent.trim();
  }

  // Fallback to page title
  const pageTitle = document.title.replace(/\s*[-|]\s*DocSend.*$/i, '').trim();
  return pageTitle || 'docsend-presentation';
}

// Message listener for communication with popup and service worker
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_SLIDE_INFO') {
    // First, try to get slide info - if we can see slides, we have access
    const slideInfo = getSlideInfo();

    if (slideInfo) {
      // We found slides - we have access
      sendResponse({
        currentSlide: slideInfo.current,
        totalSlides: slideInfo.total,
        documentTitle: getDocumentTitle()
      });
      return true;
    }

    // No slides found - check if it's because of an auth gate
    if (isAuthRequired()) {
      sendResponse({ authRequired: true });
      return true;
    }

    // No slides and no obvious auth gate - might be loading or different page structure
    sendResponse({ error: 'Could not detect slides on this page. Try refreshing.' });
    return true;
  }

  if (message.type === 'FETCH_SLIDE_URLS') {
    fetchAllSlideUrls(message.totalSlides, (current, total) => {
      chrome.runtime.sendMessage({
        type: 'FETCH_PROGRESS',
        current,
        total
      });
    }).then(urls => {
      sendResponse({ urls });
    }).catch(error => {
      sendResponse({ error: error.message });
    });
    return true; // Keep channel open for async response
  }

  if (message.type === 'GO_TO_SLIDE') {
    goToSlide(message.slideNumber);
    waitForSlideLoad().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (message.type === 'GO_TO_NEXT_SLIDE') {
    goToNextSlide();
    waitForSlideLoad().then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (message.type === 'GET_DOCUMENT_TITLE') {
    sendResponse({ title: getDocumentTitle() });
    return true;
  }
});

// Debug function to help troubleshoot
function getDebugInfo() {
  const slideInfo = getSlideInfo();
  const authRequired = isAuthRequired();
  const emailInputs = document.querySelectorAll('input[type="email"]');
  const visibleEmailInputs = Array.from(emailInputs).filter(el => {
    const style = getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden';
  });

  return {
    url: window.location.href,
    slideInfo,
    authRequired,
    emailInputCount: emailInputs.length,
    visibleEmailInputCount: visibleEmailInputs.length,
    bodyTextSample: document.body.innerText.substring(0, 500),
    pageTitle: document.title
  };
}

// Log that content script is loaded
console.log('Docsend to PDF: Content script loaded');
console.log('Docsend to PDF: Debug info:', getDebugInfo());
