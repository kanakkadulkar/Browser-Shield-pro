/**
 * BrowserShield-Pro In-Browser ML Inference Engine
 * Evaluates the trained XGBoost + Platt Calibration model directly in JavaScript.
 * Runs in sub-millisecond time with zero external network requests.
 */

class BrowserShieldInference {
  constructor(bundle) {
    this.bundle = bundle;
    this.isLoaded = !!bundle;
  }

  static async load(bundleUrl = 'model_bundle.json') {
    try {
      const response = await fetch(bundleUrl);
      const data = await response.json();
      return new BrowserShieldInference(data);
    } catch (err) {
      console.error('Failed to load BrowserShield-Pro model bundle:', err);
      throw err;
    }
  }

  /**
   * Transforms raw telemetry dictionary into the 15 BSP_v1 features.
   */
  extractFeatures(telemetry) {
    const up_ms = Number(telemetry.page_uptime_ms) || 0;
    const hasUptime = up_ms > 0;
    const t_ms = hasUptime ? up_ms : 1.0;
    const t_s = t_ms / 1000.0;
    const z = (v) => (hasUptime ? v : 0.0);

    const net = Number(telemetry.network_request_count) || 0;
    const dom = Number(telemetry.dom_mutation_count) || 0;
    const post = Number(telemetry.post_request_count) || 0;
    const lag_ms = Number(telemetry.event_loop_lag_ms) || 0;
    const unique_domains = Number(telemetry.unique_domains_contacted) || 0;
    const idle = Math.min(Math.max(Number(telemetry.idle_ratio) || 0, 0), 1);
    const vis_hidden = telemetry.visibility_hidden ? 1.0 : 0.0;
    const vis_changes = Number(telemetry.visibility_changes) || 0;

    return [
      hasUptime ? 0.0 : 1.0,                                      // 0: counts_only
      z(Math.log1p(t_s)),                                         // 1: log_uptime_s
      z(Math.min(Math.max(lag_ms / t_ms, 0.0), 1.0)),             // 2: lag_fraction
      z(Math.log1p(dom / t_s)),                                   // 3: log_dom_rate
      z(Math.log1p(net / t_s)),                                   // 4: log_net_rate
      z(Math.log1p(post / t_s)),                                  // 5: log_post_rate
      Math.min(Math.max(post / Math.max(net, 1.0), 0.0), 5.0),    // 6: post_share
      Math.log1p(dom),                                            // 7: log_dom
      Math.log1p(net),                                            // 8: log_net
      Math.log1p(post),                                           // 9: log_post
      Math.log1p(lag_ms),                                         // 10: log_lag_ms
      Math.log1p(unique_domains),                                 // 11: log_unique
      idle,                                                       // 12: idle_ratio
      vis_hidden,                                                 // 13: visibility_hidden
      Math.log1p(vis_changes),                                    // 14: log_vis_changes
    ];
  }

  checkOutOfRange(features) {
    const bounds = this.bundle.bounds;
    const delta = this.bundle.thresholds.delta_oor || 0.15;
    for (let i = 0; i < features.length; i++) {
      const minVal = bounds.min[i];
      const maxVal = bounds.max[i];
      const range = maxVal - minVal;
      if (features[i] < minVal - delta * range || features[i] > maxVal + delta * range) {
        return true;
      }
    }
    return false;
  }

  scaleFeatures(features) {
    const mean = this.bundle.scaler.mean;
    const scale = this.bundle.scaler.scale;
    const scaled = new Float64Array(features.length);
    for (let i = 0; i < features.length; i++) {
      scaled[i] = (features[i] - mean[i]) / (scale[i] || 1.0);
    }
    return scaled;
  }

  evaluateTree(node, scaled) {
    if ('leaf' in node) {
      return node.leaf;
    }
    const featIdx = parseInt(node.split.substring(1), 10);
    const val = scaled[featIdx];
    let targetId;
    if (isNaN(val) || val === null || val === undefined) {
      targetId = node.missing !== undefined ? node.missing : node.no;
    } else if (val < node.split_condition) {
      targetId = node.yes;
    } else {
      targetId = node.no;
    }

    if (node.children) {
      for (let i = 0; i < node.children.length; i++) {
        if (node.children[i].nodeid === targetId) {
          return this.evaluateTree(node.children[i], scaled);
        }
      }
    }
    return 0.0;
  }

  predictRaw(scaled) {
    let logit = 0.0;
    const trees = this.bundle.trees;
    for (let i = 0; i < trees.length; i++) {
      logit += this.evaluateTree(trees[i], scaled);
    }
    return 1.0 / (1.0 + Math.exp(-logit));
  }

  calibrate(rawProb) {
    const clipP = Math.min(Math.max(rawProb, 1e-6), 1.0 - 1e-6);
    const rawLogit = Math.log(clipP / (1.0 - clipP));
    const coef = this.bundle.platt.coef;
    const intercept = this.bundle.platt.intercept;
    const calLogit = coef * rawLogit + intercept;
    return 1.0 / (1.0 + Math.exp(-calLogit));
  }

  generateExplanations(telemetry, rawFeatures, scaledFeatures, calProb) {
    const reasons = [];
    const lag_ms = Number(telemetry.event_loop_lag_ms) || 0;
    const up_s = (Number(telemetry.page_uptime_ms) || 1000) / 1000.0;
    const post_count = Number(telemetry.post_request_count) || 0;
    const net_count = Number(telemetry.network_request_count) || 0;
    const vis_hidden = !!telemetry.visibility_hidden;
    const dom_count = Number(telemetry.dom_mutation_count) || 0;

    // Feature 2 & 10: Event Loop Lag
    if (scaledFeatures[10] > 1.2 || scaledFeatures[2] > 1.0) {
      reasons.push({
        id: 'event_loop_lag',
        title: 'Severe Event Loop Lag',
        description: `Main-thread delayed by ${(lag_ms).toFixed(0)} ms (${(lag_ms / Math.max(up_s*1000, 1) * 100).toFixed(1)}% of execution time). Typical of continuous WebAssembly/JS hashing loops.`,
        severity: 'high',
        weight: scaledFeatures[10]
      });
    }

    // Feature 5 & 6: POST request chatter
    if (post_count > 5 || scaledFeatures[5] > 1.0 || scaledFeatures[6] > 1.5) {
      const share = net_count > 0 ? (post_count / net_count * 100).toFixed(0) : 100;
      reasons.push({
        id: 'post_chatter',
        title: 'High POST Network Frequency',
        description: `${post_count} outgoing POST requests (${share}% of all traffic). Matches cryptojacking mining pool share submission patterns.`,
        severity: 'high',
        weight: scaledFeatures[5]
      });
    }

    // Feature 13: Background Execution
    if (vis_hidden && (scaledFeatures[10] > 0.5 || scaledFeatures[4] > 0.5)) {
      reasons.push({
        id: 'background_mining',
        title: 'Hidden Tab Resource Consumption',
        description: 'Heavy compute activity sustained while tab is in background/hidden state.',
        severity: 'medium',
        weight: 1.2
      });
    }

    // Feature 3 & 7: Low DOM rate with high lag
    if (dom_count < 20 && lag_ms > 200 && up_s > 3) {
      reasons.push({
        id: 'silent_worker',
        title: 'Unrendered Compute Loop',
        description: 'Intense execution without corresponding visual DOM updates, characteristic of hidden mining scripts.',
        severity: 'medium',
        weight: 0.9
      });
    }

    // Feature 11: Multi-domain contact
    if (scaledFeatures[11] > 1.8) {
      reasons.push({
        id: 'multi_domain',
        title: 'Multiple Third-Party Network Endpoints',
        description: `${telemetry.unique_domains_contacted || 0} unique external hosts reached within short duration.`,
        severity: 'low',
        weight: scaledFeatures[11]
      });
    }

    if (reasons.length === 0) {
      if (calProb > this.bundle.thresholds.suspicious) {
        reasons.push({
          id: 'composite_anomaly',
          title: 'Composite Telemetry Anomaly',
          description: 'Multi-variable anomaly detected across combined CPU and network rate distributions.',
          severity: 'medium',
          weight: 0.5
        });
      } else {
        reasons.push({
          id: 'benign_telemetry',
          title: 'Normal Browsing Behavior',
          description: 'CPU lag, network volume, and DOM interaction rates are consistent with benign web pages.',
          severity: 'none',
          weight: 0.0
        });
      }
    }

    // Sort by weight descending, pick top 3
    reasons.sort((a, b) => b.weight - a.weight);
    return reasons.slice(0, 3);
  }

  /**
   * Full inference pipeline: Telemetry -> Features -> Scaler -> XGBoost -> Platt -> Policy
   */
  predict(telemetry) {
    const t0 = performance.now();
    const rawFeatures = this.extractFeatures(telemetry);
    const isOutOfRange = this.checkOutOfRange(rawFeatures);
    const scaled = this.scaleFeatures(rawFeatures);
    const rawScore = this.predictRaw(scaled);
    const calibratedProb = this.calibrate(rawScore);

    const tDang = this.bundle.thresholds.dangerous;
    const tSusp = this.bundle.thresholds.suspicious;

    let verdict = 'SAFE';
    let statusClass = 'safe';

    if (isOutOfRange) {
      verdict = 'UNSURE';
      statusClass = 'unsure';
    } else if (calibratedProb >= tDang) {
      verdict = 'DANGEROUS';
      statusClass = 'danger';
    } else if (calibratedProb >= tSusp) {
      verdict = 'SUSPICIOUS';
      statusClass = 'warning';
    }

    const elapsed = performance.now() - t0;
    const reasons = this.generateExplanations(telemetry, rawFeatures, scaled, calibratedProb);

    return {
      verdict,
      statusClass,
      riskScore: Math.round(calibratedProb * 1000) / 10, // e.g. 87.4%
      rawScore: Math.round(rawScore * 10000) / 10000,
      calibratedScore: calibratedProb,
      isOutOfRange,
      thresholds: {
        dangerous: tDang,
        suspicious: tSusp
      },
      reasons,
      latencyMs: Math.round(elapsed * 100) / 100,
      telemetry,
      rawFeatures,
      scaledFeatures: Array.from(scaled)
    };
  }
}

// Export for browser scripts, modules, or worker environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BrowserShieldInference };
}
if (typeof window !== 'undefined') {
  window.BrowserShieldInference = BrowserShieldInference;
}
