"""
NEBULA-FORGE — Skill Marketplace Service
Fetch, cache, search, and install marketplace skills.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .models import MarketplaceSkill
from .vault import Vault

REGISTRY_URL = "https://skills.nebula-forge.dev/index.json"

FALLBACK_SKILLS: list[dict] = [
    {
        "id": "code-reviewer",
        "name": "code-reviewer",
        "description": "Expert code review with security, performance, and style checks.",
        "author": "nebula-community",
        "category": "code-review",
        "tags": ["review", "security", "quality"],
        "stars": 4.9,
        "downloads": 1200,
        "verified": True,
        "compatible_agents": ["opencode", "claude-code", "gemini"],
        "repo_url": "https://github.com/nebula-forge/skills-code-reviewer.git",
        "version": "1.0.0",
    },
    {
        "id": "db-migrator",
        "name": "db-migrator",
        "description": "Generate safe, reversible DB migration plans with rollback strategy.",
        "author": "sqlengineer",
        "category": "database",
        "tags": ["database", "migrations", "postgres"],
        "stars": 4.7,
        "downloads": 890,
        "verified": False,
        "compatible_agents": ["opencode", "claude-code"],
        "repo_url": "https://github.com/nebula-forge/skills-db-migrator.git",
        "version": "1.0.0",
    },
    {
        "id": "api-contract-writer",
        "name": "api-contract-writer",
        "description": "Write OpenAPI 3.1 contracts from code and product requirements.",
        "author": "api_guild",
        "category": "documentation",
        "tags": ["openapi", "rest", "docs"],
        "stars": 4.6,
        "downloads": 743,
        "verified": False,
        "compatible_agents": ["opencode", "claude-code", "gemini"],
        "repo_url": "https://github.com/nebula-forge/skills-api-contract-writer.git",
        "version": "1.0.0",
    },
]


class SkillMarketplace:
    """Marketplace index provider with local cache support."""

    def __init__(self, vault: Vault) -> None:
        self.vault = vault
        self.cache_path = self.vault.vault_dir / "marketplace_cache.json"
        self._index: list[MarketplaceSkill] = []

    def fetch_index(self, *, timeout: float = 4.0) -> list[MarketplaceSkill]:
        """Fetch index from network, then cache; fallback to cache/built-ins."""
        self.vault.ensure_dirs()

        try:
            with urlopen(REGISTRY_URL, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            skills_data = payload.get("skills", [])
            self._index = [MarketplaceSkill(**s) for s in skills_data]
            self.cache_path.write_text(raw, encoding="utf-8")
            if self._index:
                return self._index
        except (URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
            pass

        if self.cache_path.exists():
            try:
                payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
                self._index = [MarketplaceSkill(**s) for s in payload.get("skills", [])]
                if self._index:
                    return self._index
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        self._index = [MarketplaceSkill(**s) for s in FALLBACK_SKILLS]
        return self._index

    def search(self, query: str) -> list[MarketplaceSkill]:
        """Search already loaded index (case-insensitive)."""
        q = query.lower().strip()
        if not q:
            return list(self._index)
        return [
            s for s in self._index
            if q in s.name.lower()
            or q in s.description.lower()
            or q in s.author.lower()
            or any(q in t.lower() for t in s.tags)
            or q in s.category.lower()
        ]

    def install(self, skill: MarketplaceSkill, scope: str, cwd: Path) -> tuple[bool, str]:
        """Install skill repo into global or local skill directory."""
        if not skill.repo_url:
            return False, "Missing repo URL"

        if scope == "global":
            target_root = self.vault.skills_dir
        else:
            target_root = self.vault.project_skills_dir(cwd)

        target_root.mkdir(parents=True, exist_ok=True)
        target = target_root / skill.name

        if target.exists():
            return False, f"Skill already exists at {target}"

        try:
            proc = subprocess.run(
                ["git", "clone", "--depth=1", skill.repo_url, str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return True, f"Installed {skill.name}"

            # If clone fails (private/missing repo), scaffold a starter SKILL.md to keep UX smooth.
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text(
                "\n".join([
                    "---",
                    f"name: {skill.name}",
                    f"category: {skill.category}",
                    f"version: {skill.version}",
                    f"author: {skill.author}",
                    "model_preference: copilot/claude-opus-4-6",
                    "thinking_mode: auto",
                    f"tags: {', '.join(skill.tags) if skill.tags else 'general'}",
                    "description: >",
                    f"  {skill.description}",
                    "---",
                    "",
                    f"# Skill: {skill.name}",
                    "",
                    "## Purpose",
                    skill.description,
                    "",
                    "## Instructions",
                    "<!-- Add detailed instructions -->",
                ]),
                encoding="utf-8",
            )
            return True, f"Installed fallback skill scaffold for {skill.name}"
        except Exception as e:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            return False, str(e)
