"""
NEBULA-FORGE — Session Replay Screen
Timeline browser for parsed agent sessions.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Input, Select, Static

from ..models import AgentSession
from ..session_parser import SessionReplayParser


class SessionReplayScreen(Container):
    """Browse, filter, and inspect past agent sessions."""

    def __init__(self) -> None:
        super().__init__()
        self.parser = SessionReplayParser()
        self._sessions: list[AgentSession] = []
        self._selected: AgentSession | None = None

    def compose(self) -> ComposeResult:
        yield Static("  ◉  SESSION REPLAY", classes="section-title")
        yield ScrollableContainer(
            Static("[bold #7dcfff]Agent Activity Log[/]"),
            Static("[#565f89]Replay parsed OpenCode/Claude sessions from local logs.[/]\n"),
            Horizontal(
                Input(placeholder="Search sessions...", id="session-query"),
                Select(
                    options=[
                        ("All", "all"),
                        ("OpenCode", "opencode"),
                        ("Claude Code", "claude-code"),
                    ],
                    value="all",
                    id="session-agent-filter",
                ),
                Button("Refresh", id="btn-session-refresh", classes="btn-primary"),
                Button("Search", id="btn-session-search", classes="btn-ghost"),
            ),
            Container(id="session-list"),
            Container(id="session-detail"),
            classes="panel",
        )

    def on_mount(self) -> None:
        self.refresh_sessions()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-session-refresh":
            self.refresh_sessions()
        elif bid == "btn-session-search":
            self._render_list()
        elif bid.startswith("session-open-"):
            sid = bid[len("session-open-"):]
            self._selected = next((s for s in self._sessions if s.id == sid), None)
            self._render_detail()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "session-query":
            self._render_list()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "session-agent-filter":
            self._render_list()

    def refresh_sessions(self) -> None:
        """Public refresh hook for app-level actions and command palette."""
        self._refresh_sessions()

    def _refresh_sessions(self) -> None:
        self._sessions = self.parser.load_sessions()
        self._selected = self._sessions[0] if self._sessions else None
        self._render_list()
        self._render_detail()

    def _render_list(self) -> None:
        host = self.query_one("#session-list", Container)
        host.remove_children()

        query = self.query_one("#session-query", Input).value.strip().lower()
        sel = self.query_one("#session-agent-filter", Select)
        agent_filter = str(sel.value) if sel.value != Select.BLANK else "all"

        filtered = []
        for s in self._sessions:
            if agent_filter != "all" and s.agent != agent_filter:
                continue
            hay = f"{s.id} {s.agent} {s.branch} {s.project_path}".lower()
            if query and query not in hay:
                continue
            filtered.append(s)

        host.mount(Static("\n[bold #7dcfff]Sessions[/]"))
        if not filtered:
            host.mount(Static("[#565f89]No sessions matched your filters.[/]"))
            return

        for s in filtered[:80]:
            dirty = "[#e0af68]⚠ dirty[/]" if s.git_dirty else "[#9ece6a]✓ clean[/]"
            host.mount(Container(
                Horizontal(
                    Static(f"[#c0caf5]{s.started_at or 'unknown'}[/]  [#bb9af7]{s.agent}[/]  [#565f89]{s.branch or '—'}[/]  {dirty}"),
                    Button("Open", id=f"session-open-{s.id}", classes="btn-ghost"),
                ),
                Static(f"[#3b4261]{s.project_path}[/]"),
                classes="plugin-card",
            ))

    def _render_detail(self) -> None:
        host = self.query_one("#session-detail", Container)
        host.remove_children()

        host.mount(Static("\n[bold #7dcfff]Session Timeline[/]"))
        if not self._selected:
            host.mount(Static("[#565f89]Select a session to inspect details.[/]"))
            return

        s = self._selected
        host.mount(Static(
            f"[#565f89]Agent:[/] [#c0caf5]{s.agent}[/]  "
            f"[#565f89]Branch:[/] [#c0caf5]{s.branch or '—'}[/]  "
            f"[#565f89]Events:[/] [#7aa2f7]{len(s.events)}[/]"
        ))

        type_icon = {
            "message": "📋",
            "read": "🔍",
            "edit": "✏️",
            "run": "🧪",
            "commit": "📝",
        }

        for ev in s.events[:120]:
            icon = type_icon.get(ev.type, "•")
            path = f"  [#3b4261]{ev.path}[/]" if ev.path else ""
            host.mount(Static(f"[#565f89]{ev.timestamp}[/]  {icon}  [#c0caf5]{ev.summary}[/]{path}"))
