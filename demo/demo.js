/**
 * BrowserShield-Pro Live Demo & Benchmark Studio Controller
 */

let inferenceEngine = null;
let currentWorkload = 'idle';
let isRunning = false;
let autoStopTimer = null;
let countdownInterval = null;
let secondsRemaining = 30;

// Simulation metrics state
let simStartTime = performance.now();
let simLagMs = 0;
let simDomCount = 0;
let simNetCount = 0;
let simPostCount = 0;
let simIdleSec = 0;
let activeWorkers = [];
let animFrameId = null;

// DOM Elements
const tabBtns = document.querySelectorAll('.nav-tab');
const tabPanes = document.querySelectorAll('.tab-pane');
const workloadBtns = document.querySelectorAll('.workload-btn');
const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const countdownSpan = document.getElementById('countdownSpan');
const intensitySlider = document.getElementById('intensitySlider');
const intensityVal = document.getElementById('intensityVal');
const workerSlider = document.getElementById('workerSlider');
const workerVal = document.getElementById('workerVal');
const postSlider = document.getElementById('postSlider');
const postVal = document.getElementById('postVal');

// Verdict Elements
const verdictHero = document.getElementById('verdictHero');
const heroIcon = document.getElementById('heroIcon');
const heroTitle = document.getElementById('heroTitle');
const heroSub = document.getElementById('heroSub');
const heroProb = document.getElementById('heroProb');
const hudLag = document.getElementById('hudLag');
const hudDom = document.getElementById('hudDom');
const hudPost = document.getElementById('hudPost');
const hudReasons = document.getElementById('hudReasons');
const benignCanvas = document.getElementById('benignCanvas');
const canvasWrapper = document.getElementById('canvasWrapper');

// 1. Initialize
async function init() {
  try {
    const candidatePaths = [
      window.__MODEL_BUNDLE_URL__,
      'model_bundle.json',
      'demo/model_bundle.json',
      'extension/model_bundle.json',
      '../extension/model_bundle.json'
    ].filter(Boolean);

    for (const path of candidatePaths) {
      try {
        inferenceEngine = await BrowserShieldInference.load(path);
        console.log('BrowserShield Studio model loaded from:', path);
        break;
      } catch (_) {}
    }
    if (!inferenceEngine) {
      console.warn('Could not load model bundle from candidate paths, creating fallback instance.');
    }
  } catch (e) {
    console.error('Failed to load bundle in studio:', e);
  }

  setupEventListeners();
  startTelemetryLoop();
}

function setupEventListeners() {
  // Tabs
  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabBtns.forEach((b) => b.classList.remove('active'));
      tabPanes.forEach((p) => p.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.getAttribute('data-tab');
      document.getElementById(target).classList.add('active');
    });
  });

  // Workload selection
  workloadBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      if (isRunning) stopCurrentWorkload();
      workloadBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentWorkload = btn.getAttribute('data-workload');
      updateWorkloadDetails();
    });
  });

  // Sliders
  intensitySlider.addEventListener('input', (e) => {
    intensityVal.textContent = `${e.target.value}%`;
  });
  workerSlider.addEventListener('input', (e) => {
    workerVal.textContent = e.target.value;
  });
  postSlider.addEventListener('input', (e) => {
    postVal.textContent = `${e.target.value} req/s`;
  });

  // Action Buttons
  btnStart.addEventListener('click', startCurrentWorkload);
  btnStop.addEventListener('click', stopCurrentWorkload);
}

function updateWorkloadDetails() {
  const isAttack = currentWorkload.startsWith('miner') || currentWorkload.startsWith('stealth');
  const isBenignVisual = currentWorkload === 'video' || currentWorkload === 'webgl';

  if (isBenignVisual) {
    canvasWrapper.classList.add('active');
  } else {
    canvasWrapper.classList.remove('active');
  }
}

// 2. Workload Generators
function startCurrentWorkload() {
  if (isRunning) return;
  isRunning = true;
  btnStart.style.display = 'none';
  btnStop.style.display = 'inline-flex';
  secondsRemaining = 30;
  countdownSpan.textContent = `(Auto-stops in ${secondsRemaining}s)`;

  simStartTime = performance.now();
  simLagMs = 0;
  simDomCount = 0;
  simNetCount = 0;
  simPostCount = 0;

  const duty = parseInt(intensitySlider.value, 10) / 100.0;
  const numWorkers = parseInt(workerSlider.value, 10);
  const postRate = parseInt(postSlider.value, 10);

  // Auto-stop safety timer
  countdownInterval = setInterval(() => {
    secondsRemaining--;
    if (secondsRemaining <= 0) {
      stopCurrentWorkload();
    } else {
      countdownSpan.textContent = `(Auto-stops in ${secondsRemaining}s)`;
    }
  }, 1000);

  if (currentWorkload === 'miner_wasm' || currentWorkload === 'miner_throttled') {
    startMinerWorkers(numWorkers, duty);
  } else if (currentWorkload === 'stealth_miner') {
    startMinerWorkers(numWorkers, duty);
    startPostChatter(postRate);
  } else if (currentWorkload === 'video') {
    startVideoCanvasSimulation();
  } else if (currentWorkload === 'webgl') {
    startWebGLShaderSimulation();
  } else if (currentWorkload === 'dom_churn') {
    startDomChurnSimulation();
  }
}

function stopCurrentWorkload() {
  isRunning = false;
  btnStart.style.display = 'inline-flex';
  btnStop.style.display = 'none';
  countdownSpan.textContent = '';
  if (countdownInterval) clearInterval(countdownInterval);
  if (autoStopTimer) clearTimeout(autoStopTimer);

  // Terminate workers
  activeWorkers.forEach((w) => w.terminate());
  activeWorkers = [];

  // Stop canvas animations
  if (animFrameId) cancelAnimationFrame(animFrameId);
}

// Web Worker Miner Simulation
function startMinerWorkers(count, dutyCycle) {
  const workerCode = `
    let running = true;
    self.onmessage = function(e) {
      if (e.data === 'stop') running = false;
    };
    function computeLoop() {
      if (!running) return;
      const start = Date.now();
      const workTime = ${Math.round(50 * dutyCycle)};
      const restTime = ${Math.round(50 * (1 - dutyCycle))};
      
      while (Date.now() - start < workTime) {
        let h = 0x811c9dc5;
        for (let i = 0; i < 200000; i++) {
          h = Math.imul(h ^ (i & 0xff), 0x01000193);
        }
      }
      setTimeout(computeLoop, Math.max(restTime, 1));
    }
    computeLoop();
  `;
  const blob = new Blob([workerCode], { type: 'application/javascript' });
  const blobUrl = URL.createObjectURL(blob);

  for (let i = 0; i < count; i++) {
    const worker = new Worker(blobUrl);
    activeWorkers.push(worker);
  }

  // Also introduce main-thread event loop lag for visible detector effect
  function lagTick() {
    if (!isRunning) return;
    const start = performance.now();
    const burn = 35 * dutyCycle;
    while (performance.now() - start < burn) {
      Math.sin(Math.random());
    }
    simLagMs += burn * 1.8;
    setTimeout(lagTick, 60);
  }
  setTimeout(lagTick, 60);
}

function startPostChatter(ratePerSec) {
  const interval = 1000 / Math.max(ratePerSec, 1);
  const timer = setInterval(() => {
    if (!isRunning) {
      clearInterval(timer);
      return;
    }
    simPostCount += 1;
    simNetCount += 1;
  }, interval);
}

function startVideoCanvasSimulation() {
  canvasWrapper.classList.add('active');
  const ctx = benignCanvas.getContext('2d');
  let frame = 0;
  function render() {
    if (!isRunning) return;
    frame++;
    ctx.fillStyle = `hsl(${frame % 360}, 70%, 20%)`;
    ctx.fillRect(0, 0, benignCanvas.width, benignCanvas.height);
    ctx.fillStyle = '#fff';
    ctx.font = '14px Inter';
    ctx.fillText(`Benign 60 FPS Video Streamer - Frame ${frame}`, 15, 45);
    simNetCount += 0.05;
    animFrameId = requestAnimationFrame(render);
  }
  render();
}

function startWebGLShaderSimulation() {
  canvasWrapper.classList.add('active');
  const ctx = benignCanvas.getContext('2d');
  let t = 0;
  function render() {
    if (!isRunning) return;
    t += 0.05;
    ctx.fillStyle = '#050a14';
    ctx.fillRect(0, 0, benignCanvas.width, benignCanvas.height);
    ctx.strokeStyle = `hsl(${(t * 40) % 360}, 100%, 50%)`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let x = 0; x < benignCanvas.width; x += 5) {
      const y = 40 + Math.sin(x * 0.04 + t) * 20 + Math.cos(x * 0.02 - t) * 10;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    animFrameId = requestAnimationFrame(render);
  }
  render();
}

function startDomChurnSimulation() {
  const churnTimer = setInterval(() => {
    if (!isRunning) {
      clearInterval(churnTimer);
      return;
    }
    simDomCount += 12;
  }, 100);
}

// 3. Real-Time Telemetry & Inference Loop
function startTelemetryLoop() {
  setInterval(() => {
    if (!inferenceEngine) return;

    const up_ms = isRunning ? Math.max(performance.now() - simStartTime, 500) : 15000;
    const telemetry = {
      page_uptime_ms: up_ms,
      event_loop_lag_ms: isRunning ? simLagMs : 12,
      dom_mutation_count: isRunning ? simDomCount : 45,
      network_request_count: isRunning ? Math.max(Math.round(simNetCount), 1) : 24,
      post_request_count: isRunning ? simPostCount : 1,
      unique_domains_contacted: isRunning && currentWorkload.startsWith('stealth') ? 5 : 2,
      idle_ratio: isRunning ? 0.92 : 0.40,
      visibility_hidden: 0,
      visibility_changes: 0
    };

    const result = inferenceEngine.predict(telemetry);
    renderHUD(result);
  }, 350);
}

function renderHUD(result) {
  verdictHero.className = `verdict-hero ${result.statusClass}`;
  heroProb.textContent = `${result.riskScore.toFixed(1)}%`;

  if (result.verdict === 'DANGEROUS') {
    heroIcon.textContent = '🚨';
    heroTitle.textContent = 'CRYPTOJACKING ATTACK DETECTED';
    heroSub.textContent = `High Confidence Anomaly (Latency: ${result.latencyMs}ms)`;
  } else if (result.verdict === 'SUSPICIOUS') {
    heroIcon.textContent = '⚠️';
    heroTitle.textContent = 'SUSPICIOUS WORKLOAD DETECTED';
    heroSub.textContent = `Elevated Resource Thresholds (Latency: ${result.latencyMs}ms)`;
  } else if (result.verdict === 'UNSURE') {
    heroIcon.textContent = '❓';
    heroTitle.textContent = 'OUT-OF-DISTRIBUTION WORKLOAD';
    heroSub.textContent = 'Telemetry outside trained bounding envelope';
  } else {
    heroIcon.textContent = '🛡️';
    heroTitle.textContent = 'NORMAL BENIGN BROWSING';
    heroSub.textContent = `Zero Threat Detected (Latency: ${result.latencyMs}ms)`;
  }

  const tel = result.telemetry;
  hudLag.textContent = `${Math.round(tel.event_loop_lag_ms)} ms`;
  hudDom.textContent = `${Math.round(tel.dom_mutation_count)}`;
  hudPost.textContent = `${tel.post_request_count} / ${tel.network_request_count}`;

  // Reasons list
  hudReasons.innerHTML = '';
  result.reasons.forEach((r) => {
    const card = document.createElement('div');
    card.className = `reason-card ${r.severity}`;
    let ic = '🟢';
    if (r.severity === 'high') ic = '🔴';
    else if (r.severity === 'medium') ic = '🟡';

    card.innerHTML = `
      <div class="reason-title">
        <span>${ic}</span>
        <span>${escapeHtml(r.title)}</span>
      </div>
      <div class="reason-desc">${escapeHtml(r.description)}</div>
    `;
    hudReasons.appendChild(card);
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', init);
