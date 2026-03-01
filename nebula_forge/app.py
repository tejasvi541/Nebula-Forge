"""
NEBULA-FORGE — Main Application
The Agentic Orchestrator TUI.
"""

from __future__ import annotations
import os
from collections.abc import Iterable
from pathlib import Path

from textual.app import App, ComposeResult
from textual.app import SystemCommand
from textual.widgets import (
    Button, Footer, Header, Label, Static, TabbedContent, TabPane, Select
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import work
from rich.text import Text

from .vault import Vault
from .provisioner import Provisioner
from .screens.splash import SplashScreen
from .screens.wizard import WizardScreen
from .screens.vault_screen import VaultScreen
from .screens.skill_factory import SkillFactoryScreen
from .screens.project_screen import ProjectScreen
from .screens.blueprint import BlueprintScreen
from .screens.radar_screen import RadarScreen
from .screens.session_replay import SessionReplayScreen
from .screens.mcp_builder import MCPBuilderScreen
from .theme_engine import ThemeEngine


NAV_ITEMS = [
    ("vault",    "◈  The Vault",       "Keys & Config"),
    ("skills",   "⊕  Skill Factory",   "Global Skills"),
    ("project",  "⬡  Provisioner",     "Project Setup"),
    ("blueprint","◉  Blueprints",      "Agent Scratchpad"),
    ("radar",    "◎  Forge Radar",     "Project Intelligence"),
    ("sessions", "◉  Session Replay",  "Agent Activity Log"),
    ("mcp",      "⬡  MCP Builder",     "Custom MCP Servers"),
]


class NebulaApp(App):
    """NEBULA-FORGE — The Agentic Orchestrator."""

    CSS_PATH = ["themes/tokyo_night.tcss", "themes/overrides/tokyo_night.tcss"]
    TITLE = "NEBULA-FORGE"
    SUB_TITLE = "Agentic Orchestrator v1.0"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("f1", "nav_vault", "Vault"),
        ("f2", "nav_skills", "Skills"),
        ("f3", "nav_project", "Project"),
        ("f4", "nav_blueprint", "Blueprints"),
        ("f5", "nav_radar", "Radar"),
        ("f6", "nav_sessions", "Sessions"),
        ("f7", "nav_mcp", "MCP Builder"),
        ("ctrl+r", "refresh_view", "Refresh"),
        ("`", "command_palette", "Palette"),
        ("?", "show_help", "Help"),
    ]

    active_section: reactive[str] = reactive("vault")

    def __init__(self):
        super().__init__()
        self.vault = Vault()
        self.provisioner = Provisioner(self.vault)
        self.theme_engine = ThemeEngine()

        # Initialize CSS paths based on stored theme preference.
        cfg = self.vault.load()
        self.css_path = self.theme_engine.css_paths_for(cfg.theme)

    # ── Compose ──────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="app-grid"):
            # ── Sidebar
            with Vertical(id="sidebar"):
                yield Static(
                    "  ◆ NEBULA-FORGE ◆",
                    id="sidebar-logo",
                )
                yield Static(
                    "  THE AGENTIC\n  ORCHESTRATOR",
                    id="sidebar-title",
                )
                yield Static("")
                yield Static("  MODULES", classes="nav-section-label")

                for section_id, label, desc in NAV_ITEMS:
                    yield Button(
                        f"  {label}",
                        id=f"nav-{section_id}",
                        classes="nav-item",
                    )

                yield Static("  SYSTEM", classes="nav-section-label")
                yield Button("  ⚙  Settings", id="nav-settings", classes="nav-item")
                yield Button("  ◌  Re-run Wizard", id="nav-wizard", classes="nav-item")

                yield Static(
                    self._build_status_line(),
                    id="sidebar-status",
                )

            # ── Main content
            with Vertical(id="main-content"):
                with Horizontal(id="top-bar"):
                    yield Static("", id="top-bar-title")
                    yield Static("", id="breadcrumb")

                yield Container(id="content-area")

        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────

    def on_mount(self) -> None:
        self.push_screen(SplashScreen())
        self._update_nav()
        self._load_section("vault")

    def on_screen_resume(self) -> None:
        """Called when returning from a pushed screen (splash/wizard)."""
        if not self.vault.is_initialized():
            self.call_later(self._launch_wizard)

    def _launch_wizard(self) -> None:
        self.push_screen(WizardScreen(self.vault, on_complete=self._on_wizard_done))

    def _on_wizard_done(self) -> None:
        self.query_one("#sidebar-status", Static).update(self._build_status_line())
        self.app.notify("✓ NEBULA-FORGE initialized!", severity="information")

    def _build_status_line(self) -> str:
        cfg = self.vault.load()
        model = cfg.default_model.split("/")[-1][:14]
        init = "[#9ece6a]●[/]" if cfg.initialized else "[#f7768e]●[/]"
        return f"  {init} [#565f89]{model}[/]"

    # ── Navigation ────────────────────────────────────────────

    def _update_nav(self) -> None:
        for section_id, _, _ in NAV_ITEMS:
            try:
                btn = self.query_one(f"#nav-{section_id}", Button)
                if section_id == self.active_section:
                    btn.add_class("active")
                else:
                    btn.remove_class("active")
            except Exception:
                pass

    def _load_section(self, section_id: str) -> None:
        self.active_section = section_id
        self._update_nav()

        titles = {
            "vault": ("◈  THE VAULT", "Keys · Config · Environment"),
            "skills": ("⊕  SKILL FACTORY", "Global Skill Registry"),
            "project": ("⬡  PROJECT PROVISIONER", "One-Click Agent Bootstrap"),
            "blueprint": ("◉  BLUEPRINT GENERATOR", "Agent Scratchpad · Dynamic Markdown"),
            "radar": ("◎  FORGE RADAR", "Live Project Intelligence"),
            "sessions": ("◉  SESSION REPLAY", "Agent Activity Log"),
            "mcp": ("⬡  MCP PLUGIN BUILDER", "Generate Custom MCP Servers"),
            "settings": ("⚙  SETTINGS", "Application Settings"),
        }
        title, crumb = titles.get(section_id, ("NEBULA-FORGE", ""))

        try:
            self.query_one("#top-bar-title", Static).update(f"[bold #7dcfff]{title}[/]")
            self.query_one("#breadcrumb", Static).update(f"[#565f89]  ›  {crumb}[/]")
        except Exception:
            pass

        content_area = self.query_one("#content-area")
        content_area.remove_children()

        if section_id == "vault":
            content_area.mount(VaultScreen(self.vault))
        elif section_id == "skills":
            content_area.mount(SkillFactoryScreen(self.vault, self.provisioner))
        elif section_id == "project":
            content_area.mount(ProjectScreen(self.vault, self.provisioner))
        elif section_id == "blueprint":
            content_area.mount(BlueprintScreen(self.vault, self.provisioner))
        elif section_id == "radar":
            content_area.mount(RadarScreen(self.vault))
        elif section_id == "sessions":
            content_area.mount(SessionReplayScreen())
        elif section_id == "mcp":
            content_area.mount(MCPBuilderScreen())
        elif section_id == "settings":
            content_area.mount(self._build_settings())

    def _build_settings(self) -> Container:
        cfg = self.vault.load()
        theme_options = [(t.label, t.key) for t in self.theme_engine.list_themes()]
        shortcuts = [
            ("F1", "The Vault"),
            ("F2", "Skill Factory"),
            ("F3", "Project Provisioner"),
            ("F4", "Blueprint Generator"),
            ("F5", "Forge Radar"),
            ("F6", "Session Replay"),
            ("F7", "MCP Builder"),
            ("Ctrl+R", "Refresh current view"),
            ("`", "Command palette"),
            ("Q", "Quit"),
            ("?", "Show this help"),
        ]
        return ScrollableContainer(
            Static("[bold #7dcfff]Application Settings[/]\n"),
            Static(
                f"[#bb9af7]Vault Path:[/]  [#565f89]{self.vault.vault_dir}[/]\n"
                f"[#bb9af7]Skills Dir:[/]  [#565f89]{self.vault.skills_dir}[/]\n"
                f"[#bb9af7]Agents Dir:[/]  [#565f89]{self.vault.agents_dir}[/]\n"
                f"[#bb9af7]Default Model:[/]  [#7aa2f7]{cfg.default_model}[/]\n"
            ),
            Static("\n[bold #7dcfff]Theme Engine[/]"),
            Static(f"[#565f89]Current theme:[/] [#9ece6a]{cfg.theme}[/]"),
            Horizontal(
                Select(options=theme_options, value=cfg.theme, id="settings-theme-select"),
                Button("Apply Theme", id="btn-apply-theme", classes="btn-primary"),
            ),
            Static("[#565f89]Theme is applied immediately when possible and always persisted.[/]"),
            Static("[bold #7dcfff]Keyboard Shortcuts[/]\n"),
            *[Static(f"  [bold #7aa2f7]{key:6}[/]  [#c0caf5]{action}[/]") for key, action in shortcuts],
            classes="panel",
        )

    def get_system_commands(self, screen) -> Iterable[SystemCommand]:
        """Feature 11: quick command palette entries for power users."""
        yield from super().get_system_commands(screen)

        # Navigation
        yield SystemCommand("◈ Vault: Open", "Open Vault module", self.action_nav_vault)
        yield SystemCommand("⊕ Skill Factory: Open", "Open Skill Factory module", self.action_nav_skills)
        yield SystemCommand("⬡ Provisioner: Open", "Open Project Provisioner module", self.action_nav_project)
        yield SystemCommand("◉ Blueprint: Open", "Open Blueprint Generator module", self.action_nav_blueprint)
        yield SystemCommand("◎ Radar: Open", "Open Forge Radar module", self.action_nav_radar)
        yield SystemCommand("◉ Session Replay: Open", "Open Session Replay module", self.action_nav_sessions)
        yield SystemCommand("⬡ MCP Builder: Open", "Open MCP Builder module", self.action_nav_mcp)
        yield SystemCommand("⚙ Settings: Open", "Open application settings", lambda: self._load_section("settings"))

        # Focused actions
        yield SystemCommand("⊕ Skill Factory: Create New Skill", "Open Create Skill tab", self._cmd_open_skill_create)
        yield SystemCommand("⊕ Skill Factory: Marketplace", "Open Marketplace tab", self._cmd_open_skill_marketplace)
        yield SystemCommand("⊕ Skill Factory: Forge Sync", "Open Forge Sync tab", self._cmd_open_skill_sync)
        yield SystemCommand("◎ Radar: Refresh Project Scan", "Open Radar and refresh scan", self._cmd_refresh_radar)
        yield SystemCommand("◉ Session Replay: Refresh", "Open Session Replay and refresh logs", self._cmd_refresh_sessions)
        yield SystemCommand("⟳ Refresh Current View", "Reload active section", self.action_refresh_view)
        yield SystemCommand("◌ Re-run Wizard", "Open setup wizard", lambda: self.push_screen(WizardScreen(self.vault, on_complete=self._on_wizard_done)))

        # Theme quick actions
        for theme in self.theme_engine.list_themes():
            yield SystemCommand(
                f"⚙ Settings: Apply Theme → {theme.label}",
                f"Apply and persist {theme.key}",
                lambda key=theme.key: self._apply_theme_by_key(key),
                discover=False,
            )

    # ── Events ────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "nav-vault":
            self._load_section("vault")
        elif bid == "nav-skills":
            self._load_section("skills")
        elif bid == "nav-project":
            self._load_section("project")
        elif bid == "nav-blueprint":
            self._load_section("blueprint")
        elif bid == "nav-radar":
            self._load_section("radar")
        elif bid == "nav-sessions":
            self._load_section("sessions")
        elif bid == "nav-mcp":
            self._load_section("mcp")
        elif bid == "btn-apply-theme":
            self._apply_theme_from_settings()
        elif bid == "nav-settings":
            self._load_section("settings")
        elif bid == "nav-wizard":
            self.push_screen(WizardScreen(self.vault, on_complete=self._on_wizard_done))

    # ── Actions ───────────────────────────────────────────────

    def action_nav_vault(self) -> None:
        self._load_section("vault")

    def action_nav_skills(self) -> None:
        self._load_section("skills")

    def action_nav_project(self) -> None:
        self._load_section("project")

    def action_nav_blueprint(self) -> None:
        self._load_section("blueprint")

    def action_nav_radar(self) -> None:
        self._load_section("radar")

    def action_nav_sessions(self) -> None:
        self._load_section("sessions")

    def action_nav_mcp(self) -> None:
        self._load_section("mcp")

    def _open_skill_tab(self, tab_id: str) -> None:
        self._load_section("skills")
        try:
            skills = self.query_one("#content-area").query_one(SkillFactoryScreen)
            tabs = skills.query_one("#skill-tabs", TabbedContent)
            tabs.active = tab_id
        except Exception:
            pass

    def _cmd_open_skill_create(self) -> None:
        self._open_skill_tab("tab-create")

    def _cmd_open_skill_marketplace(self) -> None:
        self._open_skill_tab("tab-marketplace")

    def _cmd_open_skill_sync(self) -> None:
        self._open_skill_tab("tab-sync")

    def _cmd_refresh_radar(self) -> None:
        self._load_section("radar")
        try:
            radar = self.query_one("#content-area").query_one(RadarScreen)
            radar.refresh_current_project()
        except Exception:
            self.action_refresh_view()

    def _cmd_refresh_sessions(self) -> None:
        self._load_section("sessions")
        try:
            replay = self.query_one("#content-area").query_one(SessionReplayScreen)
            replay.refresh_sessions()
        except Exception:
            self.action_refresh_view()

    def _apply_theme_by_key(self, selected: str) -> None:
        cfg = self.vault.load()
        cfg.theme = selected
        self.vault.save(cfg)

        try:
            self.css_path = self.theme_engine.css_paths_for(selected)
            self.refresh_css()
            self.notify(f"✓ Theme applied: {selected}", severity="information")
        except Exception:
            self.notify(f"✓ Theme saved: {selected} (restart may be required)", severity="information")

    def _apply_theme_from_settings(self) -> None:
        try:
            select = self.query_one("#settings-theme-select", Select)
            selected = str(select.value) if select.value != Select.BLANK else "tokyo_night"
        except Exception:
            selected = "tokyo_night"
        self._apply_theme_by_key(selected)

    def action_refresh_view(self) -> None:
        self._load_section(self.active_section)
        self.notify("✓ Refreshed", severity="information")

    def action_show_help(self) -> None:
        self._load_section("settings")

    def action_save(self) -> None:
        self.notify("Vault auto-saves on every change", severity="information")

    def action_quit(self) -> None:
        self.exit()
