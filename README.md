# NEBULA-FORGE ◆ The Agentic Orchestrator

NEBULA-FORGE is a terminal-native control center for AI-assisted software engineering.
It helps you manage skills, project context, vault secrets, session replay, radar diagnostics,
MCP plugin scaffolding, and team sync workflows from one Textual TUI.

## Core Capabilities

- Vault profiles + API key management
- Skill Factory (create, compose, marketplace, cookbook, sync)
- Project Provisioner with Ghost Diff previews
- Context Architect for AGENTS.md
- Session Replay timeline for local agent logs
- Forge Radar project health checks
- MCP Builder for TypeScript server scaffolds
- Theme engine + command palette shortcuts

## Quick Start

## Requirements

- Python 3.11+
- macOS / Linux / Windows

## Install from source

```bash
git clone <this-repo>
cd nebula-forge
chmod +x install.sh && ./install.sh
source .venv/bin/activate
nf
```

You can also run:

```bash
nebula-forge
python -m nebula_forge
```

## Keyboard Map

| Key | Module |
| --- | --- |
| F1 | ◈ The Vault |
| F2 | ⊕ Skill Factory |
| F3 | ⬡ Project Provisioner |
| F4 | ◉ Blueprint Generator |
| F5 | ◎ Forge Radar |
| F6 | ◉ Session Replay |
| F7 | ⬡ MCP Builder |
| ` | Command Palette |
| Ctrl+R | Refresh current module |
| Q | Quit |

## Skill Cookbook (In-App)

PRDv2 cookbook examples are available directly in Skill Factory.

Path: `F2` → `Cookbook`

Includes one-click actions:

- Load into Composer
- Install Global
- Install Local

Seed examples:

- `git-workflow`
- `prompt-engineer`
- `test-guardian`

See detailed cookbook usage in [docs/SKILL_COOKBOOK.md](docs/SKILL_COOKBOOK.md).

## Testing

Run the local test suite:

```bash
python -m pip install -e .
python -m pip install pytest
pytest -q
```

## CI + Release Pipeline

This repository includes:

- CI workflow: [/.github/workflows/ci.yml](.github/workflows/ci.yml)
- Release workflow: [/.github/workflows/release.yml](.github/workflows/release.yml)

Release workflow builds and publishes three executable archives:

- macOS
- Linux
- Windows

Trigger by pushing a version tag:

```bash
git tag v1.1.0
git push origin v1.1.0
```

Release details: [docs/RELEASES.md](docs/RELEASES.md)

## Documentation

- User guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- Skill cookbook: [docs/SKILL_COOKBOOK.md](docs/SKILL_COOKBOOK.md)
- Release + binaries: [docs/RELEASES.md](docs/RELEASES.md)

## Development

```bash
textual run --dev nebula_forge/app.py
```
