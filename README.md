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

Clone and run the entire platform with a **single command** (handles Python virtualenv, dependencies, Playwright browser, and Ollama check automatically):

```bash
# 1. Clone the repo
git clone https://github.com/Aryanban/aeoforge.git
cd aeoforge

# 2. Automated setup & launch Web UI on http://localhost:8000
./setup.sh --start
```

Open **`http://localhost:8000`** in your browser. Done.

### Other One-Liner Commands
```bash
# Run an instant audit from your terminal
./setup.sh --audit https://dholeramap.com

# Run the automated test suite (25 tests)
./setup.sh --test
```

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

## 🛠️ Key Capabilities

* **Visual Grounding (Set-of-Mark)**: Tags interactive buttons and inputs with numeric visual badges on high-res screenshots for VLM reasoning.
* **Competitor Lab**: Side-by-side URL comparison showing why competitors outrank you in answer engines.
* **In-UI AST Codebase Patcher**: Click *"Apply Fix to Codebase"* to automatically write `llms.txt` and inject JSON-LD into your local HTML/React/Next.js repo.
* **Persistent History & Progression Drawer (`⌘H`)**: Tracks domain score evolution over time (`+18 pts` net delta).
* **Native MCP Server**: Directly plug AEOForge tools into Claude Desktop, Cursor, Antigravity, or Cline.

---

## 🖥️ CLI Reference

```bash
# 1. Audit a URL with rich terminal scorecard
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com

# 2. Multi-page internal link crawl with sitewide score
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com --crawl --max-pages 5

# 3. Generate machine-executable agent-spec.json and llms.txt
.venv/bin/python -m aeoforge.cli spec https://dholeramap.com --out-dir ./specs

# 4. Patch a local web repository
.venv/bin/python -m aeoforge.cli patch --target-dir ./my-web-project
```

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

## 🔌 Universal Agent Compatibility (MCP & API)

### Model Context Protocol (MCP)
Add AEOForge to your Claude Desktop or Cursor configuration:
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

### Programmatic REST API
Agents can discover all available tools and schemas dynamically:
```bash
curl -s http://127.0.0.1:8000/api/v1/tools | jq .
```

> **For AI Coding Agents**: See **[`AGENTS.md`](AGENTS.md)** for architecture, internal APIs, CLI flags, and implementation guidelines.

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
