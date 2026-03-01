# NEBULA-FORGE User Guide

This guide explains day-to-day usage of NEBULA-FORGE v2 foundations.

## Start the App

```bash
nf
```

or:

```bash
nebula-forge
```

## Keyboard Navigation

- `F1` Vault
- `F2` Skill Factory
- `F3` Project Provisioner
- `F4` Blueprint Generator
- `F5` Forge Radar
- `F6` Session Replay
- `F7` MCP Builder
- `` ` `` Command Palette
- `Ctrl+R` Refresh current module
- `Q` Quit

## Module Walkthrough

## 1) Vault (F1)

Purpose: API keys, profiles, directories, exports.

Common flow:

1. Create/switch profile.
2. Save provider keys.
3. Verify status tab is green.

## 2) Skill Factory (F2)

Tabs:

- `Registry`: inspect existing skills
- `Create Skill`: form-based generation
- `Composer`: live preview + quality score
- `Marketplace`: install from marketplace index
- `Cookbook`: curated skill examples
- `Forge Sync`: git-based team sharing

### Skill scopes

- Global: shared across projects
- Local: only current project (`.opencode/skills`)

## 3) Project Provisioner (F3)

Flow:

1. Scan project path.
2. Select skill injections.
3. Preview Ghost Diff.
4. Execute bootstrap.

Feature 12 support:

- Side-by-side diff for `AGENTS.md` and `opencode.json` before execution.
- Context Architect write requires explicit confirmation from diff view.

## 4) Blueprint Generator (F4)

Generate planning blueprints from templates or Studio interview mode.

## 5) Forge Radar (F5)

Scan project health:

- AGENTS.md presence
- `opencode.json` presence
- `.opencode/` presence
- git cleanliness
- skill count and warnings

## 6) Session Replay (F6)

Replay parsed sessions from local logs.

Usage tips:

- Search field filters as you type.
- Agent selector updates list live.
- Open session to inspect timeline events.

## 7) MCP Builder (F7)

Describe a capability in plain language, detect tools, and scaffold a TypeScript MCP server into project local folder.

## Command Palette

Open with `` ` ``.

Includes:

- Module navigation
- Skill Factory deep links
- Radar/Sessions refresh actions
- Theme quick apply actions

## Team Sync (Forge Sync)

Configure in Skill Factory → Forge Sync tab.

- Save repo URL + branch.
- Pull to import remote skills.
- Push to publish local global skills.

Expected repo layout:

```text
skills/<skill-name>/SKILL.md
```

## Best Practices

- Keep `AGENTS.md` current after major architecture changes.
- Use cookbook entries as starting points, not final skills.
- Run tests before pushing sync updates.
- Prefer narrow, single-purpose skills over oversized prompts.
