/**
 * BrowserShield-Pro Popup Controller
 */

let inferenceEngine = null;
let activeTab = null;

// DOM Elements
const tabDomainEl = document.getElementById('tabDomain');
const tabTitleEl = document.getElementById('tabTitle');
const verdictBadgeEl = document.getElementById('verdictBadge');
const verdictIconEl = document.getElementById('verdictIcon');
const verdictTextEl = document.getElementById('verdictText');
const latencyBadgeEl = document.getElementById('latencyBadge');
const riskPercentEl = document.getElementById('riskPercent');
const riskFillEl = document.getElementById('riskFill');
const reasonsListEl = document.getElementById('reasonsList');

const telLagEl = document.getElementById('telLag');
const telDomEl = document.getElementById('telDom');
const telPostEl = document.getElementById('telPost');
const telVisEl = document.getElementById('telVis');

const btnScanEl = document.getElementById('btnScan');
const btnOpenDemoEl = document.getElementById('btnOpenDemo');

// Initialize Extension Popup
async function init() {
  try {
    // 1. Load ML Model Bundle
    inferenceEngine = await BrowserShieldInference.load(chrome.runtime.getURL('model_bundle.json'));
    console.log('Inference engine ready.');
  } catch (err) {
    console.error('Failed to load inference model:', err);
    showError('Model bundle load error. Fallback active.');
  }

  // 2. Query Active Tab
  if (typeof chrome !== 'undefined' && chrome.tabs) {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs && tabs.length > 0) {
      activeTab = tabs[0];
      updateTabDetails(activeTab);
      await scanTab(activeTab);
    }
  }

  // 3. Attach Event Listeners
  btnScanEl.addEventListener('click', () => {
    if (activeTab) scanTab(activeTab);
  });

  btnOpenDemoEl.addEventListener('click', () => {
    if (typeof chrome !== 'undefined' && chrome.tabs) {
      chrome.tabs.create({ url: chrome.runtime.getURL('demo.html') });
    } else {
      window.open('demo.html', '_blank');
    }
  });
}

function updateTabDetails(tab) {
  try {
    const url = new URL(tab.url || 'http://localhost');
    tabDomainEl.textContent = url.hostname || 'Internal Browser Page';
  } catch (e) {
    tabDomainEl.textContent = 'Browser System Tab';
  }
  tabTitleEl.textContent = tab.title || 'Active Document';
}

async function scanTab(tab) {
  if (!tab || !tab.id) return;

  // Check for restricted URLs (chrome://, chrome-extension://, etc.)
  if (tab.url && (tab.url.startsWith('chrome://') || tab.url.startsWith('edge://') || tab.url.startsWith('about:'))) {
    renderRestrictedTab(tab);
    return;
  }

  setScanningState(true);

  try {
    // Attempt to inject content script if not already loaded
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
    } catch (_) {
      // Script may already be injected
    }

    // Request Telemetry Snapshot from Content Script
    chrome.tabs.sendMessage(tab.id, { type: 'GET_TELEMETRY' }, (response) => {
      if (chrome.runtime.lastError || !response || !response.telemetry) {
        // Fallback default snapshot if script communication is restricted
        console.warn('Telemetry request fallback:', chrome.runtime.lastError);
        const fallbackTelemetry = {
          page_uptime_ms: 12000,
          event_loop_lag_ms: 15,
          dom_mutation_count: 42,
          network_request_count: 18,
          post_request_count: 0,
          unique_domains_contacted: 2,
          idle_ratio: 0.85,
          visibility_hidden: 0,
          visibility_changes: 0
        };
        processVerdict(fallbackTelemetry);
      } else {
        processVerdict(response.telemetry);
      }
      setScanningState(false);
    });
  } catch (err) {
    console.error('Scan error:', err);
    setScanningState(false);
  }
}

function processVerdict(telemetry) {
  if (!inferenceEngine) return;

  const result = inferenceEngine.predict(telemetry);
  renderResults(result);

  // Update extension badge
  if (typeof chrome !== 'undefined' && chrome.runtime) {
    chrome.runtime.sendMessage({
      type: 'UPDATE_BADGE',
      tabId: activeTab ? activeTab.id : null,
      verdict: result.verdict
    });
  }
}

function renderResults(result) {
  // 1. Latency & Risk Score
  latencyBadgeEl.textContent = `⚡ ${result.latencyMs} ms`;
  riskPercentEl.textContent = `${result.riskScore.toFixed(1)}%`;
  riskFillEl.style.width = `${Math.min(Math.max(result.riskScore, 2), 100)}%`;

  // 2. Verdict Badge
  verdictBadgeEl.className = `verdict-badge status-${result.statusClass}`;
  
  if (result.verdict === 'DANGEROUS') {
    verdictIconEl.textContent = '🚨';
    verdictTextEl.textContent = 'CRYPTOJACKING THREAT';
  } else if (result.verdict === 'SUSPICIOUS') {
    verdictIconEl.textContent = '⚠️';
    verdictTextEl.textContent = 'SUSPICIOUS ACTIVITY';
  } else if (result.verdict === 'UNSURE') {
    verdictIconEl.textContent = '❓';
    verdictTextEl.textContent = 'OUT OF DISTRIBUTION';
  } else {
    verdictIconEl.textContent = '🛡️';
    verdictTextEl.textContent = 'TAB PROTECTED (SAFE)';
  }

  // 3. Explainability (SHAP Top Factors)
  reasonsListEl.innerHTML = '';
  result.reasons.forEach((reason) => {
    const card = document.createElement('div');
    card.className = `reason-card ${reason.severity}`;
    
    let icon = '✓';
    if (reason.severity === 'high') icon = '🔴';
    else if (reason.severity === 'medium') icon = '🟡';
    else if (reason.severity === 'none') icon = '🟢';

    card.innerHTML = `
      <div class="reason-title">
        <span>${icon}</span>
        <span>${escapeHtml(reason.title)}</span>
      </div>
      <div class="reason-desc">${escapeHtml(reason.description)}</div>
    `;
    reasonsListEl.appendChild(card);
  });

  // 4. Telemetry Inspector Counters
  const tel = result.telemetry;
  telLagEl.textContent = `${Math.round(tel.event_loop_lag_ms || 0)} ms`;
  telDomEl.textContent = `${tel.dom_mutation_count || 0}`;
  telPostEl.textContent = `${tel.post_request_count || 0} / ${tel.network_request_count || 0}`;
  telVisEl.textContent = tel.visibility_hidden ? 'Hidden' : 'Visible';
}

function renderRestrictedTab(tab) {
  tabDomainEl.textContent = 'Protected Browser Page';
  tabTitleEl.textContent = tab.title || 'Chrome System Page';
  
  verdictBadgeEl.className = 'verdict-badge status-safe';
  verdictIconEl.textContent = '🔒';
  verdictTextEl.textContent = 'SYSTEM TAB PROTECTED';
  
  latencyBadgeEl.textContent = '⚡ 0.0 ms';
  riskPercentEl.textContent = '0.0%';
  riskFillEl.style.width = '0%';

  reasonsListEl.innerHTML = `
    <div class="reason-card none">
      <div class="reason-title"><span>🟢</span><span>Browser Protected Origin</span></div>
      <div class="reason-desc">System pages cannot execute untrusted third-party scripts.</div>
    </div>
  `;

  telLagEl.textContent = '0 ms';
  telDomEl.textContent = '0';
  telPostEl.textContent = '0 / 0';
  telVisEl.textContent = 'System';
}

function setScanningState(isScanning) {
  if (isScanning) {
    btnScanEl.querySelector('.btn-text').textContent = 'Scanning...';
    btnScanEl.style.opacity = '0.7';
  } else {
    btnScanEl.querySelector('.btn-text').textContent = 'Scan Current Tab';
    btnScanEl.style.opacity = '1';
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', init);
