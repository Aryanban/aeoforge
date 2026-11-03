/**
 * AEOForge Ultra-Premium Engineering Studio Controller
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

  // Keyboard shortcut: ⌘K or / to focus search
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      document.getElementById("targetUrlInput")?.focus();
    } else if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
      e.preventDefault();
      document.getElementById("targetUrlInput")?.focus();
    }
  });
});

// Check System Status & Ollama Connectivity
async function checkSystemStatus() {
  const badgeLabel = document.getElementById("engineStatusLabel");
  try {
    const res = await fetch("/api/v1/system-status");
    if (res.ok) {
      const data = await res.json();
      if (data.ollama_available) {
        badgeLabel.textContent = `llama3.2 · on-device · 45 tok/s`;
      } else if (data.meta_api_configured) {
        badgeLabel.textContent = `meta-cloud · llama-3.2-vision`;
      } else {
        badgeLabel.textContent = `offline-deterministic`;
      }
    }
  } catch (e) {
    badgeLabel.textContent = `server-offline`;
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

// Quick Preset Loader
function loadPreset(domain) {
  const input = document.getElementById("targetUrlInput");
  if (input) {
    input.value = domain;
    document.getElementById("auditSubmitBtn")?.click();
  }
}

// Audit Form Submission
async function handleAuditSubmit(event) {
  event.preventDefault();
  let url = document.getElementById("targetUrlInput").value.trim();
  const captureScreenshot = document.getElementById("screenshotToggle").checked;

  if (!url) return;
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }

  const loadingEl = document.getElementById("loadingIndicator");
  const submitBtn = document.getElementById("auditSubmitBtn");

  loadingEl.classList.remove("hidden");
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
    currentSpecResult = data; // In-memory specs synthesized with zero redundant roundtrips!
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
  // Master Score & Telemetry
  const score = result.overall_score;
  document.getElementById("scoreDisplay").textContent = score;
  document.getElementById("targetUrlPill").textContent = result.url;
  document.getElementById("targetUrlPill").title = result.url;
  
  const gradeBadge = document.getElementById("gradeBadge");
  gradeBadge.textContent = `Grade ${result.grade}`;
  document.getElementById("statusHeadline").textContent = result.status;

  // Grade color scheme
  if (score >= 80) {
    gradeBadge.className = "px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono";
  } else if (score >= 60) {
    gradeBadge.className = "px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono";
  } else {
    gradeBadge.className = "px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono";
  }

  // 4 Foundation Tracks Telemetry
  const pA = result.pillars.pillar_a_citability;
  const pB = result.pillars.pillar_b_navigability;
  const pC = result.pillars.pillar_c_protocols;
  const pD = result.pillars.pillar_d_structured_data;

  // Telemetry Bars
  document.getElementById("scorePillarA").textContent = `${pA.score} / 25`;
  document.getElementById("barPillarA").style.width = `${Math.min(100, (pA.score / 25) * 100)}%`;
  document.getElementById("factDensityVal").textContent = `${pA.details.fact_density_pct}%`;
  document.getElementById("capsuleVal").textContent = pA.details.has_answer_capsule ? "Capsule: Yes" : "Capsule: None";

  document.getElementById("scorePillarB").textContent = `${pB.score} / 25`;
  document.getElementById("barPillarB").style.width = `${Math.min(100, (pB.score / 25) * 100)}%`;
  document.getElementById("tokenRatioVal").textContent = `${pB.details.token_ratio_pct}%`;
  document.getElementById("trapsCountVal").textContent = pB.details.traps_detected_count;

  document.getElementById("scorePillarC").textContent = `${pC.score} / 25`;
  document.getElementById("barPillarC").style.width = `${Math.min(100, (pC.score / 25) * 100)}%`;
  document.getElementById("llmsTxtVal").textContent = pC.details.has_llms_txt ? "Found" : "None";
  document.getElementById("robotsVal").textContent = pC.details.ai_bots_allowed ? "Allowed" : "Restricted";

  document.getElementById("scorePillarD").textContent = `${pD.score} / 25`;
  document.getElementById("barPillarD").style.width = `${Math.min(100, (pD.score / 25) * 100)}%`;
  const schemas = pD.details.schema_types || [];
  document.getElementById("schemaCountVal").textContent = schemas.length;
  document.getElementById("webmcpVal").textContent = pD.details.discovered_endpoints && pD.details.discovered_endpoints.length > 0 ? "WebMCP" : "None";

  // Strengths List
  const strengthsUl = document.getElementById("strengthsUl");
  strengthsUl.innerHTML = "";
  if (result.key_strengths && result.key_strengths.length > 0) {
    result.key_strengths.forEach(s => {
      const li = document.createElement("li");
      li.innerHTML = escapeHtml(s);
      strengthsUl.appendChild(li);
    });
  } else {
    strengthsUl.innerHTML = `<li>No significant agent strengths detected.</li>`;
  }

  // Blockers List
  const blockersUl = document.getElementById("blockersUl");
  blockersUl.innerHTML = "";
  if (result.critical_blockers && result.critical_blockers.length > 0) {
    result.critical_blockers.forEach(b => {
      const li = document.createElement("li");
      li.innerHTML = escapeHtml(b);
      blockersUl.appendChild(li);
    });
  } else {
    blockersUl.innerHTML = `<li>Zero navigation blockers or modal traps detected. Clean layout.</li>`;
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

  // Meta Llama 3.2 Tactical Navigation Plan
  const adviceEl = document.getElementById("agentAdviceText");
  if (result.visual_analysis && result.visual_analysis.agent_navigation_advice) {
    adviceEl.textContent = result.visual_analysis.agent_navigation_advice;
  } else {
    adviceEl.textContent = "Clean layout. Proceed with semantic selectors.";
  }

  // Interactive Marks List
  const marksScroll = document.getElementById("interactiveMarksScroll");
  const marksBadgeCount = document.getElementById("marksBadgeCount");
  const marks = result.interactive_marks || [];
  marksBadgeCount.textContent = `${marks.length} grounded`;
  marksScroll.innerHTML = "";

  if (marks.length > 0) {
    marks.forEach(m => {
      const row = document.createElement("div");
      row.className = "p-2 bg-zinc-900 hover:bg-zinc-800 border border-white/5 rounded-lg flex items-center justify-between text-[11px] transition-all";
      const markId = m.id !== undefined ? m.id : (m.mark_id !== undefined ? m.mark_id : 1);
      const label = (m.name || m.text || m.href || "").substring(0, 32);
      row.innerHTML = `
        <div class="flex items-center space-x-2 truncate">
          <span class="som-badge-pill">[${markId}]</span>
          <span class="text-zinc-300 font-mono truncate">&lt;${m.tag}&gt; "${escapeHtml(label)}"</span>
        </div>
        <span class="text-zinc-500 text-[10px] uppercase font-mono">${m.role || m.tag}</span>
      `;
      marksScroll.appendChild(row);
    });
  } else {
    marksScroll.innerHTML = `<p class="text-zinc-600 text-xs py-3 text-center">No interactive marks grounded.</p>`;
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

// Handshake Subtabs Switching
function switchHandshakeTab(subtab) {
  activeHandshakeTab = subtab;
  const tabs = ["agent_spec", "llms_txt", "schema_jsonld", "blockers"];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`hTab-${t}`);
    if (btn) {
      if (t === subtab) {
        btn.className = "px-2.5 py-1 rounded-md bg-white text-black font-semibold";
      } else {
        btn.className = "px-2.5 py-1 rounded-md text-zinc-400 hover:text-white bg-zinc-900 border border-white/5";
      }
    }
  });

  const codeView = document.getElementById("handshakeCodeView");
  const blockersView = document.getElementById("blockersView");

  if (subtab === "blockers") {
    codeView.classList.add("hidden");
    blockersView.classList.remove("hidden");
  } else {
    codeView.classList.remove("hidden");
    blockersView.classList.add("hidden");
    renderHandshakeCode();
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

// Copy Llama 3.2 Agent Advice
function copyAgentAdvice() {
  const advice = document.getElementById("agentAdviceText").textContent;
  navigator.clipboard.writeText(advice);
  showToast("Copied tactical agent plan");
}

// 1-Click Codebase Patcher
async function handlePatchSubmit(event) {
  event.preventDefault();
  const targetDir = document.getElementById("patchTargetDirInput").value.trim();
  const feedbackEl = document.getElementById("patchFeedback");
  const btn = document.getElementById("patchSubmitBtn");

  if (!targetDir) return;

  btn.disabled = true;
  feedbackEl.classList.remove("hidden");
  feedbackEl.innerHTML = `<span>Applying patches to ${escapeHtml(targetDir)}...</span>`;

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
        <div class="font-bold text-white mb-1">✨ Successfully Patched Codebase:</div>
        ${filesList || '<div>No files modified.</div>'}
      `;
      showToast("Codebase patched successfully");
    } else {
      feedbackEl.innerHTML = `<span class="text-rose-400">Patch error: ${data.detail}</span>`;
    }
  } catch (e) {
    feedbackEl.innerHTML = `<span class="text-rose-400">Error: ${e.message}</span>`;
  } finally {
    btn.disabled = false;
  }
}

// Sitewide BFS Crawl
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
      const gradeColor = p.overall_score >= 80 ? "text-emerald-400" : (p.overall_score >= 60 ? "text-amber-400" : "text-rose-400");

      tr.innerHTML = `
        <td class="p-2 text-zinc-300 truncate max-w-[200px]" title="${p.url}">${p.url}</td>
        <td class="p-2 font-bold ${gradeColor}">${p.overall_score}</td>
        <td class="p-2 ${gradeColor}">${p.grade}</td>
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

// Cloudflare XOR Deobfuscate
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
      outEl.innerHTML = `Decoded Email: <strong class="text-white">${data.decoded_email || 'Invalid token'}</strong>`;
    } else {
      outEl.innerHTML = `<span class="text-rose-400">Failed to decode</span>`;
    }
  } catch (e) {
    outEl.innerHTML = `<span class="text-rose-400">Error: ${e.message}</span>`;
  }
}

// Toggle SoM Overlay
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

// Scroll to Handshake Section
function scrollToHandshake() {
  document.getElementById("handshakeSection")?.scrollIntoView({ behavior: "smooth" });
}

// Export Full HTML Report
function exportCurrentReport() {
  if (!currentAuditResult) {
    showToast("Please run an audit first");
    return;
  }
  const blob = new Blob([document.documentElement.outerHTML], { type: "text/html" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `aeoforge-${new URL(currentAuditResult.url).hostname}.html`;
  a.click();
  showToast("Report exported");
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
  }, 2200);
}
