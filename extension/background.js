/**
 * BrowserShield-Pro Background Service Worker (Manifest V3)
 * Manages badge state, tab monitoring coordination, and local storage.
 */

// Initialize defaults on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    autoScanEnabled: false,
    continuousMonitoring: false,
    alertThreshold: 'suspicious',
    scanHistory: []
  });
  console.log('BrowserShield-Pro service worker initialized.');
});

// Update badge appearance based on risk level
function updateBadge(tabId, verdict) {
  if (!tabId) return;

  let text = '';
  let color = '#10b981'; // green

  switch (verdict) {
    case 'DANGEROUS':
      text = 'ALERT';
      color = '#ef4444'; // red
      break;
    case 'SUSPICIOUS':
      text = '!';
      color = '#f59e0b'; // amber
      break;
    case 'UNSURE':
      text = '?';
      color = '#6366f1'; // indigo
      break;
    case 'SAFE':
    default:
      text = 'OK';
      color = '#10b981'; // emerald green
      break;
  }

  chrome.action.setBadgeText({ tabId, text });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
}

// Listen for messages from popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'UPDATE_BADGE') {
    const tabId = request.tabId || (sender.tab && sender.tab.id);
    if (tabId) {
      updateBadge(tabId, request.verdict);
    }
    sendResponse({ success: true });
  } else if (request.type === 'OPEN_DEMO') {
    chrome.tabs.create({ url: chrome.runtime.getURL('demo.html') });
    sendResponse({ success: true });
  }
  return true;
});
