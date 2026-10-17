/**
 * Sheilded page hook (runs in the page's MAIN world).
 * Content scripts live in an isolated world, so wrapping fetch/XHR there never sees the
 * page's own requests. This hook reports each request to content.js via a DOM event.
 */
(function () {
  if (window.__SheildedHooked) return;
  window.__SheildedHooked = true;

  function report(method, url) {
    try {
      const u = new URL(url, location.href);
      window.dispatchEvent(new CustomEvent('sheilded-request', {
        detail: { method: String(method || 'GET').toUpperCase(), host: u.hostname }
      }));
    } catch (_) {}
  }

  const origFetch = window.fetch;
  if (origFetch) {
    window.fetch = function (input, init) {
      try {
        const isReq = typeof Request !== 'undefined' && input instanceof Request;
        const url = isReq ? input.url : String(input);
        const method = (init && init.method) || (isReq ? input.method : 'GET');
        report(method, url);
      } catch (_) {}
      return origFetch.apply(this, arguments);
    };
  }

  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    report(method, url);
    return origOpen.apply(this, arguments);
  };

  const origBeacon = navigator.sendBeacon;
  if (origBeacon) {
    navigator.sendBeacon = function (url) {
      report('POST', url);
      return origBeacon.apply(this, arguments);
    };
  }
})();
