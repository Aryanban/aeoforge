/**
 * AEOForge • Ultra-Premium Engineering Studio Controller
 * Modern Interactive State, Cross-Highlighting, Live Score Simulator & Bundle Export
 */

let currentAuditResult = null;
let currentSpecResult = null;
let activeHandshakeTab = "recommendations";
let showVisualBadges = true;

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
  if (window.lucide) {
    lucide.createIcons();
  }
  checkSystemStatus();

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    // ⌘K or / to focus search
    if (((e.metaKey || e.ctrlKey) && e.key === "k") || (e.key === "/" && document.activeElement?.tagName !== "INPUT")) {
      e.preventDefault();
      document.getElementById("targetUrlInput")?.focus();
      document.getElementById("targetUrlInput")?.select();
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
    // Escape: Close all open drawers
    else if (e.key === "Escape") {
      ["compareDrawer", "crawlerDrawer", "deobfuscatorDrawer", "mcpDrawer"].forEach(id => {
        document.getElementById(id)?.classList.add("hidden");
      });
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
        badgeLabel.textContent = `local-engine · deterministic`;
      }
    }
  } catch (e) {
    if (badgeLabel) badgeLabel.textContent = `engine-standby`;
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
    currentSpecResult = data; // In-memory specs synthesized at 0ms latency
    renderAuditResults(data);
    showToast("Audit completed successfully");
  } catch (error) {
    alert("Audit Error: " + error.message);
  } finally {
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
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

  // Meta Llama 3.2 Advice
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
        btn.className = "px-3 py-1.5 rounded-lg segment-tab-active transition-all";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg segment-tab-inactive transition-all";
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

// Render Recommendations & Score Simulator
function renderRecommendations(recs, potentialScore) {
  const currentSim = document.getElementById("currentSimScore");
  const potentialSim = document.getElementById("potentialSimScore");
  const gradeBadge = document.getElementById("potentialGradeBadge");
  const listEl = document.getElementById("recommendationsList");

  if (!listEl) return;

  const baseScore = currentAuditResult ? currentAuditResult.overall_score : 0;
  if (currentSim) currentSim.textContent = `${baseScore} / 100`;
  if (potentialSim) potentialSim.textContent = `${potentialScore} / 100`;

  let pGrade = potentialScore >= 90 ? "Grade A+" : (potentialScore >= 80 ? "Grade A" : (potentialScore >= 70 ? "Grade B" : "Grade C"));
  if (gradeBadge) gradeBadge.textContent = pGrade;

  listEl.innerHTML = "";
  if (!recs || recs.length === 0) {
    listEl.innerHTML = `<p class="text-zinc-600 text-xs py-4 text-center">No recommendations required. Clean agent configuration.</p>`;
    return;
  }

  recs.forEach((r, idx) => {
    const card = document.createElement("div");
    card.className = "p-3.5 bg-[#08080a] border border-white/[0.06] hover:border-white/10 rounded-xl space-y-2 transition-all";
    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <label class="flex items-start space-x-2.5 cursor-pointer flex-1">
          <input type="checkbox" checked data-boost="${r.score_boost}" onchange="recalculateSimScore()" class="rec-toggle rounded border-zinc-700 bg-zinc-900 text-white focus:ring-0 w-3.5 h-3.5 mt-0.5 accent-white">
          <div>
            <div class="flex items-center space-x-2">
              <span class="font-semibold text-white text-xs">${escapeHtml(r.title)}</span>
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">+${r.score_boost} pts</span>
            </div>
            <p class="text-xs text-zinc-400 mt-1 leading-relaxed">${escapeHtml(r.description)}</p>
          </div>
        </label>
        ${r.code_snippet ? `
          <button onclick="copySnippet(${idx})" class="text-xs font-mono px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-white/10 text-zinc-300 hover:text-white rounded-lg transition-all whitespace-nowrap flex items-center space-x-1">
            <i data-lucide="copy" class="w-3 h-3"></i>
            <span>Copy</span>
          </button>
        ` : ''}
      </div>
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
      showToast("Copied recommendation snippet");
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
    showToast("Copied Cloudflare WAF rule");
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
    alert("Comparison error: " + e.message);
  } finally {
    loading.classList.add("hidden");
    btn.disabled = false;
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
    showToast(`Downloaded aeoforge-${domain}-bundle.zip`);
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
  const maxPages = parseInt(document.getElementById("crawlMaxPagesInput").value, 10);
  const resultsDiv = document.getElementById("crawlResults");
  const btn = document.getElementById("crawlSubmitBtn");

  if (!url) return;

  btn.disabled = true;
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
    showToast("Crawl finished");
  } catch (e) {
    resultsDiv.innerHTML = `<p class="text-rose-400 text-center py-6">Crawl error: ${escapeHtml(e.message)}</p>`;
  } finally {
    btn.disabled = false;
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
      showToast("Decoded email token");
    } else {
      alert("Failed to decode token");
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
  }, 2200);
}
