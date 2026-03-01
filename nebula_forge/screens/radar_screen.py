"""
NEBULA-FORGE — Forge Radar Screen
Live-ish project health dashboard (v2 foundation).
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Input, Static

from ..models import ProjectHealth
from ..radar import HealthChecker
from ..vault import Vault


class RadarScreen(Container):
    """Forge Radar — project health and quick diagnostics."""

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self.vault = vault
        self.checker = HealthChecker(vault)
        self._health: ProjectHealth | None = None

    def compose(self) -> ComposeResult:
        cwd = Path.cwd()
        yield Static("  ◎  FORGE RADAR", classes="section-title")
        yield ScrollableContainer(
            Static("[bold #7dcfff]Live Project Intelligence[/]"),
            Static("[#565f89]Scan your current project for context/configuration gaps.[/]\n"),
            Static("[#bb9af7]Project Path[/]"),
            Input(value=str(cwd), id="radar-project-path"),
            Horizontal(
                Button("⟳ Scan", id="btn-radar-scan", classes="btn-primary"),
                Button("📁 Use CWD", id="btn-radar-cwd", classes="btn-ghost"),
            ),
            Container(id="radar-summary"),
            Container(id="radar-warnings"),
            classes="panel",
        )

    def on_mount(self) -> None:
        self.refresh_current_project()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-radar-cwd":
            cwd = Path.cwd()
            self.query_one("#radar-project-path", Input).value = str(cwd)
            self.scan_path(cwd)
        elif bid == "btn-radar-scan":
            text = self.query_one("#radar-project-path", Input).value.strip()
            if not text:
                self.app.notify("Provide a project path", severity="warning")
                return
            self.scan_path(Path(text).expanduser())

    def refresh_current_project(self) -> None:
        """Public refresh hook for app-level actions and command palette."""
        self.scan_path(Path.cwd())

    def scan_path(self, project_path: Path) -> None:
        """Public scan API for a target project path."""
        self._scan(project_path)

    def _scan(self, project_path: Path) -> None:
        if not project_path.exists() or not project_path.is_dir():
            self.app.notify(f"Invalid path: {project_path}", severity="error")
            return

        self._health = self.checker.scan(project_path)
        self._render_health()

    def _render_health(self) -> None:
        summary = self.query_one("#radar-summary", Container)
        warnings = self.query_one("#radar-warnings", Container)
        summary.remove_children()
        warnings.remove_children()

        if not self._health:
            return

        git_color = {
            "clean": "#9ece6a",
            "dirty": "#e0af68",
            "no_git": "#565f89",
        }.get(self._health.git_status, "#565f89")

        summary.mount(Static("\n[bold #7dcfff]Snapshot[/]"))
        summary.mount(Static(f"[#565f89]Path:[/] [#c0caf5]{self._health.project_path}[/]"))
        summary.mount(Static(f"[#565f89]Git:[/] [{git_color}]{self._health.git_status}[/]"))
        summary.mount(Static(f"[#565f89]AGENTS.md:[/] {'[#9ece6a]yes[/]' if self._health.has_agents_md else '[#f7768e]no[/]'}"))
        summary.mount(Static(f"[#565f89]opencode.json:[/] {'[#9ece6a]yes[/]' if self._health.has_opencode_json else '[#f7768e]no[/]'}"))
        summary.mount(Static(f"[#565f89].opencode/:[/] {'[#9ece6a]yes[/]' if self._health.has_opencode_dir else '[#f7768e]no[/]'}"))
        summary.mount(Static(f"[#565f89]Active skills:[/] [#7aa2f7]{len(self._health.active_skills)}[/]"))

        warnings.mount(Static("\n[bold #7dcfff]Warnings & Actions[/]"))
        if not self._health.warnings:
            warnings.mount(Static("[#9ece6a]✓ No warnings found[/]"))
            return

        for item in self._health.warnings:
            color = {
                "error": "#f7768e",
                "warning": "#e0af68",
                "info": "#7dcfff",
            }.get(item.level, "#7dcfff")
            suffix = f"  [#565f89]→ {item.action_label}[/]" if item.action_label else ""
            warnings.mount(Static(f"[{color}]●[/] [#c0caf5]{item.message}[/]{suffix}"))
