# NEBULA-FORGE ◆ The Agentic Orchestrator

> A high-performance TUI for orchestrating SWE agent workflows.
> Built with Python · Textual · Rich · Tokyo Night

```
███╗   ██╗███████╗██████╗ ██╗   ██╗██╗      █████╗
████╗  ██║██╔════╝██╔══██╗██║   ██║██║     ██╔══██╗
██╔██╗ ██║█████╗  ██████╔╝██║   ██║██║     ███████║
██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║██║     ██╔══██║
██║ ╚████║███████╗██████╔╝╚██████╔╝███████╗██║  ██║
╚═╝  ╚═══╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
```

---

## Install

```bash
git clone <this-repo>
cd nebula-forge
chmod +x install.sh && ./install.sh

# Activate and launch
source .venv/bin/activate
nebula-forge           # or: nf  or: python -m nebula_forge
```

**Requirements:** Python 3.11+ · macOS / Linux / WSL

---

## Modules

| Key | Module | Does |
|-----|--------|------|
| F1 | ◈ The Vault | API keys, config, environment exports |
| F2 | ⊕ Skill Factory | Create/browse/copy global skills |
| F3 | ⬡ Project Provisioner | One-click CLAUDE.md + gemini.json + skill injection |
| F4 | ◉ Blueprint Generator | Refactor · Migration · Architecture blueprints |

---

## Architecture

```
nebula_forge/
├── app.py              ← NebulaApp (main Textual App)
├── vault.py            ← Vault (key management)
├── provisioner.py      ← Provisioner (all file system logic)
├── models.py           ← Pydantic models (all data)
├── themes/
│   └── tokyo_night.tcss
└── screens/
    ├── splash.py       ← ASCII art + boot sequence
    ├── wizard.py       ← First-launch onboarding wizard
    ├── vault_screen.py ← Config management
    ├── skill_factory.py← Skill registry + creation
    ├── project_screen.py← Project detection + bootstrap
    └── blueprint.py    ← Blueprint generation
```

## Global Directory Structure Created

```
~/.nebula-forge/vault.json      ← API keys (chmod 600)
~/.claude/skills/               ← Global skill registry
~/.nebula/agents/               ← Agent configurations
~/.nebula/logs/                 ← Logs
~/.nebula/blueprints/           ← Generated blueprints
```

---

## Dev Mode

```bash
# Hot-reload during development
textual run --dev nebula_forge/app.py

# Textual console (inspect DOM/events)
textual console
```
