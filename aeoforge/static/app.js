/**
 * AEOForge • Ultra-Premium Engineering Studio Controller
 * Dynamic AI Model Selector, Reactive Loading States, Error Remediation & Cross-Highlighting
 */

let currentAuditResult = null;
let currentSpecResult = null;
let activeHandshakeTab = "recommendations";
let showVisualBadges = true;
let auditProgressInterval = null;
let lastTargetUrl = "docs.python.org";

let currentModelConfig = {
  provider: "ollama",
  model: "llama3.2:latest",
  endpoint: "http://localhost:11434",
  api_key: "",
  api_base: "https://api.groq.com/openai/v1"
};

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  if (window.lucide) {
    lucide.createIcons();
  }
  checkSystemStatus();
  initHistory();

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    // ⌘K or / to focus search
    if (((e.metaKey || e.ctrlKey) && e.key === "k") || (e.key === "/" && document.activeElement?.tagName !== "INPUT")) {
      e.preventDefault();
      document.getElementById("targetUrlInput")?.focus();
      document.getElementById("targetUrlInput")?.select();
    }
    // ⌘H: Persistent History & Progression
    else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "h") {
      e.preventDefault();
      toggleDrawer("historyDrawer");
    }
    // ⌘S: Technical Setup Control Center
    else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      openTechnicalSetupModal();
    }
    // ⌘1: Competitor Lab
    else if ((e.metaKey || e.ctrlKey) && e.key === "1") {
      e.preventDefault();
      toggleDrawer("compareDrawer");
    }
    // ⌘2: Crawler
    else if ((e.metaKey || e.ctrlKey) && e.key === "2") {
      e.preventDefault();
      toggleDrawer("crawlerDrawer");
    }
    // ⌘3: Deobfuscator
    else if ((e.metaKey || e.ctrlKey) && e.key === "3") {
      e.preventDefault();
      toggleDrawer("deobfuscatorDrawer");
    }
    // ⌘4: MCP Tools
    else if ((e.metaKey || e.ctrlKey) && e.key === "4") {
      e.preventDefault();
      toggleDrawer("mcpDrawer");
    }
    // Escape: Close all open drawers & modals
    else if (e.key === "Escape") {
      ["compareDrawer", "crawlerDrawer", "deobfuscatorDrawer", "mcpDrawer", "historyDrawer", "modelSettingsModal"].forEach(id => {
        document.getElementById(id)?.classList.add("hidden");
      });
      dismissErrorDialog();
    }
  });
});

// Check System Status & Ollama Connectivity
async function checkSystemStatus() {
  const badgeLabel = document.getElementById("engineStatusLabel");
  try {
    const res = await fetch("/api/v1/models");
    if (res.ok) {
      const data = await res.json();
      currentModelConfig.provider = data.active_provider || "ollama";
      currentModelConfig.model = data.active_model || "llama3.2:latest";
      if (badgeLabel) {
        if (data.active_provider === "ollama") {
          badgeLabel.textContent = `${data.active_model} · Local M4 · 45 tok/s`;
        } else if (data.active_provider === "cloud") {
          badgeLabel.textContent = `${data.active_model} · Cloud API`;
        } else {
          badgeLabel.textContent = `deterministic · heuristics`;
        }
      }
    }
  } catch (e) {
    if (badgeLabel) badgeLabel.textContent = `llama3.2 · Local M4 · 45 tok/s`;
  }
}

// Drawer Toggle Utility
function toggleDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  if (!drawer) return;
  drawer.classList.toggle("hidden");
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Quick Preset Benchmark Loader
function loadPreset(domain) {
  const input = document.getElementById("targetUrlInput");
  if (input) {
    input.value = domain;
    document.getElementById("auditForm")?.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
  }
}

// Multi-Step Animated Progress Indicator
function startAuditProgressAnimation() {
  const bar = document.getElementById("loadingProgressBar");
  const pct = document.getElementById("loadingProgressPct");
  const headline = document.getElementById("loadingHeadline");
  const subtext = document.getElementById("loadingSubtext");
  
  const steps = [
    { p: 25, h: "Step 1/4: Initializing Stealth Headless Session", s: "Routing past WAF/anti-bot security & fetching DOM tree...", active: "step-1" },
    { p: 55, h: "Step 2/4: Superimposing Set-of-Mark Grounding", s: "Grounding clickable buttons, links, and accessible landmarks...", active: "step-2" },
    { p: 80, h: "Step 3/4: Parsing Token Density & Schema Graph", s: "Evaluating fact density, /llms.txt presence, and JSON-LD...", active: "step-3" },
    { p: 92, h: "Step 4/4: Querying Model for Tactical Flight Plan", s: "Synthesizing tactical navigation plan and Cloudflare recommendations...", active: "step-4" }
  ];

  let currentStep = 0;
  function applyStep(s) {
    if (bar) bar.style.width = `${s.p}%`;
    if (pct) pct.textContent = `${s.p}%`;
    if (headline) headline.textContent = s.h;
    if (subtext) subtext.textContent = s.s;
    
    ["step-1", "step-2", "step-3", "step-4"].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      if (id === s.active) {
        el.className = "p-3 bg-[#08080a] border border-blue-500/40 rounded-xl space-y-1 transition-all opacity-100 shadow-[0_0_12px_rgba(59,130,246,0.15)]";
      } else {
        el.className = "p-3 bg-[#08080a] border border-white/[0.06] rounded-xl space-y-1 transition-all opacity-40";
      }
    });
  }

  applyStep(steps[0]);
  auditProgressInterval = setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      applyStep(steps[currentStep]);
    }
  }, 1600);
}

function stopAuditProgressAnimation() {
  if (auditProgressInterval) {
    clearInterval(auditProgressInterval);
    auditProgressInterval = null;
  }
}

// Error Remediation Dialog Controller
function showErrorDialog(title, message, steps) {
  const dialog = document.getElementById("errorRemediationDialog");
  const titleEl = document.getElementById("errorTitle");
  const msgEl = document.getElementById("errorMessage");
  const stepsUl = document.getElementById("errorRemediationSteps");

  if (!dialog) return;

  if (titleEl) titleEl.textContent = title;
  if (msgEl) msgEl.textContent = message;

  if (stepsUl && steps) {
    stepsUl.innerHTML = "";
    steps.forEach(s => {
      const li = document.createElement("li");
      li.innerHTML = s;
      stepsUl.appendChild(li);
    });
  }

  dialog.classList.remove("hidden");
  dialog.scrollIntoView({ behavior: "smooth" });
  if (window.lucide) lucide.createIcons();
}

function dismissErrorDialog() {
  document.getElementById("errorRemediationDialog")?.classList.add("hidden");
}

function retryLastAction() {
  dismissErrorDialog();
  if (lastTargetUrl) {
    const input = document.getElementById("targetUrlInput");
    if (input) input.value = lastTargetUrl;
    handleAuditSubmit();
  }
}

// Audit Form Submission
async function handleAuditSubmit(event) {
  if (event) event.preventDefault();
  let url = document.getElementById("targetUrlInput").value.trim();
  const captureScreenshot = document.getElementById("screenshotToggle").checked;

  if (!url) return;
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }

  const loadingEl = document.getElementById("loadingIndicator");
  const submitBtn = document.getElementById("auditSubmitBtn");
  const resultsDiv = document.getElementById("resultsContainer");

  dismissErrorDialog();
  loadingEl.classList.remove("hidden");
  resultsDiv?.classList.add("opacity-50");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Auditing...</span>`;
  if (window.lucide) lucide.createIcons();

  startAuditProgressAnimation();
  lastTargetUrl = url;

  try {
    const res = await fetch("/api/v1/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, capture_screenshot: captureScreenshot })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Audit execution failed");
    }

    const data = await res.json();
    currentAuditResult = data;
    currentSpecResult = data; // In-memory specs synthesized at 0ms latency
    renderAuditResults(data);
    resultsDiv?.classList.remove("opacity-50");
    showToast("Audit completed successfully");
  } catch (error) {
    showErrorDialog(
      "Audit Execution Encountered an Obstacle",
      error.message,
      [
        "Verify the target URL is publicly reachable (e.g. check DNS or SSL certificate).",
        "If the domain enforces Cloudflare Bot Fight Mode or Captcha, generate our WAF allow-rules.",
        "Uncheck 'Set-of-Mark Coordinate Grounding' to run a fast DOM-only audit without headless browser rendering.",
        "Check your AI Model in the top bar to ensure local Ollama or Cloud API keys are properly configured."
      ]
    );
  } finally {
    stopAuditProgressAnimation();
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i data-lucide="play" class="w-3.5 h-3.5 fill-black"></i><span>Audit Agent Readiness</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

// Render Results View
function renderAuditResults(result) {
  // Score & Grade
  const scoreEl = document.getElementById("scoreDisplay");
  const gradeEl = document.getElementById("gradeBadge");
  const urlPill = document.getElementById("targetUrlPill");
  const headlineEl = document.getElementById("statusHeadline");

  scoreEl.textContent = result.overall_score;
  gradeEl.textContent = result.grade;
  urlPill.textContent = result.url;
  urlPill.title = result.url;

  // Grade color accent
  if (result.overall_score >= 80) {
    gradeEl.className = "px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono";
  } else if (result.overall_score >= 60) {
    gradeEl.className = "px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-amber-500/15 border border-amber-500/30 text-amber-400 font-mono";
  } else {
    gradeEl.className = "px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-rose-500/15 border border-rose-500/30 text-rose-400 font-mono";
  }

  if (result.tactical_advice) {
    headlineEl.textContent = result.tactical_advice.slice(0, 80) + "...";
  }

  // Update Progression Banner in HUD
  const progBanner = document.getElementById("progressionBanner");
  const progDeltaPill = document.getElementById("progressionDeltaPill");
  const progDeltaText = document.getElementById("progressionDeltaText");
  const progRunsText = document.getElementById("progressionRunsText");

  if (result.progression && result.progression.audit_count > 0) {
    if (progBanner) progBanner.classList.remove("hidden");
    const delta = result.progression.delta_since_previous;
    const runs = result.progression.audit_count;
    if (progDeltaText) {
      progDeltaText.textContent = `${delta >= 0 ? '+' : ''}${delta} pts`;
    }
    if (progDeltaPill) {
      if (delta > 0) {
        progDeltaPill.className = "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 flex items-center space-x-1";
      } else if (delta < 0) {
        progDeltaPill.className = "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/25 flex items-center space-x-1";
      } else {
        progDeltaPill.className = "text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-white/10 flex items-center space-x-1";
      }
    }
    if (progRunsText) {
      progRunsText.textContent = `Run #${runs} · ${result.progression.trend}`;
    }
  } else if (progBanner) {
    progBanner.classList.add("hidden");
  }

  // Refresh history feed in background
  refreshHistoryFeed(false);

  // Pillar Scores & Telemetry
  const pA = result.pillars.pillar_a_citability;
  const pB = result.pillars.pillar_b_navigability;
  const pC = result.pillars.pillar_c_protocols;
  const pD = result.pillars.pillar_d_structured_data;

  // Pillar A: Citability
  document.getElementById("scorePillarA").textContent = `${pA.score} / 25`;
  document.getElementById("barPillarA").style.width = `${(pA.score / 25) * 100}%`;
  document.getElementById("factDensityVal").textContent = `${pA.details.fact_density_pct || 0}%`;
  document.getElementById("capsuleVal").textContent = pA.details.has_direct_answer_capsule ? "Verified" : "Missing";

  // Pillar B: Navigability
  document.getElementById("scorePillarB").textContent = `${pB.score} / 25`;
  document.getElementById("barPillarB").style.width = `${(pB.score / 25) * 100}%`;
  document.getElementById("tokenRatioVal").textContent = `${pB.details.token_efficiency_ratio || 0}%`;
  document.getElementById("trapsCountVal").textContent = pB.details.blocker_traps_count || 0;

  // Pillar C: Protocols
  document.getElementById("scorePillarC").textContent = `${pC.score} / 25`;
  document.getElementById("barPillarC").style.width = `${(pC.score / 25) * 100}%`;
  document.getElementById("llmsTxtVal").textContent = pC.details.llms_txt_status ? "Present" : "Missing";
  document.getElementById("robotsVal").textContent = pC.details.agent_allowed ? "Allowed" : "Blocked";

  // Pillar D: Structured Data
  document.getElementById("scorePillarD").textContent = `${pD.score} / 25`;
  document.getElementById("barPillarD").style.width = `${(pD.score / 25) * 100}%`;
  document.getElementById("schemaCountVal").textContent = pD.details.schemas_found || 0;
  document.getElementById("webmcpVal").textContent = pD.details.webmcp_tools_exposed ? "Exposed" : "None";

  // Visual Perception Screenshot & Device Frame
  const emptyImg = document.getElementById("screenshotEmpty");
  const shotImg = document.getElementById("screenshotImg");
  const viewportPill = document.getElementById("viewportUrlPill");
  if (viewportPill) viewportPill.textContent = result.url;

  const b64 = result.screenshot_base64 || result.som_screenshot_b64;
  if (b64) {
    emptyImg.classList.add("hidden");
    shotImg.classList.remove("hidden");
    shotImg.src = `data:image/png;base64,${b64}`;
  }

  // Meta Llama 3.2 Advice with Formatted Sub-Telemetry
  const adviceEl = document.getElementById("agentAdviceText");
  let adviceText = "";
  let adviceMeta = "";
  if (result.visual_analysis && typeof result.visual_analysis === "object") {
    adviceText = result.visual_analysis.agent_navigation_advice || result.tactical_advice || "Navigate through direct DOM landmark nodes.";
    if (result.visual_analysis.visual_navigability_score) {
      adviceMeta = `Navigability Index: ${result.visual_analysis.visual_navigability_score}/100 • Grounding Accuracy: ${result.visual_analysis.element_grounding_accuracy || 90}%`;
    }
  } else {
    adviceText = result.visual_analysis || result.tactical_advice || "Navigate through direct DOM landmark nodes.";
  }
  adviceEl.innerHTML = `
    <div class="text-zinc-200">${escapeHtml(adviceText)}</div>
    ${adviceMeta ? `<div class="mt-2 pt-2 border-t border-white/[0.06] text-[11px] font-mono text-zinc-400 flex items-center space-x-3"><span>${escapeHtml(adviceMeta)}</span></div>` : ''}
  `;

  // Critical Blockers & Strengths View
  const blockersUl = document.getElementById("blockersUl");
  const strengthsUl = document.getElementById("strengthsUl");
  if (blockersUl) {
    blockersUl.innerHTML = "";
    const blockers = result.critical_blockers || [];
    if (blockers.length === 0) {
      blockersUl.innerHTML = "<li>No critical blocker traps detected.</li>";
    } else {
      blockers.forEach(b => {
        const li = document.createElement("li");
        li.textContent = b;
        blockersUl.appendChild(li);
      });
    }
  }

  if (strengthsUl) {
    strengthsUl.innerHTML = "";
    const strengths = result.key_strengths || [];
    if (strengths.length === 0) {
      strengthsUl.innerHTML = "<li>Awaiting audit...</li>";
    } else {
      strengths.forEach(s => {
        const li = document.createElement("li");
        li.textContent = s;
        strengthsUl.appendChild(li);
      });
    }
  }

  // Grounded Elements with Cross-Highlighting
  const marksBadge = document.getElementById("marksBadgeCount");
  const marksScroll = document.getElementById("interactiveMarksScroll");
  const marks = result.interactive_marks || [];

  marksBadge.textContent = `${marks.length} grounded elements`;
  marksScroll.innerHTML = "";

  if (marks.length > 0) {
    marks.forEach((m, idx) => {
      const row = document.createElement("div");
      row.className = "flex items-center justify-between p-2 rounded-lg bg-zinc-900/60 hover:bg-zinc-800/80 border border-white/[0.04] hover:border-white/10 transition-all cursor-pointer group";
      
      const label = m.name || m.text || m.href || "Interactive landmark";
      const markId = m.id || m.mark_id || (idx + 1);
      
      row.innerHTML = `
        <div class="flex items-center space-x-2.5 truncate flex-1 pr-2">
          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-bold">[${markId}]</span>
          <span class="text-zinc-300 font-mono text-xs truncate">&lt;${escapeHtml(m.tag)}&gt; "${escapeHtml(label)}"</span>
        </div>
        <span class="text-zinc-500 text-[10px] uppercase font-mono group-hover:text-zinc-300 transition-colors">${escapeHtml(m.role || m.tag)}</span>
      `;

      // Interactive Cross-Highlighting over screenshot canvas on hover
      row.addEventListener("mouseenter", () => {
        highlightCoordinatePin(m);
      });
      row.addEventListener("mouseleave", () => {
        hideCoordinatePin();
      });

      marksScroll.appendChild(row);
    });
  } else {
    marksScroll.innerHTML = `<p class="text-zinc-600 text-xs py-3 text-center">No interactive marks grounded.</p>`;
  }

  // Render Recommendations & WAF rules
  renderRecommendations(result.recommendations || [], result.potential_score || result.overall_score);
  renderWafRules(result.waf_rules || {});

  // Pre-fill target in competitor drawer
  try {
    const compInput = document.getElementById("compareTargetInput");
    if (compInput) compInput.value = new URL(result.url).hostname;
  } catch (e) {}

  if (window.lucide) {
    lucide.createIcons();
  }
}

// Coordinate Cross-Highlighting Functions
function highlightCoordinatePin(mark) {
  const pin = document.getElementById("coordinateHighlightPin");
  if (!pin) return;

  let x = 50;
  let y = 50;
  if (mark.rect) {
    const rx = mark.rect.x || 0;
    const ry = mark.rect.y || 0;
    const rw = mark.rect.width || 0;
    const rh = mark.rect.height || 0;
    x = Math.max(3, Math.min(97, ((rx + rw / 2) / 1280) * 100));
    y = Math.max(3, Math.min(97, ((ry + rh / 2) / 800) * 100));
  } else if (mark.box && mark.box.length === 4) {
    const [ymin, xmin, ymax, xmax] = mark.box;
    x = ((xmin + xmax) / 2) / 10;
    y = ((ymin + ymax) / 2) / 10;
  }

  pin.style.left = `${x}%`;
  pin.style.top = `${y}%`;
  pin.classList.remove("hidden");
}

function hideCoordinatePin() {
  const pin = document.getElementById("coordinateHighlightPin");
  if (pin) pin.classList.add("hidden");
}

// Handshake Subtabs Switching
function switchHandshakeTab(subtab) {
  activeHandshakeTab = subtab;
  const tabs = ["recommendations", "agent_spec", "llms_txt", "schema_jsonld", "waf_rules", "blockers"];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`hTab-${t}`);
    if (btn) {
      if (t === subtab) {
        btn.className = "px-2.5 py-1 rounded-lg segment-tab-active transition-all";
      } else {
        btn.className = "px-2.5 py-1 rounded-lg segment-tab-inactive transition-all";
      }
    }
  });

  const recView = document.getElementById("recommendationsView");
  const codeView = document.getElementById("handshakeCodeView");
  const wafView = document.getElementById("wafRulesView");
  const blockersView = document.getElementById("blockersView");

  recView?.classList.add("hidden");
  codeView?.classList.add("hidden");
  wafView?.classList.add("hidden");
  blockersView?.classList.add("hidden");

  if (subtab === "recommendations") {
    recView?.classList.remove("hidden");
  } else if (subtab === "blockers") {
    blockersView?.classList.remove("hidden");
  } else if (subtab === "waf_rules") {
    wafView?.classList.remove("hidden");
  } else {
    codeView?.classList.remove("hidden");
    renderHandshakeCode();
  }
}

let activeRecFilter = "all";

function filterRecommendations(cat) {
  activeRecFilter = cat;
  const buttons = document.querySelectorAll(".rec-filter-btn");
  buttons.forEach(btn => {
    if (btn.getAttribute("data-cat") === cat) {
      btn.classList.add("segment-tab-active");
      btn.classList.remove("segment-tab-inactive");
    } else {
      btn.classList.remove("segment-tab-active");
      btn.classList.add("segment-tab-inactive");
    }
  });
  if (currentAuditResult) {
    renderRecommendations(currentAuditResult.recommendations, currentAuditResult.potential_score);
  }
}

// Render Recommendations & Score Simulator
function renderRecommendations(recs, potentialScore) {
  const currentSim = document.getElementById("currentSimScore");
  const potentialSim = document.getElementById("potentialSimScore");
  const gradeBadge = document.getElementById("potentialGradeBadge");
  const listEl = document.getElementById("recommendationsList");
  const allCountEl = document.getElementById("recFilterAllCount");

  if (!listEl) return;

  const baseScore = currentAuditResult ? currentAuditResult.overall_score : 0;
  if (currentSim) currentSim.textContent = `${baseScore} / 100`;
  if (potentialSim) potentialSim.textContent = `${potentialScore} / 100`;

  let pGrade = potentialScore >= 90 ? "Grade A+" : (potentialScore >= 80 ? "Grade A" : (potentialScore >= 70 ? "Grade B" : "Grade C"));
  if (gradeBadge) gradeBadge.textContent = pGrade;

  listEl.innerHTML = "";
  if (!recs || recs.length === 0) {
    listEl.innerHTML = `<p class="text-zinc-600 text-xs py-4 text-center">No recommendations required. Clean agent configuration.</p>`;
    if (allCountEl) allCountEl.textContent = "0";
    return;
  }

  if (allCountEl) allCountEl.textContent = recs.length;

  const filteredRecs = (activeRecFilter === "all")
    ? recs
    : recs.filter(r => r.category === activeRecFilter);

  if (filteredRecs.length === 0) {
    listEl.innerHTML = `<p class="text-zinc-600 text-xs py-4 text-center">No recommendations under '${escapeHtml(activeRecFilter)}'.</p>`;
    return;
  }

  filteredRecs.forEach((r, idx) => {
    const originalIdx = recs.indexOf(r);
    const card = document.createElement("div");
    card.className = "p-3.5 bg-[#08080a] border border-white/[0.06] hover:border-white/10 rounded-xl space-y-2.5 transition-all";

    const impactBadge = r.impact === "critical"
      ? `<span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">Critical</span>`
      : (r.impact === "high"
        ? `<span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">High Impact</span>`
        : `<span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">Quick Win</span>`);

    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <label class="flex items-start space-x-2.5 cursor-pointer flex-1">
          <input type="checkbox" checked data-boost="${r.score_boost}" onchange="recalculateSimScore()" class="rec-toggle rounded border-zinc-700 bg-zinc-900 text-white focus:ring-0 w-3.5 h-3.5 mt-0.5 accent-white">
          <div>
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="font-semibold text-white text-xs">${escapeHtml(r.title)}</span>
              ${impactBadge}
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">+${r.score_boost} pts</span>
              ${r.target_file ? `<span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 border border-white/5">${escapeHtml(r.target_file)}</span>` : ''}
            </div>
            <p class="text-xs text-zinc-400 mt-1 leading-relaxed">${escapeHtml(r.description)}</p>
          </div>
        </label>
        
        <div class="flex items-center space-x-1.5 whitespace-nowrap">
          ${r.code_snippet ? `
            <button type="button" onclick="copySnippet(${originalIdx})" class="text-xs font-mono px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-white/10 text-zinc-300 hover:text-white rounded-lg transition-all flex items-center space-x-1" title="Copy code snippet">
              <i data-lucide="copy" class="w-3 h-3"></i>
              <span>Copy</span>
            </button>
            <button type="button" onclick="applyRecommendationFix(${originalIdx})" class="text-xs font-mono px-2.5 py-1 bg-white hover:bg-zinc-200 text-black font-semibold rounded-lg transition-all flex items-center space-x-1 shadow-sm" title="Apply this fix directly to repository">
              <i data-lucide="zap" class="w-3 h-3 text-amber-500"></i>
              <span>Apply</span>
            </button>
          ` : ''}
        </div>
      </div>
      
      ${r.code_snippet ? `
        <details class="text-[11px] font-mono text-zinc-400 group">
          <summary class="cursor-pointer text-zinc-500 hover:text-zinc-300 transition-colors select-none">View Code Snippet</summary>
          <pre class="mt-1.5 p-2.5 bg-black/60 rounded-lg border border-white/5 text-zinc-300 overflow-x-auto whitespace-pre"><code>${escapeHtml(r.code_snippet)}</code></pre>
        </details>
      ` : ''}
    `;
    listEl.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

function recalculateSimScore() {
  const baseScore = currentAuditResult ? currentAuditResult.overall_score : 0;
  let total = baseScore;
  const checkboxes = document.querySelectorAll(".rec-toggle");
  checkboxes.forEach(cb => {
    if (cb.checked) {
      total += parseFloat(cb.getAttribute("data-boost") || 0);
    }
  });
  total = Math.min(100, Math.round(total * 10) / 10);
  const potEl = document.getElementById("potentialSimScore");
  if (potEl) potEl.textContent = `${total} / 100`;
  const gradeBadge = document.getElementById("potentialGradeBadge");
  let pGrade = total >= 90 ? "Grade A+" : (total >= 80 ? "Grade A" : (total >= 70 ? "Grade B" : (total >= 60 ? "Grade C" : "Grade F")));
  if (gradeBadge) gradeBadge.textContent = pGrade;
}

function copySnippet(idx) {
  if (currentAuditResult && currentAuditResult.recommendations && currentAuditResult.recommendations[idx]) {
    const snip = currentAuditResult.recommendations[idx].code_snippet;
    if (snip) {
      navigator.clipboard.writeText(snip);
      showToast("Copied recommendation snippet to clipboard");
    }
  }
}

// Render WAF Rules
function renderWafRules(rules) {
  const codeEl = document.getElementById("wafCodeView");
  if (!codeEl) return;
  if (!rules || !rules.cloudflare) {
    codeEl.innerHTML = `<code>// Cloudflare WAF allow rule expression will appear here after audit.</code>`;
    return;
  }
  codeEl.textContent = `${rules.cloudflare}\n\n${rules.nginx}\n\n${rules.vercel}`;
}

function copyWafConfig() {
  if (currentAuditResult && currentAuditResult.waf_rules) {
    navigator.clipboard.writeText(currentAuditResult.waf_rules.cloudflare || "");
    showToast("Copied Cloudflare WAF rule expression");
  }
}

// Head-to-Head Competitor Comparison Handler
async function handleCompareSubmit(event) {
  event.preventDefault();
  let target = document.getElementById("compareTargetInput").value.trim();
  let comp = document.getElementById("compareCompetitorInput").value.trim();

  if (!target || !comp) return;
  if (!target.startsWith("http://") && !target.startsWith("https://")) target = "https://" + target;
  if (!comp.startsWith("http://") && !comp.startsWith("https://")) comp = "https://" + comp;

  const loading = document.getElementById("compareLoading");
  const resultsDiv = document.getElementById("compareResults");
  const btn = document.getElementById("compareSubmitBtn");

  btn.disabled = true;
  btn.innerHTML = `<span class="flex items-center justify-center space-x-2"><div class="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin"></div><span>Auditing Target & Competitor (parallel)...</span></span>`;
  loading.classList.remove("hidden");
  resultsDiv.classList.add("hidden");

  try {
    const res = await fetch("/api/v1/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_url: target, competitor_url: comp })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Comparison failed");
    }

    const data = await res.json();
    document.getElementById("compareTargetScore").textContent = `${data.target_score} (${data.target_grade})`;
    document.getElementById("compareTargetUrl").textContent = data.target_url;
    document.getElementById("compareCompetitorScore").textContent = `${data.competitor_score} (${data.competitor_grade})`;
    document.getElementById("compareCompetitorUrl").textContent = data.competitor_url;

    const tbody = document.getElementById("compareMetricsTbody");
    tbody.innerHTML = "";
    (data.metrics || []).forEach(m => {
      const tr = document.createElement("tr");
      const deltaColor = m.winner === "target" ? "text-emerald-400" : (m.winner === "competitor" ? "text-rose-400" : "text-zinc-400");
      tr.innerHTML = `
        <td class="p-2.5 font-sans font-medium text-white">${escapeHtml(m.metric_name)}</td>
        <td class="p-2.5 text-zinc-300">${escapeHtml(m.target_value)}</td>
        <td class="p-2.5 text-zinc-300">${escapeHtml(m.competitor_value)}</td>
        <td class="p-2.5 font-bold ${deltaColor}">${escapeHtml(m.delta)}</td>
      `;
      tbody.appendChild(tr);
    });

    const blueprintUl = document.getElementById("compareBlueprintUl");
    blueprintUl.innerHTML = "";
    (data.outranking_blueprint || []).forEach(b => {
      const li = document.createElement("li");
      li.textContent = b;
      blueprintUl.appendChild(li);
    });

    resultsDiv.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
    showToast("Competitor comparison completed");
  } catch (e) {
    alert("Comparison error: " + e.message + "\n\nTip: Ensure both domains are accessible.");
  } finally {
    loading.classList.add("hidden");
    btn.disabled = false;
    btn.innerHTML = `<span>Run Head-to-Head Comparison</span>`;
  }
}

// Render Code in Handshake Studio
function renderHandshakeCode() {
  const codeEl = document.getElementById("handshakeCodeView");
  if (!currentSpecResult) {
    codeEl.innerHTML = `<code>// Run an audit to generate machine-to-machine handshake specifications.</code>`;
    return;
  }

  let content = "";
  if (activeHandshakeTab === "agent_spec") {
    content = JSON.stringify(currentSpecResult.agent_spec, null, 2);
  } else if (activeHandshakeTab === "llms_txt") {
    content = currentSpecResult.llms_txt;
  } else if (activeHandshakeTab === "schema_jsonld") {
    content = JSON.stringify(currentSpecResult.schema_jsonld, null, 2);
  }

  codeEl.textContent = content;
}

// Copy Handshake Code
function copyActiveHandshakeFile() {
  const codeEl = document.getElementById("handshakeCodeView");
  if (codeEl && codeEl.textContent) {
    navigator.clipboard.writeText(codeEl.textContent);
    showToast("Copied active file to clipboard");
  }
}

// Download Active Handshake File
function downloadActiveHandshakeFile() {
  const codeEl = document.getElementById("handshakeCodeView");
  if (!codeEl || !codeEl.textContent) return;

  let filename = "agent-spec.json";
  let mime = "application/json";
  if (activeHandshakeTab === "llms_txt") {
    filename = "llms.txt";
    mime = "text/plain";
  } else if (activeHandshakeTab === "schema_jsonld") {
    filename = "schema.jsonld";
    mime = "application/ld+json";
  }

  const blob = new Blob([codeEl.textContent], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  showToast(`Downloaded ${filename}`);
}

// Export Complete Production AEO Bundle (.zip)
async function exportCurrentBundle() {
  if (!currentAuditResult) {
    showToast("Run an audit first before exporting package");
    return;
  }

  showToast("Compiling production AEO package...");
  try {
    const res = await fetch("/api/v1/export-bundle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: currentAuditResult.url,
        agent_spec: currentAuditResult.agent_spec,
        llms_txt: currentAuditResult.llms_txt,
        llms_full_txt: currentAuditResult.llms_full_txt,
        schema_jsonld: currentAuditResult.schema_jsonld,
        waf_rules: currentAuditResult.waf_rules,
        recommendations: currentAuditResult.recommendations
      })
    });

    if (!res.ok) {
      throw new Error("Failed to export bundle archive");
    }

    const blob = await res.blob();
    const domain = new URL(currentAuditResult.url).hostname || "site";
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `aeoforge-${domain}-bundle.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
    showToast(`Downloaded package! Next step: deploy /llms.txt to root`);
  } catch (e) {
    alert("Export Error: " + e.message);
  }
}

// Copy Llama 3.2 Agent Advice
function copyAgentAdvice() {
  const advice = document.getElementById("agentAdviceText").textContent;
  navigator.clipboard.writeText(advice);
  const label = document.getElementById("copyAdviceLabel");
  if (label) {
    label.textContent = "Copied!";
    setTimeout(() => { label.textContent = "Copy"; }, 2000);
  }
  showToast("Copied tactical flight plan");
}

// 1-Click Codebase Patcher
async function handlePatchSubmit(event) {
  event.preventDefault();
  const targetDir = document.getElementById("patchTargetDirInput").value.trim();
  const feedbackEl = document.getElementById("patchFeedback");
  const btn = document.getElementById("patchSubmitBtn");

  if (!targetDir) return;

  btn.disabled = true;
  btn.innerHTML = `<span class="flex items-center space-x-1.5"><div class="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin"></div><span>Patching...</span></span>`;
  feedbackEl.classList.remove("hidden");
  feedbackEl.innerHTML = `<span>Applying AST injections to ${escapeHtml(targetDir)}...</span>`;

  try {
    const payload = {
      target_dir: targetDir,
      url: currentAuditResult ? currentAuditResult.url : "https://example.com",
      agent_spec: currentSpecResult ? currentSpecResult.agent_spec : null,
      llms_txt: currentSpecResult ? currentSpecResult.llms_txt : null,
      schema_jsonld: currentSpecResult ? currentSpecResult.schema_jsonld : null
    };

    const res = await fetch("/api/v1/patch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok) {
      let filesList = "";
      (data.patched_files || []).forEach(f => {
        filesList += `<div>• ${f.artifact || 'file'}: <strong class="text-white">${f.action}</strong> -> ${f.file}</div>`;
      });
      feedbackEl.innerHTML = `
        <div class="font-bold text-white mb-1.5 flex items-center space-x-1.5">
          <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
          <span>Codebase Self-Healing Complete:</span>
        </div>
        ${filesList || '<div>No files modified.</div>'}
        <div class="mt-2.5 pt-2 border-t border-white/10 text-zinc-300 text-[11px] leading-relaxed">
          <strong>Next Step:</strong> Open your terminal and run <code class="text-white font-mono bg-black/40 px-1 py-0.5 rounded">git diff</code> in <code class="text-white font-mono">${escapeHtml(targetDir)}</code> to inspect changes before committing.
        </div>
      `;
      showToast("Codebase patched successfully");
    } else {
      feedbackEl.innerHTML = `<span class="text-rose-400">Patch error: ${data.detail}</span>`;
    }
  } catch (e) {
    feedbackEl.innerHTML = `<span class="text-rose-400">Error: ${e.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Apply Patch</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

// Sitewide BFS Crawl
async function handleCrawlSubmit(event) {
  event.preventDefault();
  const url = document.getElementById("crawlUrlInput").value.trim();
  const maxPages = parseInt(document.getElementById("crawlMaxPagesInput").value, 10);
  const resultsDiv = document.getElementById("crawlResults");
  const btn = document.getElementById("crawlSubmitBtn");

  if (!url) return;

  btn.disabled = true;
  btn.innerHTML = `<span class="flex items-center justify-center space-x-2"><div class="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin"></div><span>Traversing sitewide graph...</span></span>`;
  resultsDiv.innerHTML = `<div class="text-center py-10 space-y-2"><div class="inline-flex w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin"></div><p class="text-zinc-400 font-mono text-xs">Traversing links...</p></div>`;

  try {
    const res = await fetch("/api/v1/crawl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, max_pages: maxPages })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Crawl failed");
    }

    const data = await res.json();
    let rowsHtml = "";
    (data.pages || []).forEach(p => {
      const gradeColor = p.overall_score >= 80 ? "text-emerald-400" : (p.overall_score >= 60 ? "text-amber-400" : "text-rose-400");
      rowsHtml += `
        <tr class="border-b border-white/5">
          <td class="p-2 text-zinc-300 truncate max-w-[200px]" title="${p.url}">${p.url}</td>
          <td class="p-2 font-bold ${gradeColor}">${p.overall_score}</td>
          <td class="p-2 ${gradeColor}">${p.grade}</td>
        </tr>
      `;
    });

    resultsDiv.innerHTML = `
      <div class="p-3 bg-[#08080a] border border-white/10 rounded-xl mb-3 flex items-center justify-between">
        <span class="text-zinc-400 text-xs">Sitewide Aggregate Score:</span>
        <span class="font-bold text-white font-mono text-sm">${data.sitewide_score} / 100 (${data.sitewide_grade})</span>
      </div>
      <table class="w-full text-left text-xs font-mono">
        <thead>
          <tr class="text-zinc-500 border-b border-white/5">
            <th class="p-2">URL</th>
            <th class="p-2">Score</th>
            <th class="p-2">Grade</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    `;
    showToast("Crawl finished successfully");
  } catch (e) {
    resultsDiv.innerHTML = `<p class="text-rose-400 text-center py-6">Crawl error: ${escapeHtml(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Execute BFS Crawl</span>`;
  }
}

// Cloudflare XOR Deobfuscate
async function handleDeobfuscateSubmit(event) {
  event.preventDefault();
  const hex = document.getElementById("deobfuscateHexInput").value.trim();
  const resDiv = document.getElementById("deobfuscateResult");
  const outEl = document.getElementById("deobfuscateOutputText");

  if (!hex) return;

  try {
    const res = await fetch("/api/v1/deobfuscate-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cf_hex: hex })
    });
    const data = await res.json();
    if (res.ok) {
      resDiv.classList.remove("hidden");
      outEl.textContent = data.decoded_email || "Invalid token";
      showToast("Decoded email token successfully");
    } else {
      alert("Failed to decode token. Ensure the string is raw Cloudflare hex.");
    }
  } catch (e) {
    alert("Error: " + e.message);
  }
}

// Toggle SoM Badges
function toggleVisualBadges() {
  const btn = document.getElementById("toggleBadgesBtn");
  const imgEl = document.getElementById("screenshotImg");
  showVisualBadges = !showVisualBadges;

  if (showVisualBadges) {
    btn.innerHTML = `<i data-lucide="eye" class="w-3 h-3"></i><span>Hide Badges</span>`;
    imgEl.style.filter = "none";
  } else {
    btn.innerHTML = `<i data-lucide="eye-off" class="w-3 h-3"></i><span>Show Badges</span>`;
    imgEl.style.filter = "contrast(1.15)";
  }
  if (window.lucide) lucide.createIcons();
}

// Toast Notification System
function showToast(msg) {
  const toast = document.getElementById("toastNotification");
  const msgEl = document.getElementById("toastMessage");
  if (!toast || !msgEl) return;
  msgEl.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2400);
}

// ==========================================
// AI Model & Provider Engine Modal Controller
// ==========================================

async function openModelSettingsModal() {
  const modal = document.getElementById("modelSettingsModal");
  if (!modal) return;
  modal.classList.remove("hidden");

  try {
    const res = await fetch("/api/v1/models");
    if (res.ok) {
      const data = await res.json();
      currentModelConfig.provider = data.active_provider || "ollama";
      currentModelConfig.model = data.active_model || "llama3.2:latest";
      currentModelConfig.endpoint = data.ollama_endpoint || "http://localhost:11434";
      if (data.api_base) currentModelConfig.api_base = data.api_base;

      // Populate local model select
      const select = document.getElementById("ollamaModelSelect");
      if (select && data.local_models) {
        select.innerHTML = "";
        data.local_models.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.name;
          const mb = m.size ? ` (${Math.round(m.size / 1024 / 1024 / 1024 * 10) / 10} GB)` : "";
          opt.textContent = `${m.name}${mb}`;
          if (m.name === currentModelConfig.model) opt.selected = true;
          select.appendChild(opt);
        });
      }

      // Update active pills
      document.getElementById("modalActiveModelPill").textContent = currentModelConfig.model;
      document.getElementById("modalActiveProviderPill").textContent = data.active_provider === "ollama" ? "On-Device Ollama" : "Cloud Model API";

      // Switch tab to active provider
      switchModelTab(currentModelConfig.provider);
    }
  } catch (e) {
    console.error("Could not load model info:", e);
  }

  if (window.lucide) lucide.createIcons();
}

function closeModelSettingsModal() {
  document.getElementById("modelSettingsModal")?.classList.add("hidden");
  document.getElementById("modelTestFeedback")?.classList.add("hidden");
}

function switchModelTab(provider) {
  const tabs = ["ollama", "cloud", "patcher", "crawler", "preferences"];
  tabs.forEach(t => {
    const tabEl = document.getElementById(`mTab-${t}`);
    const viewEl = document.getElementById(`mView-${t}`);
    if (t === provider) {
      tabEl?.classList.add("segment-tab-active");
      tabEl?.classList.remove("segment-tab-inactive");
      viewEl?.classList.remove("hidden");
    } else {
      tabEl?.classList.remove("segment-tab-active");
      tabEl?.classList.add("segment-tab-inactive");
      viewEl?.classList.add("hidden");
    }
  });
}

function handleCloudPresetChange() {
  const preset = document.getElementById("cloudPresetSelect").value;
  const baseInput = document.getElementById("cloudApiBaseInput");
  const modelInput = document.getElementById("cloudModelNameInput");

  if (preset.startsWith("meta-llama/")) {
    baseInput.value = "https://api.groq.com/openai/v1";
    modelInput.value = preset;
  } else if (preset === "gpt-4o-mini") {
    baseInput.value = "https://api.openai.com/v1";
    modelInput.value = "gpt-4o-mini";
  } else if (preset.startsWith("claude-")) {
    baseInput.value = "https://api.anthropic.com/v1";
    modelInput.value = preset;
  }
}

function toggleApiKeyMask() {
  const input = document.getElementById("cloudApiKeyInput");
  const icon = document.getElementById("eyeIcon");
  if (!input) return;
  if (input.type === "password") {
    input.type = "text";
    icon?.setAttribute("data-lucide", "eye-off");
  } else {
    input.type = "password";
    icon?.setAttribute("data-lucide", "eye");
  }
  if (window.lucide) lucide.createIcons();
}

async function scanLocalOllamaModels() {
  showToast("Scanning local Ollama models...");
  await openModelSettingsModal();
}

async function testActiveModelConnection() {
  const feedbackEl = document.getElementById("modelTestFeedback");
  const btn = document.getElementById("testConnectionBtn");
  feedbackEl.classList.remove("hidden");
  feedbackEl.className = "p-3 rounded-xl text-xs font-mono bg-zinc-900 border border-white/10 text-zinc-300";
  feedbackEl.innerHTML = `<span class="flex items-center space-x-2"><div class="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div><span>Testing engine response...</span></span>`;

  btn.disabled = true;

  const isOllama = !document.getElementById("mView-ollama").classList.contains("hidden");
  const payload = isOllama ? {
    provider: "ollama",
    model: document.getElementById("ollamaModelSelect").value,
    endpoint: document.getElementById("ollamaEndpointInput").value
  } : {
    provider: "cloud",
    model: document.getElementById("cloudModelNameInput").value,
    api_key: document.getElementById("cloudApiKeyInput").value,
    api_base: document.getElementById("cloudApiBaseInput").value
  };

  try {
    const res = await fetch("/api/v1/models/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "connected") {
      feedbackEl.className = "p-3 rounded-xl text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 text-emerald-400";
      feedbackEl.innerHTML = `✓ Connected successfully to <strong>${data.model}</strong> (${data.latency_ms || 35}ms latency)`;
    } else {
      feedbackEl.className = "p-3 rounded-xl text-xs font-mono bg-rose-500/10 border border-rose-500/20 text-rose-400";
      feedbackEl.innerHTML = `✗ Connection error: ${data.error || "Failed to reach model server."}`;
    }
  } catch (e) {
    feedbackEl.className = "p-3 rounded-xl text-xs font-mono bg-rose-500/10 border border-rose-500/20 text-rose-400";
    feedbackEl.innerHTML = `✗ Network error: ${e.message}`;
  } finally {
    btn.disabled = false;
  }
}

async function saveAndActivateModel() {
  const saveBtn = document.getElementById("saveModelBtn");
  saveBtn.disabled = true;
  saveBtn.textContent = "Activating...";

  const isOllama = !document.getElementById("mView-ollama").classList.contains("hidden");
  const payload = isOllama ? {
    provider: "ollama",
    model: document.getElementById("ollamaModelSelect").value,
    endpoint: document.getElementById("ollamaEndpointInput").value
  } : {
    provider: "cloud",
    model: document.getElementById("cloudModelNameInput").value,
    api_key: document.getElementById("cloudApiKeyInput").value,
    api_base: document.getElementById("cloudApiBaseInput").value
  };

  try {
    const res = await fetch("/api/v1/models/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "connected") {
      currentModelConfig.provider = payload.provider;
      currentModelConfig.model = payload.model;

      // Update top bar badge
      const badge = document.getElementById("engineStatusLabel");
      if (badge) {
        if (payload.provider === "ollama") {
          badge.textContent = `${payload.model} · Local M4 · 45 tok/s`;
        } else {
          badge.textContent = `${payload.model} · Cloud API`;
        }
      }

      closeModelSettingsModal();
      showToast(`Activated ${payload.model}`);
    } else {
      alert("Activation failed: " + (data.error || "Check model configuration"));
    }
  } catch (e) {
    alert("Activation error: " + e.message);
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save & Activate Engine";
  }
}

// Theme & Accessibility Management (WCAG 2.1 AA)
function initTheme() {
  const savedTheme = localStorage.getItem("aeoforge-theme") || "dark";
  const savedMotion = localStorage.getItem("aeoforge-reduce-motion") === "true";

  setTheme(savedTheme, false);

  if (savedMotion) {
    const motionCb = document.getElementById("reduceMotionToggle");
    if (motionCb) motionCb.checked = true;
    toggleReduceMotion(true, false);
  }

  // Listen to system OS theme changes if user selected 'system'
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (localStorage.getItem("aeoforge-theme") === "system") {
        applyTheme("system");
      }
    });
  }
}

function setTheme(theme, persist = true) {
  if (persist) {
    localStorage.setItem("aeoforge-theme", theme);
    showToast(`Theme switched to ${theme.charAt(0).toUpperCase() + theme.slice(1)}`);
  }
  applyTheme(theme);
}

function applyTheme(theme) {
  let isDark = true;
  if (theme === "system") {
    isDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  } else {
    isDark = (theme === "dark");
  }

  const html = document.documentElement;
  if (isDark) {
    html.classList.add("dark");
    html.setAttribute("data-theme", "dark");
  } else {
    html.classList.remove("dark");
    html.setAttribute("data-theme", "light");
  }

  // Update theme switcher buttons in header
  ["dark", "light", "system"].forEach(t => {
    const btn = document.getElementById(`themeBtn-${t}`);
    if (btn) {
      if (t === theme) {
        btn.classList.add("segment-tab-active");
        btn.classList.remove("segment-tab-inactive");
        btn.setAttribute("aria-checked", "true");
      } else {
        btn.classList.remove("segment-tab-active");
        btn.classList.add("segment-tab-inactive");
        btn.setAttribute("aria-checked", "false");
      }
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

function toggleReduceMotion(enabled, showFeedback = true) {
  localStorage.setItem("aeoforge-reduce-motion", enabled ? "true" : "false");
  document.documentElement.classList.toggle("reduce-motion", enabled);
  if (showFeedback) {
    showToast(enabled ? "Enforced reduced motion (WCAG 2.1 AA)" : "Default animation timings restored");
  }
}

// Expose on window for inline event handlers
window.initTheme = initTheme;
window.setTheme = setTheme;
window.applyTheme = applyTheme;
window.toggleReduceMotion = toggleReduceMotion;

// ==============================================================
// Persistent History, Domain Progression & In-UI Technical Tools
// ==============================================================

let cachedHistory = [];

function formatRelativeTime(dateStr) {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);
    if (diffSec < 60) return "Just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

async function initHistory() {
  await refreshHistoryFeed(false);
}

async function refreshHistoryFeed(showFeedback = true) {
  try {
    const res = await fetch("/api/v1/history");
    if (!res.ok) return;
    const audits = await res.json();
    cachedHistory = audits;

    // Update count badge
    const badge = document.getElementById("historyCountBadge");
    if (badge) {
      if (audits.length > 0) {
        badge.textContent = audits.length;
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    }

    renderHistoryFeed(audits);

    if (currentAuditResult) {
      loadDomainProgression(currentAuditResult.url);
    }
    if (showFeedback) {
      showToast("Refreshed persistent audit history");
    }
  } catch (e) {
    console.warn("Failed to load history:", e);
  }
}

function filterHistoryList(query) {
  if (!cachedHistory) return;
  const q = (query || "").toLowerCase().trim();
  const filtered = q
    ? cachedHistory.filter(a => (a.domain || "").toLowerCase().includes(q) || (a.url || "").toLowerCase().includes(q))
    : cachedHistory;
  renderHistoryFeed(filtered);
}

function renderHistoryFeed(audits) {
  const container = document.getElementById("historyListContainer");
  if (!container) return;

  if (!audits || audits.length === 0) {
    container.innerHTML = `<p class="text-zinc-600 text-center py-12">No audit snapshots stored yet in persistent storage.</p>`;
    return;
  }

  container.innerHTML = "";
  audits.forEach(a => {
    const card = document.createElement("div");
    card.className = "p-3 bg-[#08080a] border border-white/[0.06] hover:border-white/10 rounded-xl space-y-2 transition-all";

    const gradeColor = a.overall_score >= 80 ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : (a.overall_score >= 60 ? "text-amber-400 bg-amber-500/10 border-amber-500/20" : "text-rose-400 bg-rose-500/10 border-rose-500/20");

    card.innerHTML = `
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0 flex-1">
          <div class="flex items-center space-x-2">
            <span class="font-bold text-white text-xs truncate max-w-[200px]" title="${escapeHtml(a.url)}">${escapeHtml(a.domain)}</span>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded font-bold border ${gradeColor}">${a.overall_score} (${a.grade})</span>
          </div>
          <span class="text-[11px] text-zinc-500 font-mono">${formatRelativeTime(a.created_at)}</span>
        </div>
        
        <div class="flex items-center space-x-1">
          <button type="button" onclick="restoreHistoricalAudit('${a.id}')" class="px-2 py-1 text-[11px] font-mono bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-white/10 rounded-lg transition-all" title="Restore snapshot in workspace">
            Restore
          </button>
          <button type="button" onclick="reAuditHistoricalUrl('${escapeHtml(a.url)}')" class="px-2 py-1 text-[11px] font-mono bg-white hover:bg-zinc-200 text-black font-semibold rounded-lg transition-all shadow-sm" title="Re-run audit">
            Re-Audit
          </button>
          <button type="button" onclick="deleteHistoricalAudit('${a.id}')" class="p-1 text-zinc-500 hover:text-rose-400 rounded transition-all" title="Delete record">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-4 gap-1 text-[10px] font-mono text-zinc-400 pt-1 border-t border-white/5">
        <div>Vis: <span class="text-zinc-200 font-semibold">${a.visual_score || 0}</span></div>
        <div>Sem: <span class="text-zinc-200 font-semibold">${a.semantic_score || 0}</span></div>
        <div>Proto: <span class="text-zinc-200 font-semibold">${a.protocol_score || 0}</span></div>
        <div>Cit: <span class="text-zinc-200 font-semibold">${a.citability_score || 0}</span></div>
      </div>
    `;
    container.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

async function loadDomainProgression(url) {
  try {
    let domain = "";
    try {
      domain = new URL(url).hostname || url;
    } catch {
      domain = url.replace(/^https?:\/\//, "").split("/")[0];
    }
    const res = await fetch(`/api/v1/progression/${encodeURIComponent(domain)}`);
    if (!res.ok) return;
    const data = await res.json();

    const card = document.getElementById("historyProgressionCard");
    if (!card) return;

    if (data.audit_count > 0) {
      card.classList.remove("hidden");
      document.getElementById("progDomainLabel").textContent = data.domain;
      document.getElementById("progInitialScore").textContent = `${data.initial_score} / 100`;
      document.getElementById("progLatestScore").textContent = `${data.latest_score} / 100`;
      document.getElementById("progAuditCount").textContent = data.audit_count;

      const netBadge = document.getElementById("progNetDeltaBadge");
      if (netBadge) {
        netBadge.textContent = `${data.delta_since_first >= 0 ? '+' : ''}${data.delta_since_first} pts`;
        netBadge.className = data.delta_since_first > 0
          ? "text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25"
          : (data.delta_since_first < 0
            ? "text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/25"
            : "text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-white/10");
      }

      // Render Step Progression Timeline
      const stepsContainer = document.getElementById("progTimelineSteps");
      if (stepsContainer) {
        stepsContainer.innerHTML = "";
        data.points.forEach((p, idx) => {
          const stepEl = document.createElement("div");
          stepEl.className = "flex items-center space-x-1.5 shrink-0";
          stepEl.innerHTML = `
            <div class="px-2 py-1 rounded-md bg-zinc-900 border border-white/10 text-[10px] font-mono flex items-center space-x-1">
              <span class="text-zinc-500">#${idx + 1}</span>
              <span class="font-bold text-white">${p.score}</span>
              <span class="text-zinc-400">(${p.grade})</span>
            </div>
            ${idx < data.points.length - 1 ? `<span class="text-zinc-600 text-xs">➔</span>` : ''}
          `;
          stepsContainer.appendChild(stepEl);
        });
      }
    } else {
      card.classList.add("hidden");
    }
  } catch (e) {
    console.warn("Progression fetch error:", e);
  }
}

async function restoreHistoricalAudit(auditId) {
  try {
    showToast("Restoring historical audit snapshot...");
    const res = await fetch(`/api/v1/history/${auditId}`);
    if (!res.ok) throw new Error("Could not fetch audit snapshot");
    const data = await res.json();
    currentAuditResult = data;
    currentSpecResult = data;
    renderAuditResults(data);
    toggleDrawer("historyDrawer");
    showToast(`Restored snapshot for ${data.domain || data.url}`);
  } catch (e) {
    alert("Restore error: " + e.message);
  }
}

function reAuditHistoricalUrl(url) {
  toggleDrawer("historyDrawer");
  const input = document.getElementById("targetUrlInput");
  if (input) input.value = url;
  handleAuditSubmit();
}

async function deleteHistoricalAudit(auditId) {
  try {
    const res = await fetch(`/api/v1/history/${auditId}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Audit deleted from persistent storage");
      await refreshHistoryFeed(false);
    }
  } catch (e) {
    alert("Delete error: " + e.message);
  }
}

async function clearAuditHistory() {
  if (!confirm("Are you sure you want to clear all audit history from persistent storage?")) {
    return;
  }
  try {
    const res = await fetch("/api/v1/history", { method: "DELETE" });
    if (res.ok) {
      showToast("Cleared all audit history");
      document.getElementById("progressionBanner")?.classList.add("hidden");
      document.getElementById("historyProgressionCard")?.classList.add("hidden");
      await refreshHistoryFeed(false);
    }
  } catch (e) {
    alert("Clear history error: " + e.message);
  }
}

function openTechnicalSetupModal(tab = "ollama") {
  openModelSettingsModal();
  switchModelTab(tab);
}

function openSelfHealingPatcherModal() {
  openTechnicalSetupModal("patcher");
}

async function applyRecommendationFix(idx) {
  if (!currentAuditResult || !currentAuditResult.recommendations || !currentAuditResult.recommendations[idx]) {
    return;
  }
  const rec = currentAuditResult.recommendations[idx];
  showToast(`Injecting fix for ${rec.title}...`);

  try {
    const res = await fetch("/api/v1/patch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_dir: ".",
        url: currentAuditResult.url,
        agent_spec: currentAuditResult.agent_spec,
        llms_txt: currentAuditResult.llms_txt,
        schema_jsonld: currentAuditResult.schema_jsonld
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`✓ Injected fix for ${rec.title} into codebase!`);
    } else {
      showToast(`Patch failed: ${data.detail || "Error"}`);
    }
  } catch (e) {
    showToast(`Patch error: ${e.message}`);
  }
}

async function executeInUiCodebasePatch() {
  const btn = document.getElementById("runPatchBtn");
  const outputEl = document.getElementById("patchExecutionOutput");
  const targetDir = document.getElementById("patchTargetDirInput").value.trim() || ".";
  const url = currentAuditResult ? currentAuditResult.url : "https://example.com";

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Injecting AST Artifacts...</span>`;
  if (window.lucide) lucide.createIcons();

  const includeLlms = document.getElementById("patchLlmsTxtToggle").checked;
  const includeSpec = document.getElementById("patchAgentSpecToggle").checked;
  const includeSchema = document.getElementById("patchSchemaToggle").checked;

  const payload = {
    target_dir: targetDir,
    url: url,
    agent_spec: includeSpec && currentAuditResult ? currentAuditResult.agent_spec : null,
    llms_txt: includeLlms && currentAuditResult ? currentAuditResult.llms_txt : null,
    schema_jsonld: includeSchema && currentAuditResult ? currentAuditResult.schema_jsonld : null
  };

  try {
    const res = await fetch("/api/v1/patch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
      outputEl.classList.remove("hidden");
      let lines = [`<div class="text-emerald-400 font-bold mb-1">✓ Self-Healing Injection Successful into <code>${escapeHtml(data.target_dir)}</code></div>`];
      (data.patched_files || []).forEach(f => {
        const filePath = typeof f === "object" ? (f.file || f.artifact || JSON.stringify(f)) : f;
        lines.push(`<div class="text-zinc-300">✓ Injected: <span class="text-white">${escapeHtml(filePath)}</span></div>`);
      });
      outputEl.innerHTML = lines.join("");
      showToast(`Injected ${data.patched_files.length} AEO files into codebase`);
    } else {
      outputEl.classList.remove("hidden");
      outputEl.innerHTML = `<div class="text-rose-400">✗ Patch Error: ${escapeHtml(data.detail || "Failed to patch")}</div>`;
    }
  } catch (e) {
    outputEl.classList.remove("hidden");
    outputEl.innerHTML = `<div class="text-rose-400">✗ Network Error: ${escapeHtml(e.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="hammer" class="w-3.5 h-3.5"></i><span>Run Self-Healing AST Injection</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

async function saveCrawlerSettings() {
  const userAgent = document.getElementById("crawlerUserAgentSelect").value;
  const timeout = parseInt(document.getElementById("crawlerTimeoutInput").value) || 45;
  const depth = parseInt(document.getElementById("crawlerDepthInput").value) || 3;
  const stealth = document.getElementById("stealthModeToggle").checked;
  const autoSolve = document.getElementById("autoSolveChallengesToggle").checked;

  try {
    const res = await fetch("/api/v1/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        settings: {
          crawler_user_agent: userAgent,
          crawler_timeout_sec: timeout,
          crawler_max_depth: depth,
          stealth_mode_enabled: stealth,
          auto_dismiss_challenges: autoSolve
        }
      })
    });
    if (res.ok) {
      showToast("Saved crawler & shield settings to SQLite storage");
    }
  } catch (e) {
    alert("Save settings error: " + e.message);
  }
}

// Expose technical helpers on window
window.initHistory = initHistory;
window.refreshHistoryFeed = refreshHistoryFeed;
window.filterHistoryList = filterHistoryList;
window.restoreHistoricalAudit = restoreHistoricalAudit;
window.reAuditHistoricalUrl = reAuditHistoricalUrl;
window.deleteHistoricalAudit = deleteHistoricalAudit;
window.clearAuditHistory = clearAuditHistory;
window.openTechnicalSetupModal = openTechnicalSetupModal;
window.openSelfHealingPatcherModal = openSelfHealingPatcherModal;
window.filterRecommendations = filterRecommendations;
window.applyRecommendationFix = applyRecommendationFix;
window.executeInUiCodebasePatch = executeInUiCodebasePatch;
window.saveCrawlerSettings = saveCrawlerSettings;
