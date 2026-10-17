/**
 * BrowserShield-Pro Content Script
 * Passively and securely monitors per-tab runtime telemetry:
 * - Event-loop lag (requestAnimationFrame and high-resolution timer delays)
 * - DOM mutation rate (MutationObserver)
 * - Network requests and POST activity (PerformanceObserver + Resource Timing)
 * - Page visibility and idle interaction tracking
 */

(function () {
  if (window.__BrowserShieldTelemetryInitialized) return;
  window.__BrowserShieldTelemetryInitialized = true;

  const startTime = performance.now();
  let domMutationCount = 0;
  let accumulatedLagMs = 0;
  let lastTick = performance.now();
  let visibilityChangeCount = 0;
  let lastUserActivity = performance.now();
  let idleMs = 0;

  // Intercepted POST tracking
  let postCount = 0;
  const contactedDomains = new Set();

  // 1. DOM Mutation Monitoring
  try {
    const observer = new MutationObserver((mutations) => {
      domMutationCount += mutations.length;
    });
    if (document.documentElement) {
      observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        characterData: false
      });
    }
  } catch (e) {
    console.warn('BrowserShield DOM Observer error:', e);
  }

  // 2. High-precision Event Loop Lag Measurement
  const EXPECTED_INTERVAL = 100;
  function measureLag() {
    const now = performance.now();
    const delta = now - lastTick;
    if (delta > EXPECTED_INTERVAL + 15) {
      // Delay beyond baseline interval indicates main thread blockage
      accumulatedLagMs += (delta - EXPECTED_INTERVAL);
    }
    lastTick = now;
    setTimeout(measureLag, EXPECTED_INTERVAL);
  }
  setTimeout(measureLag, EXPECTED_INTERVAL);

  // 3. User Activity / Idle Tracking
  const activityEvents = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart'];
  function recordActivity() {
    lastUserActivity = performance.now();
  }
  activityEvents.forEach((evt) => {
    window.addEventListener(evt, recordActivity, { passive: true, capture: true });
  });

  // Track idle time
  setInterval(() => {
    const now = performance.now();
    if (now - lastUserActivity > 2000) {
      idleMs += 1000;
    }
  }, 1000);

  // 4. Visibility State
  document.addEventListener('visibilitychange', () => {
    visibilityChangeCount++;
  });

  // 5. Network & Resource Monitoring via PerformanceObserver
  function scanResources() {
    try {
      const resources = performance.getEntriesByType('resource');
      resources.forEach((entry) => {
        try {
          const url = new URL(entry.name);
          contactedDomains.add(url.hostname);
        } catch (err) {
          // relative or custom scheme
        }
      });
      return resources.length;
    } catch (e) {
      return 0;
    }
  }

  // Intercept fetch/XHR in page for accurate POST counting
  try {
    const origFetch = window.fetch;
    if (origFetch) {
      window.fetch = function (...args) {
        try {
          const opts = args[1];
          if (opts && opts.method && opts.method.toUpperCase() === 'POST') {
            postCount++;
          }
          if (args[0] && typeof args[0] === 'string') {
            const u = new URL(args[0], window.location.href);
            contactedDomains.add(u.hostname);
          }
        } catch (_) {}
        return origFetch.apply(this, args);
      };
    }

    const origOpen = XMLHttpRequest.prototype.open;
    if (origOpen) {
      XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        try {
          if (method && method.toUpperCase() === 'POST') {
            postCount++;
          }
          if (url) {
            const u = new URL(url, window.location.href);
            contactedDomains.add(u.hostname);
          }
        } catch (_) {}
        return origOpen.apply(this, [method, url, ...rest]);
      };
    }
  } catch (e) {}

  // Requests made by the page itself arrive from page_hook.js (MAIN world) as DOM events
  window.addEventListener('sheilded-request', (e) => {
    const d = e.detail || {};
    if (d.method === 'POST') postCount++;
    if (d.host) contactedDomains.add(d.host);
  });

  // Function to compile current snapshot
  function getTelemetrySnapshot() {
    const now = performance.now();
    const uptimeMs = Math.max(now - startTime, 100);
    const networkCount = Math.max(scanResources(), postCount);

    contactedDomains.add(window.location.hostname || 'localhost');

    const totalSec = uptimeMs / 1000.0;
    const idleSec = idleMs / 1000.0;
    const idleRatio = Math.min(Math.max(idleSec / Math.max(totalSec, 1), 0.0), 1.0);

    return {
      page_uptime_ms: uptimeMs,
      event_loop_lag_ms: accumulatedLagMs,
      dom_mutation_count: domMutationCount,
      network_request_count: networkCount,
      post_request_count: postCount,
      unique_domains_contacted: contactedDomains.size,
      idle_ratio: idleRatio,
      visibility_hidden: document.hidden ? 1 : 0,
      visibility_changes: visibilityChangeCount,
      url: window.location.href,
      title: document.title || window.location.hostname
    };
  }

  // 6. Chrome Message Listener
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.type === 'GET_TELEMETRY') {
        const telemetry = getTelemetrySnapshot();
        sendResponse({ success: true, telemetry });
      } else if (request.type === 'RESET_TELEMETRY') {
        domMutationCount = 0;
        accumulatedLagMs = 0;
        postCount = 0;
        sendResponse({ success: true });
      }
      return true; // Keep message port open for async response
    });
  }

  // Expose for demo pages
  window.__getBrowserShieldTelemetry = getTelemetrySnapshot;
})();
