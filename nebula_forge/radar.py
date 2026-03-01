"""
NEBULA-FORGE — Forge Radar
Lightweight project health checks for v2 foundation.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import ProjectHealth, RadarWarning
from .vault import Vault


class HealthChecker:
    """Compute a project health snapshot with actionable warnings."""

    def __init__(self, vault: Vault) -> None:
        self.vault = vault

    def scan(self, project_path: Path) -> ProjectHealth:
        path = project_path.expanduser().resolve()

        agents_md = path / "AGENTS.md"
        opencode_json = path / "opencode.json"
        opencode_dir = path / ".opencode"

        health = ProjectHealth(
            project_path=str(path),
            has_agents_md=agents_md.exists(),
            has_opencode_json=opencode_json.exists(),
            has_opencode_dir=opencode_dir.exists(),
            active_skills=self._list_active_skills(path),
            git_status=self._git_status(path),
        )

        if not health.has_agents_md:
            health.warnings.append(
                RadarWarning(
                    level="error",
                    code="AGENTS_MD_MISSING",
                    message="AGENTS.md is missing — agent context is incomplete.",
                    action_label="Bootstrap project",
                )
            )

        if not health.has_opencode_json:
            health.warnings.append(
                RadarWarning(
                    level="warning",
                    code="OPENCODE_JSON_MISSING",
                    message="opencode.json is missing — MCP/plugins cannot be configured.",
                    action_label="Run Provisioner",
                )
            )

        if not health.has_opencode_dir:
            health.warnings.append(
                RadarWarning(
                    level="warning",
                    code="OPENCODE_DIR_MISSING",
                    message=".opencode/ directory not found.",
                    action_label="Run Provisioner",
                )
            )

        if health.git_status == "dirty":
            health.warnings.append(
                RadarWarning(
                    level="info",
                    code="GIT_DIRTY",
                    message="Git workspace has uncommitted changes.",
                    action_label="Review changes",
                )
            )

        keys = self.vault.load().api_keys.masked()
        missing_keys = [k for k, v in keys.items() if isinstance(v, str) and "NOT SET" in v]
        if missing_keys:
            health.warnings.append(
                RadarWarning(
                    level="info",
                    code="KEYS_INCOMPLETE",
                    message=f"{len(missing_keys)} API key(s) are not set in Vault.",
                    action_label="Open Vault",
                )
            )

        return health

    def _list_active_skills(self, project_path: Path) -> list[str]:
        skills_dir = self.vault.project_skills_dir(project_path)
        if not skills_dir.exists():
            return []
        return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())

    def _git_status(self, project_path: Path) -> str:
        if not (project_path / ".git").exists():
            return "no_git"

        try:
            proc = subprocess.run(
                ["git", "-C", str(project_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                return "no_git"
            return "dirty" if proc.stdout.strip() else "clean"
        except Exception:
            return "no_git"


def load_opencode_config(project_path: Path) -> dict:
    """Best-effort loader for project opencode.json."""
    config_path = project_path / "opencode.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
