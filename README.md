# AEOForge ⚡
> **The Open-Source Lighthouse for AI Agents & Answer Engines.**  
> Built for the **Meta Global AI Developer Hackathon 2026** • Powered by **Meta Llama 3.2 Vision**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Meta AI: Llama 3.2](https://img.shields.io/badge/Meta_AI-Llama_3.2-0668E1?style=flat-square&logo=meta&logoColor=white)](https://ai.meta.com/llama/)
[![Playwright](https://img.shields.io/badge/Headless-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![Standard: llms.txt](https://img.shields.io/badge/Protocol-llms.txt-008080?style=flat-square)](https://llmstxt.org)
[![MCP Server](https://img.shields.io/badge/MCP-Native_Tools-8A2BE2?style=flat-square)](https://modelcontextprotocol.io)

---

## ⚡ Value Proposition

The web was built for **human retinas**. Today, the web is browsed by **Answer Engines** (Meta AI, Perplexity, ChatGPT Search) and **Autonomous Web Agents** (Claude Computer Use, browser-use).

When AI visits your website:
- **95% of pages fail**: Massive DOM bloat (50,000+ tokens) wastes LLM context windows.
- **Agents get trapped**: Unlabelled buttons, cookie popups, and modal overlays stall agents in infinite loops.
- **Content is hallucinated or ignored**: Sites lack structured fact-triplets, `/llms.txt` manifests, and Schema.org entity graphs.

**AEOForge solves this in seconds.** It crawls your website with local headless vision, scores it across 4 AEO Pillars (0–100), grounds interactive elements with Set-of-Mark tags, and auto-generates machine-executable `agent-spec.json`, `llms.txt`, and Schema.org patches.

---

## 🚀 Download & Quickstart

Clone and launch the entire platform with a **single command** (handles Python virtualenv, dependencies, Playwright browser, and Ollama check automatically):

```bash
# 1. Clone the repo
git clone https://github.com/Aryanban/aeoforge.git
cd aeoforge

# 2. Automated setup & launch Web UI (automatically opens your browser!)
./setup.sh --start
```

Your browser will automatically open to **`http://localhost:8000`**.

```bash
# Direct terminal commands to open the Web UI at any time:
open http://localhost:8000         # macOS
xdg-open http://localhost:8000     # Linux
start http://localhost:8000        # Windows
# or via CLI flag:
.venv/bin/python -m aeoforge.cli serve --open
```

---

## 🎯 3 Ways to Use AEOForge

### 1. In Your Browser (Localhost Web UI)
Launch via `./setup.sh --start` and navigate to `http://localhost:8000`:
- **Live 4-Pillar Scorecard**: Enter any URL to get an instant 0–100 AEO score, grade, and prioritized action plan.
- **Set-of-Mark Visual Grounding**: View your site through the eyes of an AI agent with numbered visual bounding boxes on interactive elements.
- **Competitor Lab**: Compare two domains side-by-side to uncover why competitors rank higher in AI Overviews.
- **One-Click Codebase Patching**: Click *"Apply Fix to Codebase"* in the UI to automatically inject `llms.txt` and Schema.org JSON-LD into your project.
- **Persistent Progression Drawer (`⌘H`)**: Review historical audit progressions and verify net score gains (`+18 pts`).

### 2. From Your Terminal (CLI)
Run audits, crawls, and codebase patches directly from your command line:
```bash
# Audit a single page with rich terminal scorecard
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com

# Multi-page BFS crawl with sitewide score
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com --crawl --max-pages 5

# Export machine-executable agent-spec.json and compliant llms.txt
.venv/bin/python -m aeoforge.cli spec https://dholeramap.com --out-dir ./output

# Automatically patch local HTML/Next.js repo with missing llms.txt and JSON-LD
.venv/bin/python -m aeoforge.cli patch ./my-website-repo --url https://dholeramap.com
```

### 3. By Autonomous AI Agents (Claude Code, Antigravity, Cursor, Codex)
Empower your autonomous AI coding assistants (**Claude Code**, **Antigravity**, **Cursor**, **OpenAI Codex**) to audit, diagnose, and self-heal your website's AEO without manual human intervention.

#### The Autonomous Self-Healing Agent Loop:
1. **Audit**: Agent calls `aeoforge_audit(url)` to identify missing `llms.txt`, unlabelled buttons, or missing JSON-LD schemas.
2. **Spec Generation**: Agent calls `aeoforge_generate_spec(url)` to produce exact machine-executable fixes.
3. **AST Self-Healing Patch**: Agent invokes `aeoforge patch <dir>` or directly applies the generated Schema.org JSON-LD and `llms.txt` to the codebase.
4. **Autonomous Verification**: Agent re-runs `aeoforge_audit(url)` to verify the score jump (`+20 pts`) before committing!

#### Configure External Agents via MCP (Model Context Protocol):
Add AEOForge to your Claude Desktop, Cursor, or Antigravity configuration (`claude_desktop_config.json`, `.cursor/mcp.json`, or `~/.gemini/antigravity/mcp_config.json`):
```json
{
  "mcpServers": {
    "aeoforge": {
      "command": "/absolute/path/to/aeoforge/.venv/bin/python",
      "args": ["-m", "aeoforge.mcp_server"],
      "cwd": "/absolute/path/to/aeoforge"
    }
  }
}
```

#### Programmatic Agent Manifest:
Agents can dynamically query all endpoints and schemas at runtime:
```bash
curl -s http://127.0.0.1:8000/api/v1/tools | jq .
```

> **Detailed Agent Manual**: See **[`AGENTS.md`](AGENTS.md)** for architecture, internal APIs, and autonomous tool-calling loops.

---

## 💻 100% Local Sovereignty (Runs on a 16GB Laptop)

Zero cloud subscriptions. Zero mandatory API keys. Runs entirely on your local machine:

| Component | Local Engine | Resource Footprint |
| :--- | :--- | :--- |
| **Reasoning & Citability** | Local Meta Llama 3.2 via [Ollama](https://ollama.com) (`ollama pull llama3.2`) | ~2.0 GB RAM (ultra-fast on M-series Mac / PC) |
| **Browser Navigator** | Local Playwright Chromium (stealth mode) | ~300 MB RAM |
| **Persistent Storage** | Local SQLite (`data/aeoforge.db`) with WAL mode | Instant zero-latency queries |
| **Codebase Patcher** | Local AST injector (adds `llms.txt` & JSON-LD) | Local filesystem |
| **Fallback** | Built-in deterministic regex & DOM heuristics | Runs immediately if Ollama is off |

*(Optional: Cloud keys for Meta Model API, Gemini, Claude, or OpenAI can be added in the UI settings).*

---

## 📊 The 4 AEO Pillars (0–100 Score)

```
       0 ────────────── 50 ────────────── 75 ────────────── 100
      [    F / D    ]     [     C     ]     [     B     ]     [     A     ]
      Critical Traps    Needs Optimize    Agent-Ready       Benchmark
```

| Pillar | Max Pts | What We Measure | Why AI Cares |
| :--- | :---: | :--- | :--- |
| **Pillar A: Citability** | 25 | Fact-triplet density (`<S, P, O>`), 40–60 word answer capsules, E-E-A-T credentials | Answer engines need concise, verifiable assertions to cite your site in AI Overviews. |
| **Pillar B: Navigability** | 25 | Text-to-DOM ratio, semantic landmarks (`<main>`, `<nav>`), zero modal/cookie traps | Traps and bloated HTML burn LLM tokens and trigger agent timeouts. |
| **Pillar C: Machine Protocols** | 25 | Spec-compliant `/llms.txt`, `robots.txt` AI crawler directives | Dictates whether AI crawlers (`Meta-ExternalAgent`, `PerplexityBot`) are allowed to index you. |
| **Pillar D: Structured Data** | 25 | Schema.org JSON-LD graphs, hidden public JSON API endpoints | Allows agents to query clean structured data without parsing messy HTML. |

---

## 🔍 Real-World Audit: `dholeramap.com`

```
Target URL:        https://dholeramap.com/
Overall Score:     66.0 / 100 (Grade C)
Key Strengths:     Valid /llms.txt detected • Zero modal traps • 100% accessible element names
Critical Blockers: robots.txt disallows web crawlers • Zero Schema.org graphs • Heavy DOM bloat (4.2% text)
Quick Fixes:       Allow Meta-ExternalAgent in robots.txt • Inject Organization JSON-LD • Add author byline
```

---

## 🧪 Testing

```bash
./setup.sh --test
# or
.venv/bin/pytest -v
```

---

## 📜 License & Attribution

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.  
Copyright © 2026 Aryan Bansal. Built with pride for the Meta Global AI Developer Hackathon 2026.
