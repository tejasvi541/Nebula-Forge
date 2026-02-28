"""
NEBULA-FORGE — Main Application
The Agentic Orchestrator TUI.
"""

from __future__ import annotations
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import (
    Button, Footer, Header, Label, Static, TabbedContent, TabPane
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


NAV_ITEMS = [
    ("vault",    "◈  The Vault",       "Keys & Config"),
    ("skills",   "⊕  Skill Factory",   "Global Skills"),
    ("project",  "⬡  Provisioner",     "Project Setup"),
    ("blueprint","◉  Blueprints",      "Agent Scratchpad"),
]


class NebulaApp(App):
    """NEBULA-FORGE — The Agentic Orchestrator."""

    CSS_PATH = "themes/tokyo_night.tcss"
    TITLE = "NEBULA-FORGE"
    SUB_TITLE = "Agentic Orchestrator v1.0"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
        ("f1", "nav_vault", "Vault"),
        ("f2", "nav_skills", "Skills"),
        ("f3", "nav_project", "Project"),
        ("f4", "nav_blueprint", "Blueprints"),
        ("f5", "refresh_view", "Refresh"),
        ("?", "show_help", "Help"),
    ]

    active_section: reactive[str] = reactive("vault")

    def __init__(self):
        super().__init__()
        self.vault = Vault()
        self.provisioner = Provisioner(self.vault)

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
        elif section_id == "settings":
            content_area.mount(self._build_settings())

    def _build_settings(self) -> Container:
        cfg = self.vault.load()
        shortcuts = [
            ("F1", "The Vault"),
            ("F2", "Skill Factory"),
            ("F3", "Project Provisioner"),
            ("F4", "Blueprint Generator"),
            ("F5", "Refresh current view"),
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
            Static("[bold #7dcfff]Keyboard Shortcuts[/]\n"),
            *[Static(f"  [bold #7aa2f7]{key:6}[/]  [#c0caf5]{action}[/]") for key, action in shortcuts],
            classes="panel",
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

    def action_refresh_view(self) -> None:
        self._load_section(self.active_section)
        self.notify("✓ Refreshed", severity="information")

    def action_show_help(self) -> None:
        self._load_section("settings")

    def action_save(self) -> None:
        self.notify("Vault auto-saves on every change", severity="information")

    def action_quit(self) -> None:
        self.exit()
