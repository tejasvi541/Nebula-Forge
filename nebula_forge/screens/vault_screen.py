"""
NEBULA-FORGE — Vault Screen
Config management, key status, environment export.
"""

from __future__ import annotations
import uuid
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import (
    Button, Input, Static, TabbedContent, TabPane, Select,
)
from textual.containers import (
    Horizontal, Container, ScrollableContainer,
)
from ..vault import Vault
from ..models import APIKeys

MODELS = [
    "copilot/claude-opus-4-6",
    "copilot/gpt-5.1-codex-max",
    "copilot/gemini-3.1-pro-preview",
    "nvidia/devstral-2-123b-instruct-2512",
    "opencodezen/minimax-m2-5",
    "copilot/claude-sonnet-4-5",
    "copilot/gpt-5",
]


class VaultScreen(Container):
    """The Vault — configuration and key management."""

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self.vault = vault

    def compose(self) -> ComposeResult:
        yield Static("  ◈  THE VAULT  —  Configuration & Key Management", classes="section-title")
        with TabbedContent(id="vault-tabs"):
            with TabPane("  Status  ", id="tab-status"):
                yield self._build_status_tab()
            with TabPane("  API Keys  ", id="tab-keys"):
                yield self._build_keys_tab()
            with TabPane("  Paths  ", id="tab-paths"):
                yield self._build_paths_tab()
            with TabPane("  Export  ", id="tab-export"):
                yield self._build_export_tab()

    def _build_status_tab(self) -> Container:
        cfg = self.vault.load()
        status = self.vault.status_summary()
        rows = "\n".join(
            f"[#bb9af7]{k:20}[/]  "
            + (f"[#9ece6a]{v}[/]" if "✓" in v or v not in ("✗ missing", "no") else f"[#f7768e]{v}[/]")
            for k, v in status.items()
        )
        return Container(
            Static(
                f"[bold #7dcfff]Vault Location[/]\n"
                f"[#565f89]{self.vault.vault_dir}[/]\n\n"
                f"[bold #7dcfff]Configuration Status[/]\n{rows}"
            ),
            classes="panel",
        )

    def _build_keys_tab(self) -> ScrollableContainer:
        cfg = self.vault.load()
        keys = self.vault.get_active_api_keys()
        profiles = self.vault.list_profiles()
        profile_options = [(p, p) for p in profiles] if profiles else [("default", "default")]

        fixed_fields = [
            ("github_copilot", "GitHub Copilot Token", keys.github_copilot or ""),
            ("google_ai", "Google AI API Key", keys.google_ai or ""),
            ("anthropic", "Anthropic API Key", keys.anthropic or ""),
            ("nvidia", "NVIDIA NIM API Key", keys.nvidia or ""),
        ]
        children: list = [
            Static("[bold #7dcfff]Vault Profiles[/]"),
            Static(f"[#565f89]Active profile:[/] [#9ece6a]{cfg.active_profile}[/]"),
            Horizontal(
                Select(options=profile_options, value=cfg.active_profile, id="profile-switch-select"),
                Button("Switch", id="btn-switch-profile", classes="btn-ghost"),
            ),
            Horizontal(
                Input(placeholder="new-profile-name", id="profile-new-name"),
                Button("Create", id="btn-create-profile", classes="btn-primary"),
            ),
            Static(""),
            Static("[bold #7dcfff]Fixed API Keys[/]\n"),
        ]
        for fid, label, val in fixed_fields:
            children.append(Static(f"[#bb9af7]{label}[/]"))
            children.append(Input(value=val, password=True, id=f"key-{fid}", placeholder="not set"))

        children.append(Static("\n[bold #7dcfff]Custom API Keys[/]"))
        children.append(Static("[#565f89]Add any extra keys you need (stored by name).[/]\n"))

        custom_rows = [
            self._make_custom_key_row(name, val)
            for name, val in keys.custom_endpoints.items()
        ]
        children.append(Container(*custom_rows, id="custom-keys-container"))
        children.append(Horizontal(
            Button("＋  Add Key", id="btn-add-custom-key", classes="btn-ghost"),
            Button("💾  Save Keys", id="btn-save-keys", classes="btn-primary"),
        ))
        children.append(Static(
            "[#565f89]\nKeys are stored locally in ~/.nebula-forge/vault.json\n"
            "File permissions are set to 600 (owner read-only).[/]"
        ))
        return ScrollableContainer(*children, id="keys-panel", classes="panel")

    def _make_custom_key_row(self, name: str = "", val: str = "") -> Horizontal:
        row_id = uuid.uuid4().hex[:8]
        return Horizontal(
            Input(value=name, placeholder="KEY_NAME", classes="custom-key-name"),
            Input(value=val, password=True, placeholder="value", classes="custom-key-val"),
            Button("✕", id=f"remove-custom-{row_id}", classes="btn-danger"),
            id=f"custom-row-{row_id}",
            classes="custom-key-row",
        )

    def _build_paths_tab(self) -> ScrollableContainer:
        cfg = self.vault.load()
        return ScrollableContainer(
            Static("[bold #7dcfff]Global Directories[/]"),
            Static("[#565f89]Where NEBULA-FORGE stores skills, agents, logs, and blueprints globally.[/]\n"),
            Static("[#bb9af7]Skills Directory[/]"),
            Input(value=str(self.vault.skills_dir), id="dir-skills"),
            Static("[#bb9af7]Agents Directory[/]"),
            Input(value=str(self.vault.agents_dir), id="dir-agents"),
            Static("[#bb9af7]Logs Directory[/]"),
            Input(value=str(self.vault.logs_dir), id="dir-logs"),
            Static("[#bb9af7]Blueprints Directory[/]"),
            Input(value=str(self.vault.blueprints_dir), id="dir-blueprints"),
            Static("[#565f89]\nNote: If the old directory is empty it will be removed on save.[/]"),
            Static("\n[bold #7dcfff]Per-Project Subdirectories[/]"),
            Static(
                "[#565f89]Relative paths created inside each project root when provisioning.\n"
                "OpenCode discovers skills from [#9ece6a].opencode/skills/[/][#565f89], "
                "[#9ece6a].claude/skills/[/][#565f89], or [#9ece6a].agents/skills/[/][#565f89].[/]\n"
            ),
            Static("[#bb9af7]Project Skills Subdir[/]"),
            Input(value=cfg.project_skills_subdir, id="dir-project-skills",
                  placeholder=".opencode/skills"),
            Static("[#bb9af7]Project Agents Subdir[/]"),
            Input(value=cfg.project_agents_subdir, id="dir-project-agents",
                  placeholder=".opencode/agents"),
            Static("[#565f89]\nVault location (fixed):[/]"),
            Static(f"[#565f89]{self.vault.vault_dir}[/]"),
            Static(f"\n[#7aa2f7]{len(self.vault.list_global_skills())}[/] skills in global registry\n"),
            Horizontal(
                Button("💾  Save Directories", id="btn-save-dirs", classes="btn-primary"),
                Button("🔧  Re-initialize", id="btn-reinit-dirs", classes="btn-ghost"),
            ),
            classes="panel",
        )

    def _build_export_tab(self) -> Container:
        exports = self.vault.get_env_exports()
        if exports:
            display = "\n".join(
                f"export {line.split('=')[0]}=[bold #9ece6a]****[/]"
                if "=" in line else line
                for line in exports.split("\n")
            )
        else:
            display = "[#f7768e]No API keys configured.[/]"

        return Container(
            Static("[bold #7dcfff]Shell Export Preview[/]\n[#565f89](values masked for security)[/]\n"),
            Static(display, classes="panel"),
            Button("📋  Copy Exports to Clipboard", id="btn-copy-exports", classes="btn-ghost"),
            Button("📄  Save to ~/.nebula-forge/exports.sh", id="btn-save-exports", classes="btn-ghost"),
            classes="panel",
        )

    # ── Events ────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-save-keys":
            self._save_keys()
        elif bid == "btn-create-profile":
            self._create_profile()
        elif bid == "btn-switch-profile":
            self._switch_profile()
        elif bid == "btn-add-custom-key":
            self._add_custom_key_row()
        elif bid.startswith("remove-custom-"):
            self._remove_custom_key_row(bid[len("remove-custom-"):])
        elif bid == "btn-save-dirs":
            self._save_dirs()
        elif bid == "btn-reinit-dirs":
            self.vault.ensure_dirs()
            self.app.notify("✓ Directories re-initialized", severity="information")
        elif bid == "btn-save-exports":
            self._save_exports()
        elif bid == "btn-copy-exports":
            self.app.notify("Use 'Save to file' — clipboard not available in TUI", severity="warning")

    def _save_keys(self) -> None:
        cfg = self.vault.load()
        current = self.vault.get_active_api_keys().model_dump()
        for fid in ("github_copilot", "google_ai", "anthropic", "nvidia"):
            try:
                val = self.query_one(f"#key-{fid}", Input).value.strip()
                current[fid] = val or None
            except Exception:
                pass
        # Collect dynamic custom keys
        custom: dict[str, str] = {}
        try:
            for row in self.query_one("#custom-keys-container").query(".custom-key-row"):
                try:
                    name = row.query_one(".custom-key-name", Input).value.strip()
                    val = row.query_one(".custom-key-val", Input).value.strip()
                    if name:
                        custom[name] = val
                except Exception:
                    pass
        except Exception:
            pass
        current["custom_endpoints"] = custom
        cfg.key_profiles[cfg.active_profile] = APIKeys(**current)
        cfg.api_keys = cfg.key_profiles[cfg.active_profile]
        self.vault.save(cfg)
        self.app.notify("✓ API keys saved to vault", severity="information")

    def _create_profile(self) -> None:
        try:
            name = self.query_one("#profile-new-name", Input).value.strip()
        except Exception:
            name = ""
        if not name:
            self.app.notify("Profile name is required", severity="warning")
            return
        ok = self.vault.create_profile(name)
        if ok:
            self.app.notify(f"✓ Profile '{name}' created and activated", severity="information")
        else:
            self.app.notify(f"Could not create profile '{name}'", severity="error")

    def _switch_profile(self) -> None:
        try:
            sel = self.query_one("#profile-switch-select", Select)
            name = str(sel.value) if sel.value != Select.BLANK else ""
        except Exception:
            name = ""
        if not name:
            self.app.notify("Select a profile first", severity="warning")
            return
        ok = self.vault.switch_profile(name)
        if ok:
            self.app.notify(f"✓ Switched to profile '{name}'", severity="information")
        else:
            self.app.notify(f"Could not switch to profile '{name}'", severity="error")

    def _add_custom_key_row(self) -> None:
        try:
            self.query_one("#custom-keys-container").mount(self._make_custom_key_row())
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")

    def _remove_custom_key_row(self, row_id: str) -> None:
        try:
            self.query_one(f"#custom-row-{row_id}").remove()
        except Exception:
            pass

    def _save_dirs(self) -> None:
        try:
            skills     = self.query_one("#dir-skills", Input).value.strip()
            agents     = self.query_one("#dir-agents", Input).value.strip()
            logs       = self.query_one("#dir-logs", Input).value.strip()
            blueprints = self.query_one("#dir-blueprints", Input).value.strip()
            self.vault.update_dirs(
                skills_dir=skills or None,
                agents_dir=agents or None,
                logs_dir=logs or None,
                blueprints_dir=blueprints or None,
            )
            proj_skills    = self.query_one("#dir-project-skills", Input).value.strip()
            proj_agents    = self.query_one("#dir-project-agents", Input).value.strip()
            self.vault.update_project_dirs(
                skills_subdir=proj_skills or None,
                agents_subdir=proj_agents or None,
            )
            self.app.notify("✓ Directories updated", severity="information")
        except Exception as e:
            self.app.notify(f"Error saving directories: {e}", severity="error")

    def _save_exports(self) -> None:
        exports = self.vault.get_env_exports()
        out = self.vault.vault_dir / "exports.sh"
        out.write_text(f"#!/bin/bash\n# Generated by NEBULA-FORGE\n{exports}\n")
        out.chmod(0o600)
        self.app.notify(f"✓ Saved to {out}", severity="information")
