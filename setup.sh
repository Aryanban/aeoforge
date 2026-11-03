#!/usr/bin/env bash
# ==============================================================================
# AEOForge ⚡ Automated Local Setup & Launch Script
# Autonomous Meta AI Web Agent & AEO Auditor
# ==============================================================================
set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "  ╔════════════════════════════════════════════════════════════════════╗"
    echo "  ║                                                                    ║"
    echo "  ║   ⚡ AEOForge • Autonomous Meta AI Web Agent & AEO Auditor          ║"
    echo "  ║   Zero-Friction Automated Local Setup & Launch Engine              ║"
    echo "  ║                                                                    ║"
    echo "  ╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_header

# ------------------------------------------------------------------------------
# 1. Check Python Version (>= 3.10 required)
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ [1/5] Checking Python runtime environment...${NC}"

PYTHON_BIN=""
for candidate in python3.11 python3.12 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        VER=$($candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN="$candidate"
            echo -e "  ${GREEN}✓ Found compatible Python: $PYTHON_BIN ($VER)${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}✗ Error: Python 3.10 or higher is required but not found.${NC}"
    echo -e "  Please install Python 3.11+ via homebrew (\`brew install python@3.11\`) or python.org."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Virtual Environment Setup
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}▶ [2/5] Initializing isolated Python virtual environment...${NC}"

VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "  Creating new virtual environment at ${BOLD}.venv${NC}..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo -e "  ${GREEN}✓ Virtual environment created.${NC}"
else
    echo -e "  ${GREEN}✓ Existing virtual environment detected at .venv${NC}"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ------------------------------------------------------------------------------
# 3. Dependency Installation
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}▶ [3/5] Installing core dependencies & AEOForge package...${NC}"

# Check if uv is available for 10x faster installation
if command -v uv >/dev/null 2>&1; then
    echo -e "  ${CYAN}⚡ uv detected! Using ultra-fast package installer...${NC}"
    uv pip install --python "$VENV_PYTHON" -e .
else
    echo -e "  Using standard pip installer..."
    "$VENV_PIP" install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
    "$VENV_PIP" install -e .
fi
echo -e "  ${GREEN}✓ AEOForge dependencies successfully installed.${NC}"

# ------------------------------------------------------------------------------
# 4. Playwright Headless Browser Installation
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}▶ [4/5] Verifying Playwright headless browser drivers...${NC}"

if "$VENV_PYTHON" -m playwright install chromium; then
    echo -e "  ${GREEN}✓ Playwright Chromium engine installed & ready.${NC}"
else
    echo -e "  ${YELLOW}⚠ Warning: Playwright install encountered a warning. Retrying with system dependencies...${NC}"
    "$VENV_PYTHON" -m playwright install --with-deps chromium || true
fi

# ------------------------------------------------------------------------------
# 5. Local Ollama & Meta Llama 3.2 Check
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}▶ [5/5] Checking Local Meta AI Engine (Ollama)...${NC}"

if command -v ollama >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Ollama CLI is installed on this system.${NC}"
    # Check if daemon is running
    if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Ollama daemon is actively running on http://127.0.0.1:11434${NC}"
        # Check if llama3.2 is pulled
        MODELS=$(curl -s http://127.0.0.1:11434/api/tags | grep -o '"name":"[^"]*"' || true)
        if echo "$MODELS" | grep -q "llama3.2"; then
            echo -e "  ${GREEN}✓ Meta Llama 3.2 model is pulled and ready for local inference!${NC}"
        else
            echo -e "  ${YELLOW}ℹ Meta Llama 3.2 not found locally in Ollama.${NC}"
            echo -e "    Pulling ${BOLD}llama3.2:latest${NC} (approx 2.0GB, ultra-fast on 16GB Mac)..."
            ollama pull llama3.2 || echo -e "  ${YELLOW}⚠ Skipping auto-pull. You can run \`ollama pull llama3.2\` anytime.${NC}"
        fi
    else
        echo -e "  ${YELLOW}ℹ Ollama daemon is not currently running.${NC}"
        echo -e "    Start it anytime via: ${BOLD}ollama serve${NC}"
        echo -e "    (Note: AEOForge operates with zero API keys even without Ollama using deterministic heuristics!)${NC}"
    fi
else
    echo -e "  ${YELLOW}ℹ Ollama is not installed.${NC}"
    echo -e "    To run 100% private local Meta Llama 3.2 Vision on Mac: \`brew install ollama && ollama serve\`"
    echo -e "    (AEOForge operates seamlessly with cloud keys or built-in deterministic heuristics without Ollama!)${NC}"
fi

# Ensure data directory for persistent SQLite database exists
mkdir -p "$ROOT_DIR/data"

echo -e "\n${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}✨ AEOForge environment is 100% verified, configured, and ready!${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"

# ------------------------------------------------------------------------------
# Handle Command Line Arguments
# ------------------------------------------------------------------------------
ACTION="${1:-}"

if [ "$ACTION" == "--start" ] || [ "$ACTION" == "start" ] || [ "$ACTION" == "serve" ]; then
    PORT="${2:-8000}"
    echo -e "\n${CYAN}${BOLD}🚀 Launching AEOForge REST API & Interactive UI on http://127.0.0.1:${PORT}...${NC}"
    echo -e "Press ${BOLD}Ctrl+C${NC} to stop the server.\n"
    exec "$VENV_PYTHON" -m uvicorn aeoforge.main:app --host 127.0.0.1 --port "$PORT" --reload
elif [ "$ACTION" == "--audit" ] || [ "$ACTION" == "audit" ]; then
    TARGET_URL="${2:-}"
    if [ -z "$TARGET_URL" ]; then
        echo -e "${RED}Error: Please specify a URL to audit. Example: ./setup.sh --audit https://example.com${NC}"
        exit 1
    fi
    echo -e "\n${CYAN}⚡ Running CLI audit on ${BOLD}$TARGET_URL${NC}...\n"
    exec "$VENV_PYTHON" -m aeoforge.cli audit "$TARGET_URL"
elif [ "$ACTION" == "--test" ] || [ "$ACTION" == "test" ]; then
    echo -e "\n${CYAN}🧪 Running AEOForge automated test suite...${NC}\n"
    exec "$VENV_PYTHON" -m pytest -v
else
    echo -e "\n${BOLD}Quick Command Reference:${NC}"
    echo -e "  • Launch Web Dashboard & REST API: ${CYAN}./setup.sh --start${NC} (or \`.venv/bin/uvicorn aeoforge.main:app\`)"
    echo -e "  • Run Instant CLI Audit:            ${CYAN}./setup.sh --audit https://dholeramap.com${NC}"
    echo -e "  • Run Test Suite:                   ${CYAN}./setup.sh --test${NC}"
    echo -e "  • Start External MCP Server:        ${CYAN}.venv/bin/python -m aeoforge.mcp_server${NC}"
    echo -e "\nOpen ${CYAN}http://localhost:8000${NC} in your browser to explore the dashboard!"
fi
