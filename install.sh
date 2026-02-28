#!/bin/bash
# ════════════════════════════════════════════════════
#  NEBULA-FORGE — Installer
#  Run: chmod +x install.sh && ./install.sh
# ════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN}  ◆  NEBULA-FORGE Installer  ◆${NC}"
echo ""

# Check Python 3.11+
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python 3.11+ required. Install from python.org${NC}"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MIN=$(python3 -c "import sys; print(1 if sys.version_info >= (3, 11) else 0)")
if [ "$PY_MIN" = "0" ]; then
    echo -e "${RED}✗ Python 3.11+ required. Found $PY_VER${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PY_VER${NC}"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate || . .venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  NEBULA-FORGE installed!             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  Activate venv:  ${CYAN}source .venv/bin/activate${NC}"
echo -e "  Launch:         ${CYAN}nebula-forge${NC}  or  ${CYAN}nf${NC}"
echo -e "                  ${CYAN}python -m nebula_forge${NC}"
echo ""
echo -e "  Dev mode:       ${CYAN}textual run nebula_forge/app.py${NC}"
echo ""
