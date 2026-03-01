"""
NEBULA-FORGE — Session Replay Parser
Loads agent session logs from common local paths.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import AgentSession, SessionEvent


class SessionReplayParser:
    """Parse OpenCode and Claude Code JSONL session logs."""

    def __init__(self) -> None:
        self.opencode_root = Path.home() / ".opencode" / "sessions"
        self.claude_root = Path.home() / ".claude" / "projects"

    def load_sessions(self, limit: int = 200) -> list[AgentSession]:
        sessions: list[AgentSession] = []
        sessions.extend(self._load_opencode(limit=limit))
        sessions.extend(self._load_claude(limit=limit))

        if not sessions:
            sessions = self._fallback_sessions()

        sessions.sort(key=lambda s: s.started_at or "", reverse=True)
        return sessions[:limit]

    def _load_opencode(self, limit: int = 200) -> list[AgentSession]:
        out: list[AgentSession] = []
        if not self.opencode_root.exists():
            return out

        files = sorted(self.opencode_root.glob("*.jsonl"), reverse=True)
        for fp in files[:limit]:
            sess = self._parse_jsonl_file(fp, agent="opencode")
            if sess:
                out.append(sess)
        return out

    def _load_claude(self, limit: int = 200) -> list[AgentSession]:
        out: list[AgentSession] = []
        if not self.claude_root.exists():
            return out

        files = sorted(self.claude_root.glob("**/*.jsonl"), reverse=True)
        for fp in files[:limit]:
            sess = self._parse_jsonl_file(fp, agent="claude-code")
            if sess:
                out.append(sess)
        return out

    def _parse_jsonl_file(self, file_path: Path, agent: str) -> AgentSession | None:
        events: list[SessionEvent] = []
        started_at = ""
        branch = ""
        project_path = str(file_path.parent)

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    ts = str(
                        data.get("timestamp")
                        or data.get("time")
                        or data.get("created_at")
                        or ""
                    )
                    if not started_at and ts:
                        started_at = ts

                    tool_name = str(data.get("tool") or data.get("type") or "message").lower()
                    path = (
                        data.get("path")
                        or data.get("file")
                        or data.get("file_path")
                        or None
                    )
                    summary = self._summarize_event(data, tool_name)

                    if not branch:
                        branch = str(data.get("branch") or "")

                    if "project_path" in data and data.get("project_path"):
                        project_path = str(data.get("project_path"))

                    events.append(
                        SessionEvent(
                            timestamp=ts,
                            type=self._normalize_type(tool_name),
                            path=str(path) if path else None,
                            summary=summary,
                            raw=data,
                        )
                    )
        except Exception:
            return None

        if not events:
            return None

        return AgentSession(
            id=file_path.stem,
            agent=agent,
            project_path=project_path,
            branch=branch,
            started_at=started_at,
            ended_at=events[-1].timestamp if events else None,
            events=events,
            git_dirty=False,
        )

    def _normalize_type(self, text: str) -> str:
        t = text.lower()
        if any(x in t for x in ["read", "open_file"]):
            return "read"
        if any(x in t for x in ["edit", "write", "apply"]):
            return "edit"
        if any(x in t for x in ["run", "shell", "command", "exec"]):
            return "run"
        if "commit" in t:
            return "commit"
        return "message"

    def _summarize_event(self, data: dict, tool_name: str) -> str:
        for key in ["summary", "message", "content", "text", "prompt", "command"]:
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                clean = " ".join(val.strip().split())
                return clean[:160]

        if data.get("file") or data.get("path"):
            p = data.get("file") or data.get("path")
            return f"{tool_name}: {p}"

        return tool_name or "event"

    def _fallback_sessions(self) -> list[AgentSession]:
        """Fallback sample when no log files exist yet."""
        return [
            AgentSession(
                id="sample-session",
                agent="opencode",
                project_path=str(Path.cwd()),
                branch="main",
                started_at="sample",
                ended_at="sample",
                events=[
                    SessionEvent(timestamp="14:32:05", type="message", summary="Task: sample session (no local logs found)", raw={}),
                    SessionEvent(timestamp="14:32:18", type="read", path="src/app.py", summary="Read file src/app.py", raw={}),
                    SessionEvent(timestamp="14:35:44", type="edit", path="src/app.py", summary="Edited app navigation", raw={}),
                    SessionEvent(timestamp="14:42:19", type="run", summary="Run tests", raw={}),
                ],
                git_dirty=False,
            )
        ]
