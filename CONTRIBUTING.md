# Contributing to AEOForge

Thank you for your interest in contributing to **AEOForge**! We are building an open, local-first Answer Engine Optimization (AEO) and agent-readiness platform for AI answer engines and autonomous agents.

Whether you are fixing a bug, adding an agent protocol check, improving citability scoring, or optimizing the frontend UI, your contributions are welcome.

---

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aryanban/aeoforge.git
   cd aeoforge
   ```

2. **Automated Environment Setup:**
   Run the unified setup script (creates virtual environment, installs dependencies, checks Playwright):
   ```bash
   ./setup.sh
   ```

3. **Activate Virtual Environment manually (optional):**
   ```bash
   source .venv/bin/activate
   ```

---

## 🧪 Testing Guidelines

Before opening a pull request, ensure all tests pass cleanly:

```bash
# Run pytest across all test suites
.venv/bin/pytest -v

# Run UI verification (headless browser check)
python scripts/verify_ui.py
```

- Every new feature or bug fix must include a corresponding test in `tests/`.
- Ensure tests run deterministically with zero flaky failures.

---

## 📐 Coding Standards & Principles

1. **Surgical, Minimal Changes:**
   - Solve problems with the smallest complete diff.
   - Do not reformat unrelated code, introduce heavy dependencies, or add speculative abstractions.
2. **Zero-Build UI Policy:**
   - The web interface (`aeoforge/templates/index.html`) runs natively in the browser without npm, Webpack, or Vite build steps.
   - Maintain pure modern CSS custom properties and standard browser APIs.
3. **Deterministic Fallbacks:**
   - Any LLM-assisted analysis must include a deterministic regex/AST fallback so audits never fail when an LLM daemon is offline.
4. **Commit Conventions:**
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)`: New capability or check
   - `fix(...)`: Bug fix or patch
   - `test(...)`: New or updated tests
   - `docs(...)`: Documentation improvements
   - `chore(...)`: Tooling, workflow, or dependency maintenance

---

## 🚀 Submitting a Pull Request

1. Create a dedicated branch for your work:
   ```bash
   git checkout -b fix/issue-description
   ```
2. Commit your changes with conventional messages.
3. Push to your fork and submit a PR against `master`.
4. Follow the PR template: describe the problem, summarize the fix, and attach test output.

---

## 💬 Community & Code of Conduct

- Be respectful, constructive, and collaborative in code reviews and discussions.
- We follow standard open-source community standards to make everyone feel welcome.
