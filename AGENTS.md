# AGENTS.md — Autonomous AI Agent Operating Manual
> **For Autonomous AI Coding Agents, IDE Extensions & Multi-Agent Swarms**  
> Compatible with: **Cursor**, **Windsurf**, **Claude Code**, **Antigravity**, **Cline**, **GitHub Copilot Workspace**, and **Aider**.

---

## ⚡ 1. Repository Essence & Architecture

**AEOForge** is an open-source, local-first Answer Engine Optimization (AEO) and Agent-Readiness platform. It acts as an autonomous auditor and navigation compiler that evaluates websites for AI agents (Meta AI, Perplexity, ChatGPT Search, Claude Computer Use) and answer engines.

### Directory Layout & Key Modules
```
clever-volta/
├── aeoforge/                      # Core Python Package
│   ├── main.py                    # FastAPI application, REST endpoints, and Web UI mount
│   ├── cli.py                     # Rich CLI interface (audit, spec, patch, serve)
│   ├── config.py                  # Pydantic v2 settings (env variables, model defaults)
│   ├── storage.py                 # SQLite persistent storage engine (WAL mode, progression tracking)
│   ├── mcp_server.py              # Model Context Protocol (MCP) server for external AI tools
│   ├── deobfuscator.py            # Cloudflare XOR cipher & anti-bot deobfuscator
│   ├── navigator/
│   │   └── browser.py             # Stealth Playwright headless navigator, a11y tree & Set-of-Mark (SoM)
│   ├── scorer/
│   │   ├── engine.py              # 4-Pillar AEO Scoring Engine (Citability, Navigability, Protocols, Schema)
│   │   ├── citability.py          # Pillar A: Fact-triplet density, definition blocks, E-E-A-T
│   │   ├── navigability.py        # Pillar B: DOM token cost, a11y landmarks, trap detection
│   │   ├── protocols.py           # Pillar C: llms.txt validation, robots.txt AI bot directives
│   │   ├── structured_data.py     # Pillar D: Schema.org JSON-LD validator & hidden API discovery
│   │   └── recommendations.py     # Recommendation engine & Cloudflare WAF/worker rule generator
│   ├── spec/
│   │   ├── spec_generator.py      # Generates machine-executable agent-spec.json
│   │   ├── llmstxt_gen.py         # Generates compliant llms.txt & llms-full.txt
│   │   └── schema_gen.py          # Auto-generates Schema.org JSON-LD graphs
│   ├── patcher/
│   │   └── ast_patcher.py         # Self-healing AST codebase patcher (HTML/Next.js/React injection)
│   └── templates/
│       └── index.html             # Vanilla, high-performance UI (No build step required)
├── tests/                         # Pytest test suite (25+ tests covering API, Scorer, Storage, MCP)
├── scripts/
│   ├── verify_ui.py               # Playwright headless UI verification script
│   └── start_ollama.sh            # Background Ollama manager
├── setup.sh                       # Single-instruction automated setup script for humans and agents
├── pyproject.toml                 # Package definition & dependency list
├── README.md                      # Human developer documentation & visual guide
└── AGENTS.md                      # This file (AI agent manual)
```

---

## 🛠️ 2. Environment Setup & Execution (Single-Command)

Any AI agent operating in this repository can configure the entire environment with a single command:

```bash
# Automated setup (installs virtualenv, dependencies, Playwright browser, checks Ollama)
./setup.sh

# Run all test suites
./setup.sh --test
# or directly:
.venv/bin/pytest -v

# Launch the REST API & Web UI on port 8000
./setup.sh --start 8000
# or directly:
.venv/bin/uvicorn aeoforge.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🤖 3. Programmatic API & Tool Manifest (`/api/v1/tools`)

When building autonomous agents or tool-calling loops, agents should query `GET /api/v1/tools` to discover all available endpoints and input/output schemas dynamically:

```bash
curl -s http://127.0.0.1:8000/api/v1/tools | jq .
```

### Essential Endpoints for Agents

| Endpoint | Method | Payload / Params | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/audit` | `POST` | `{"url": "https://...", "capture_screenshot": true}` | Performs 4-pillar AEO audit, returns 0–100 score, grade, visual tags, and blockers. |
| `/api/v1/compare` | `POST` | `{"url_a": "https://...", "url_b": "https://..."}` | Direct side-by-side AEO competitive comparison between two domains. |
| `/api/v1/spec` | `POST` | `{"url": "https://..."}` | Generates machine-readable `agent-spec.json`, `llms.txt`, and Schema.org JSON-LD. |
| `/api/v1/history` | `GET` | `?limit=50&domain=example.com` | Retrieves persistent audit records from SQLite database. |
| `/api/v1/progression/{domain}` | `GET` | `{domain:path}` | Returns historical progression curve, net delta (`+X pts`), and audit timeline. |
| `/api/v1/models` | `GET` | None | Returns active AI model, Ollama local availability, and configured provider. |
| `/api/v1/models` | `POST` | `{"provider": "ollama", "model": "llama3.2"}` | Switches active AI model (Ollama, Meta Model API, Anthropic, Gemini, OpenAI). |
| `/api/v1/settings` | `GET` / `POST` | Key-value settings JSON | Reads or updates user preferences, crawler stealth mode, and API keys. |
| `/api/v1/patch` | `POST` | `{"target_dir": "./path", "spec": {...}}` | AST-based codebase patcher that writes `llms.txt` and injects JSON-LD into index.html. |
| `/api/v1/deobfuscate` | `POST` | `{"html": "..."}` | Decodes Cloudflare email-protection ciphers (`data-cfemail`). |

---

## 💻 4. CLI Execution for Autonomous Agents

Agents running shell commands can directly invoke the CLI module:

```bash
# 1. Audit a single URL with JSON output
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com --json

# 2. Multi-page BFS crawl (internal link discovery)
.venv/bin/python -m aeoforge.cli audit https://dholeramap.com --crawl --max-pages 5 --json

# 3. Generate Agent Navigation Spec and llms.txt to an output directory
.venv/bin/python -m aeoforge.cli spec https://dholeramap.com --out-dir ./output

# 4. Patch a local web repository with self-healing specifications
.venv/bin/python -m aeoforge.cli patch --target-dir /path/to/web-repo
```

---

## 🔌 5. Model Context Protocol (MCP) Server Integration

AEOForge exposes a native MCP server at `aeoforge.mcp_server`. Agents in Claude Desktop, Cursor, Antigravity, or Cline can invoke AEOForge tools natively.

### Configuration Snippet (`claude_desktop_config.json` or `.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "aeoforge": {
      "command": "/absolute/path/to/clever-volta/.venv/bin/python",
      "args": ["-m", "aeoforge.mcp_server"],
      "cwd": "/absolute/path/to/clever-volta"
    }
  }
}
```

### Native MCP Tools Available:
1. `aeoforge_audit(url: str)`: Audits target site across 4 pillars, calculates score & grade.
2. `aeoforge_generate_spec(url: str)`: Emits machine-executable `agent-spec.json` and `llms.txt`.
3. `aeoforge_verify_citability(text: str)`: Analyzes text passage for fact-triplets and answer capsules.
4. `aeoforge_detect_traps(url: str)`: Detects cookie consent walls, modal overlays, and affordance traps.
5. `aeoforge_deobfuscate_cloudflare(html_or_code: str)`: Decodes obfuscated Cloudflare email tokens.

---

## 🧠 6. Local vs. Cloud Inference Hierarchy

AEOForge is designed for **100% Local Sovereignty** with zero required cloud subscriptions:

1. **Local Ollama (Default Priority)**:
   - Endpoint: `http://127.0.0.1:11434`
   - Default Model: `llama3.2` or `llama3.2-vision`
   - Zero cost, zero latency to cloud, 100% private.
2. **Cloud Model Providers**:
   - Meta Model API (`META_MODEL_API_KEY`)
   - Anthropic Claude (`ANTHROPIC_API_KEY`)
   - Google Gemini (`GEMINI_API_KEY`)
   - OpenAI (`OPENAI_API_KEY`)
   - Groq / OpenRouter (`GROQ_API_KEY`, `OPENROUTER_API_KEY`)
3. **Deterministic Fallback**:
   - If no LLM daemon or API key is available, AEOForge automatically falls back to deterministic AST and regex heuristics. The audit **never fails**.

---

## 🗄️ 7. Persistent SQLite Storage Engine

- **Database Path**: `data/aeoforge.db` (auto-created on first run).
- **Driver**: Built-in Python `sqlite3` with `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`.
- **Tables**:
  - `audits`: Stores full audit payloads, pillar scores, timestamp, domain, recommendations count.
  - `settings`: Key-value JSON store for user preferences, dark/light theme, API keys, crawler settings.
  - `patches`: Records of applied codebase patches, target directories, and modified files.
- **Progression Logic**:
  - Every audit on a domain automatically queries historical records to compute `baseline_score`, `latest_score`, and `net_delta`.
  - Progression data is returned in both the REST API and CLI output.

---

## 📐 8. Developer Guidelines for AI Agents Modifying This Codebase

When writing code or refactoring within this repository, follow these non-negotiable rules:

1. **Minimal Surgical Changes (`/ponytail` principle)**:
   - Solve tasks with the smallest complete diff.
   - Do not introduce massive external dependencies or heavy JS frameworks when vanilla JS / CSS solves the requirement.
2. **Preserve Zero-Build UI**:
   - The UI in `aeoforge/templates/index.html` runs without npm, Webpack, or Vite build steps.
   - Keep it standalone, reactive, and responsive using modern CSS custom properties and native DOM APIs.
3. **Always Run Tests Before Reporting Completion**:
   - Execute `.venv/bin/pytest` and verify 100% pass rate.
   - If UI changes were made, run `scripts/verify_ui.py` to confirm zero console errors.
4. **Maintain Privacy & Safe Sandboxing**:
   - Never commit `.env` or sensitive API keys.
   - Quarantined planning documents (`reference.md`, `architecture.md`, `implementation.md`) are gitignored and must remain strictly local.
