"""
NEBULA-FORGE — Forge Sync (Foundation)
Git-based team skill registry synchronization.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .vault import Vault


@dataclass
class SyncStatus:
    configured: bool
    repo_url: str
    branch: str
    auto: bool
    connected: bool
    local_skills: int
    remote_skills: int
    last_pull: str
    last_push: str
    message: str


class ForgeSync:
    """Synchronize local global skills with a shared git repository."""

    def __init__(self, vault: Vault) -> None:
        self.vault = vault
        self.repo_dir = self.vault.vault_dir / "sync-registry"

    def status(self) -> SyncStatus:
        cfg = self.vault.load()
        repo_url = cfg.sync_repo_url or ""
        connected = self.repo_dir.exists() and (self.repo_dir / ".git").exists()

        local_skills = len(self.vault.list_global_skills())
        remote_skills = len(self._list_remote_skill_dirs()) if connected else 0

        return SyncStatus(
            configured=bool(repo_url),
            repo_url=repo_url,
            branch=cfg.sync_branch,
            auto=cfg.sync_auto,
            connected=connected,
            local_skills=local_skills,
            remote_skills=remote_skills,
            last_pull=cfg.sync_last_pull or "never",
            last_push=cfg.sync_last_push or "never",
            message="ready" if repo_url else "not configured",
        )

    def configure(self, repo_url: str, branch: str = "main", auto: bool = False) -> tuple[bool, str]:
        repo = repo_url.strip()
        if not repo:
            return False, "Repository URL is required"

        cfg = self.vault.load()
        cfg.sync_repo_url = repo
        cfg.sync_branch = branch.strip() or "main"
        cfg.sync_auto = bool(auto)
        self.vault.save(cfg)
        return True, "Sync configuration saved"

    def pull(self) -> tuple[bool, str]:
        cfg = self.vault.load()
        repo_url = (cfg.sync_repo_url or "").strip()
        branch = cfg.sync_branch or "main"
        if not repo_url:
            return False, "Sync repository is not configured"

        ok, msg = self._ensure_repo(repo_url, branch)
        if not ok:
            return False, msg

        ok, msg = self._git(["fetch", "origin", branch])
        if not ok:
            return False, msg

        ok, msg = self._git(["checkout", branch])
        if not ok:
            return False, msg

        ok, msg = self._git(["pull", "origin", branch])
        if not ok:
            return False, msg

        copied = self._copy_remote_to_local()
        cfg.sync_last_pull = datetime.now().isoformat(timespec="seconds")
        self.vault.save(cfg)
        return True, f"Pulled and applied {copied} skill(s)"

    def push(self) -> tuple[bool, str]:
        cfg = self.vault.load()
        repo_url = (cfg.sync_repo_url or "").strip()
        branch = cfg.sync_branch or "main"
        if not repo_url:
            return False, "Sync repository is not configured"

        ok, msg = self._ensure_repo(repo_url, branch)
        if not ok:
            return False, msg

        exported = self._copy_local_to_remote()

        ok, _ = self._git(["add", "."])
        if not ok:
            return False, "Unable to stage sync changes"

        commit_msg = f"sync(skills): export {exported} local skill(s)"
        self._git(["commit", "-m", commit_msg])  # no-op if nothing changed

        ok, msg = self._git(["push", "origin", branch])
        if not ok:
            return False, msg

        cfg.sync_last_push = datetime.now().isoformat(timespec="seconds")
        self.vault.save(cfg)
        return True, f"Pushed {exported} skill(s)"

    # ── Internal helpers ─────────────────────────────────────────

    def _ensure_repo(self, repo_url: str, branch: str) -> tuple[bool, str]:
        self.vault.ensure_dirs()
        if not self.repo_dir.exists():
            ok, msg = self._run(["git", "clone", "--depth=1", "--branch", branch, repo_url, str(self.repo_dir)])
            if not ok:
                return False, f"Clone failed: {msg}"
            return True, "cloned"

        if not (self.repo_dir / ".git").exists():
            return False, f"Sync dir exists but is not a git repo: {self.repo_dir}"

        return True, "ok"

    def _git(self, args: list[str]) -> tuple[bool, str]:
        return self._run(["git", *args], cwd=self.repo_dir)

    def _run(self, command: list[str], cwd: Path | None = None) -> tuple[bool, str]:
        try:
            proc = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return True, proc.stdout.strip() or "ok"
            return False, (proc.stderr or proc.stdout or "command failed").strip()
        except Exception as e:
            return False, str(e)

    def _skills_root_remote(self) -> Path:
        return self.repo_dir / "skills"

    def _list_remote_skill_dirs(self) -> list[Path]:
        root = self._skills_root_remote()
        if not root.exists():
            return []
        return [p for p in root.iterdir() if p.is_dir()]

    def _copy_remote_to_local(self) -> int:
        src_root = self._skills_root_remote()
        if not src_root.exists():
            return 0

        count = 0
        for src in self._list_remote_skill_dirs():
            skill_name = src.name
            src_skill_md = src / "SKILL.md"
            if not src_skill_md.exists():
                continue
            dst = self.vault.skills_dir / skill_name
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_skill_md, dst / "SKILL.md")
            count += 1
        return count

    def _copy_local_to_remote(self) -> int:
        dst_root = self._skills_root_remote()
        dst_root.mkdir(parents=True, exist_ok=True)

        count = 0
        for src in self.vault.list_global_skills():
            src_skill_md = src / "SKILL.md"
            if not src_skill_md.exists():
                continue
            dst = dst_root / src.name
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_skill_md, dst / "SKILL.md")
            count += 1
        return count
