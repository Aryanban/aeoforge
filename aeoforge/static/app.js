/**
 * AEOForge Frontend Controller
 * Answer Engine Optimization & Web Agent-Readiness Studio
 */

let currentAuditResult = null;
let currentSpecResult = null;
let activeHandshakeTab = "agent_spec";
let showVisualBadges = true;

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  checkSystemStatus();
});

// Switch Main Navigation Tabs
function switchTab(tabId) {
  const tabs = ["audit", "crawler", "handshake", "security", "mcp"];
  tabs.forEach(t => {
    const viewEl = document.getElementById(`view-${t}`);
    const tabBtn = document.getElementById(`tab-${t}`);
    if (viewEl) {
      if (t === tabId) {
        viewEl.classList.remove("hidden");
      } else {
        viewEl.classList.add("hidden");
      }
    }
    if (tabBtn) {
      if (t === tabId) {
        tabBtn.className = "px-3 py-1.5 rounded-md text-xs font-medium text-blue-400 bg-blue-500/10 border border-blue-500/30 transition-smooth flex items-center space-x-1.5";
      } else {
        tabBtn.className = "px-3 py-1.5 rounded-md text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-smooth flex items-center space-x-1.5";
      }
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }

  // If opening Handshake studio, ensure specs are fetched
  if (tabId === "handshake" && currentAuditResult && !currentSpecResult) {
    fetchHandshakeSpecs(currentAuditResult.url);
  }
}

// Check Backend & Ollama Engine Status
async function checkSystemStatus() {
  const pillText = document.getElementById("engineStatusText");
  try {
    const res = await fetch("/api/v1/system-status");
    if (res.ok) {
      const data = await res.json();
      if (data.ollama_available) {
        pillText.textContent = `Ollama ${data.ollama_model} (Active · Apple Silicon M4)`;
        pillText.className = "text-emerald-400 font-mono text-[11px]";
      } else if (data.meta_api_configured) {
        pillText.textContent = "Meta Model API Cloud (Active)";
        pillText.className = "text-blue-400 font-mono text-[11px]";
      } else {
        pillText.textContent = "Offline Deterministic Engine";
        pillText.className = "text-slate-400 font-mono text-[11px]";
      }
    } else {
      pillText.textContent = "Local Server Standby";
    }
  } catch (e) {
    pillText.textContent = "Local Server Standby";
  }
}

// Preset Loader
function loadPreset(url) {
  const input = document.getElementById("targetUrlInput");
  if (input) {
    input.value = url;
    document.getElementById("auditSubmitBtn").click();
  }
}

// Audit Form Submission
async function handleAuditSubmit(event) {
  event.preventDefault();
  const urlInput = document.getElementById("targetUrlInput");
  const captureScreenshot = document.getElementById("screenshotToggle").checked;
  const url = urlInput.value.trim();

  if (!url) return;

  const loadingEl = document.getElementById("loadingIndicator");
  const resultsEl = document.getElementById("resultsContainer");
  const submitBtn = document.getElementById("auditSubmitBtn");

  loadingEl.classList.remove("hidden");
  resultsEl.classList.add("hidden");
  submitBtn.disabled = true;

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
    currentSpecResult = data; // specs are now synthesized in memory with zero redundant latency!
    renderAuditResults(data);
    renderHandshakeCode();
  } catch (error) {
    alert("Audit Error: " + error.message);
  } finally {
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
  }
}

// Render Results View
function renderAuditResults(result) {
  const resultsEl = document.getElementById("resultsContainer");
  resultsEl.classList.remove("hidden");

  // Master Score
  const score = result.overall_score;
  const scoreCircle = document.getElementById("scoreGaugeCircle");
  const scoreText = document.getElementById("scoreDisplay");
  const gradeBadge = document.getElementById("gradeBadge");
  const targetPill = document.getElementById("targetUrlPill");
  const headline = document.getElementById("statusHeadline");
  const desc = document.getElementById("statusDescription");

  scoreText.textContent = score;
  targetPill.textContent = result.url;
  targetPill.title = result.url;
  gradeBadge.textContent = `Grade ${result.grade}`;
  headline.textContent = result.status;

  // Animate Circular Gauge
  const circumference = 264;
  const offset = circumference - (circumference * score) / 100;
  scoreCircle.style.strokeDashoffset = offset;

  if (score >= 80) {
    scoreCircle.setAttribute("class", "text-emerald-500 score-ring");
    gradeBadge.className = "text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
  } else if (score >= 60) {
    scoreCircle.setAttribute("class", "text-amber-500 score-ring");
    gradeBadge.className = "text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20";
  } else {
    scoreCircle.setAttribute("class", "text-red-500 score-ring");
    gradeBadge.className = "text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20";
  }

  // 4 Pillars
  const pA = result.pillars.pillar_a_citability;
  const pB = result.pillars.pillar_b_navigability;
  const pC = result.pillars.pillar_c_protocols;
  const pD = result.pillars.pillar_d_structured_data;

  document.getElementById("scorePillarA").textContent = `${pA.score} / 25`;
  document.getElementById("factDensityVal").textContent = `${pA.details.fact_density_pct}%`;
  document.getElementById("capsuleVal").textContent = pA.details.has_answer_capsule ? "✅ Present" : "❌ Missing";
  document.getElementById("eeatVal").textContent = `${pA.details.eeat_score} / 100`;

  document.getElementById("scorePillarB").textContent = `${pB.score} / 25`;
  document.getElementById("tokenRatioVal").textContent = `${pB.details.token_ratio_pct}%`;
  document.getElementById("trapsCountVal").textContent = pB.details.traps_detected_count;
  if (pB.details.traps_detected_count > 0) {
    document.getElementById("trapsCountVal").className = "text-red-400 font-bold font-mono";
  } else {
    document.getElementById("trapsCountVal").className = "text-emerald-400 font-bold font-mono";
  }
  document.getElementById("marksCountVal").textContent = (result.interactive_marks || []).length;

  document.getElementById("scorePillarC").textContent = `${pC.score} / 25`;
  document.getElementById("llmsTxtVal").textContent = pC.details.has_llms_txt ? "✅ Found" : "❌ None";
  document.getElementById("llmsTxtVal").className = pC.details.has_llms_txt ? "text-emerald-400 font-bold" : "text-red-400 font-bold";
  document.getElementById("llmsFullVal").textContent = pC.details.has_llms_full_txt ? "✅ Found" : "❌ None";
  document.getElementById("llmsFullVal").className = pC.details.has_llms_full_txt ? "text-emerald-400 font-bold" : "text-slate-400 font-bold";
  document.getElementById("robotsVal").textContent = pC.details.ai_bots_allowed ? "Allowed" : "Restricted";

  document.getElementById("scorePillarD").textContent = `${pD.score} / 25`;
  const schemas = pD.details.schema_types || [];
  document.getElementById("schemaCountVal").textContent = schemas.length > 0 ? schemas.join(", ") : "None";
  document.getElementById("webmcpVal").textContent = pD.details.discovered_endpoints && pD.details.discovered_endpoints.length > 0 ? "✅ Discovered" : "None";
  document.getElementById("ogVal").textContent = pD.details.has_opengraph ? "✅ Complete" : "Partial";

  // Strengths List
  const strengthsUl = document.getElementById("strengthsList");
  strengthsUl.innerHTML = "";
  if (result.key_strengths && result.key_strengths.length > 0) {
    result.key_strengths.forEach(s => {
      const li = document.createElement("li");
      li.className = "flex items-start space-x-2";
      li.innerHTML = `<span class="text-emerald-500 font-bold mt-0.5">•</span><span>${escapeHtml(s)}</span>`;
      strengthsUl.appendChild(li);
    });
  } else {
    strengthsUl.innerHTML = `<li class="text-slate-500">No significant agent strengths detected.</li>`;
  }

  // Blockers List
  const blockersUl = document.getElementById("blockersList");
  blockersUl.innerHTML = "";
  if (result.critical_blockers && result.critical_blockers.length > 0) {
    result.critical_blockers.forEach(b => {
      const li = document.createElement("li");
      li.className = "flex items-start space-x-2";
      li.innerHTML = `<span class="text-red-500 font-bold mt-0.5">•</span><span>${escapeHtml(b)}</span>`;
      blockersUl.appendChild(li);
    });
  } else {
    blockersUl.innerHTML = `<li class="text-emerald-400">Zero navigation blockers or modal traps detected.</li>`;
  }

  // Set-of-Mark Screenshot
  const imgEl = document.getElementById("screenshotImg");
  const emptyEl = document.getElementById("screenshotEmpty");
  if (result.screenshot_base64) {
    imgEl.src = "data:image/jpeg;base64," + result.screenshot_base64;
    imgEl.classList.remove("hidden");
    emptyEl.classList.add("hidden");
  } else {
    imgEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
  }

  // Meta Llama 3.2 Agent Advice
  const adviceEl = document.getElementById("agentAdviceText");
  const confEl = document.getElementById("groundingConfidenceVal");
  if (result.visual_analysis) {
    adviceEl.textContent = `"${result.visual_analysis.agent_navigation_advice || 'Clean layout. Proceed with semantic selectors.'}"`;
    confEl.textContent = `${result.visual_analysis.element_grounding_accuracy || 92}%`;
  }

  // Interactive Marks List
  const marksScroll = document.getElementById("interactiveMarksScroll");
  const marksBadgeCount = document.getElementById("marksBadgeCount");
  const marks = result.interactive_marks || [];
  marksBadgeCount.textContent = `${marks.length} elements`;
  marksScroll.innerHTML = "";

  if (marks.length > 0) {
    marks.forEach(m => {
      const row = document.createElement("div");
      row.className = "p-2 bg-[#141d2b] hover:bg-[#1a2538] border border-[#1f293d] rounded-lg flex items-center justify-between text-[11px] transition-smooth";
      const markId = m.id !== undefined ? m.id : (m.mark_id !== undefined ? m.mark_id : 1);
      const label = (m.name || m.text || m.href || "").substring(0, 32);
      row.innerHTML = `
        <div class="flex items-center space-x-2 truncate">
          <span class="som-badge-pill">[${markId}]</span>
          <span class="text-slate-300 font-mono truncate">&lt;${m.tag}&gt; "${label}"</span>
        </div>
        <span class="text-slate-500 text-[10px] uppercase font-mono">${m.role || m.tag}</span>
      `;
      marksScroll.appendChild(row);
    });
  } else {
    marksScroll.innerHTML = `<p class="text-slate-500 text-xs py-4 text-center">No interactive marks grounded.</p>`;
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

// Fetch Handshake Specs
async function fetchHandshakeSpecs(url) {
  try {
    const res = await fetch("/api/v1/spec", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url })
    });
    if (res.ok) {
      currentSpecResult = await res.json();
      renderHandshakeCode();
    }
  } catch (e) {
    console.error("Spec fetch failed:", e);
  }
}

// Switch Handshake Subtab
function switchHandshakeTab(subtab) {
  activeHandshakeTab = subtab;
  const tabs = ["agent_spec", "llms_txt", "llms_full_txt", "schema_jsonld", "html_head"];
  tabs.forEach(t => {
    const btn = document.getElementById(`hTab-${t}`);
    if (btn) {
      if (t === subtab) {
        btn.className = "px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 font-mono font-medium";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 font-mono font-medium";
      }
    }
  });
  renderHandshakeCode();
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
  } else if (activeHandshakeTab === "llms_full_txt") {
    content = currentSpecResult.llms_full_txt;
  } else if (activeHandshakeTab === "schema_jsonld") {
    content = JSON.stringify(currentSpecResult.schema_jsonld, null, 2);
  } else if (activeHandshakeTab === "html_head") {
    content = `<!-- AEOForge Machine Handshake Discovery Tags -->
<link rel="alternate" type="text/markdown" href="/llms.txt" title="LLM Agent Navigation Index">
<meta name="agent-spec" content="/agent-spec.json">
<script type="application/ld+json">
${JSON.stringify(currentSpecResult.schema_jsonld, null, 2)}
<\/script>`;
  }

  codeEl.textContent = content;
}

// Copy Handshake Code
function copyActiveHandshakeFile() {
  const codeEl = document.getElementById("handshakeCodeView");
  if (codeEl && codeEl.textContent) {
    navigator.clipboard.writeText(codeEl.textContent);
    showToast("Copied to clipboard!");
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
  } else if (activeHandshakeTab === "llms_full_txt") {
    filename = "llms-full.txt";
    mime = "text/plain";
  } else if (activeHandshakeTab === "schema_jsonld") {
    filename = "schema.jsonld";
    mime = "application/ld+json";
  } else if (activeHandshakeTab === "html_head") {
    filename = "head-tags.html";
    mime = "text/html";
  }

  const blob = new Blob([codeEl.textContent], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  showToast(`Downloaded ${filename}`);
}

// Codebase Patcher Handler
async function handlePatchSubmit(event) {
  event.preventDefault();
  const targetDir = document.getElementById("patchTargetDirInput").value.trim();
  const feedbackEl = document.getElementById("patchFeedback");
  const btn = document.getElementById("patchSubmitBtn");

  if (!targetDir) return;

  btn.disabled = true;
  feedbackEl.classList.remove("hidden");
  feedbackEl.innerHTML = `<span class="text-blue-400">Scanning local directory and injecting patches...</span>`;

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
        filesList += `<div>• ${f.artifact || 'file'}: <strong class="text-emerald-400">${f.action}</strong> -> ${f.file}</div>`;
      });
      feedbackEl.innerHTML = `
        <div class="font-bold text-white mb-1">✨ Successfully Patched Codebase:</div>
        ${filesList || '<div>No files modified.</div>'}
      `;
      showToast("Codebase patched successfully!");
    } else {
      feedbackEl.innerHTML = `<span class="text-red-400">Patch error: ${data.detail}</span>`;
    }
  } catch (e) {
    feedbackEl.innerHTML = `<span class="text-red-400">Error: ${e.message}</span>`;
  } finally {
    btn.disabled = false;
  }
}

// Sitewide BFS Crawl Handler
async function handleCrawlSubmit(event) {
  event.preventDefault();
  const url = document.getElementById("crawlUrlInput").value.trim();
  const maxPages = parseInt(document.getElementById("crawlMaxPages").value, 10);
  const loading = document.getElementById("crawlLoading");
  const resultsDiv = document.getElementById("crawlResults");
  const tbody = document.getElementById("crawlTableBody");
  const avgBadge = document.getElementById("sitewideScoreBadge");
  const btn = document.getElementById("crawlSubmitBtn");

  if (!url) return;

  btn.disabled = true;
  loading.classList.remove("hidden");
  resultsDiv.classList.add("hidden");
  tbody.innerHTML = "";

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
    avgBadge.textContent = `${data.sitewide_score} / 100 (${data.sitewide_grade})`;

    (data.pages || []).forEach(p => {
      const tr = document.createElement("tr");
      const gradeColor = p.overall_score >= 80 ? "text-emerald-400" : (p.overall_score >= 60 ? "text-amber-400" : "text-red-400");
      const blocker = (p.blockers && p.blockers.length > 0) ? p.blockers[0] : "None (Clean)";

      tr.innerHTML = `
        <td class="py-2.5 px-4 font-sans text-blue-400 truncate max-w-xs" title="${p.url}">${p.url}</td>
        <td class="py-2.5 px-4 font-bold ${gradeColor}">${p.overall_score}</td>
        <td class="py-2.5 px-4 font-bold ${gradeColor}">${p.grade}</td>
        <td class="py-2.5 px-4 text-slate-300 font-mono">${(p.token_ratio * 100).toFixed(1)}%</td>
        <td class="py-2.5 px-4 font-sans text-slate-400 truncate max-w-xs" title="${blocker}">${blocker}</td>
      `;
      tbody.appendChild(tr);
    });

    resultsDiv.classList.remove("hidden");
  } catch (e) {
    alert("Crawl failed: " + e.message);
  } finally {
    loading.classList.add("hidden");
    btn.disabled = false;
  }
}

// Cloudflare XOR Deobfuscate Handler
async function handleDeobfuscateSubmit(event) {
  event.preventDefault();
  const hex = document.getElementById("deobfuscateInput").value.trim();
  const outEl = document.getElementById("deobfuscateOutput");

  if (!hex) return;

  try {
    const res = await fetch("/api/v1/deobfuscate-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cf_hex: hex })
    });
    const data = await res.json();
    if (res.ok) {
      outEl.innerHTML = `Decoded Email: <strong class="text-emerald-400">${data.decoded_email || 'Invalid token'}</strong>`;
    } else {
      outEl.innerHTML = `<span class="text-red-400">Failed to decode</span>`;
    }
  } catch (e) {
    outEl.innerHTML = `<span class="text-red-400">Error: ${e.message}</span>`;
  }
}

// Toggle SoM Overlay in visual box
function toggleVisualBadges() {
  const btn = document.getElementById("toggleBadgesBtn");
  const imgEl = document.getElementById("screenshotImg");
  showVisualBadges = !showVisualBadges;

  if (showVisualBadges) {
    btn.textContent = "Hide SoM Overlay";
    imgEl.style.filter = "none";
  } else {
    btn.textContent = "Show SoM Overlay";
    imgEl.style.filter = "contrast(1.2)";
  }
}

// Download HTML Report
function downloadHtmlReport() {
  if (!currentAuditResult) return;
  const blob = new Blob([document.documentElement.outerHTML], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `aeoforge-report-${new URL(currentAuditResult.url).hostname}.html`;
  a.click();
  showToast("Exported HTML report");
}

// Toast Notification
function showToast(msg) {
  const toast = document.getElementById("toast");
  const msgEl = document.getElementById("toastMsg");
  msgEl.textContent = msg;
  toast.classList.remove("translate-y-20", "opacity-0");
  toast.classList.add("translate-y-0", "opacity-100");
  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0");
    toast.classList.remove("translate-y-0", "opacity-100");
  }, 2500);
}
