"""
NEBULA-FORGE — Vault
Encrypted-at-rest config & API key management.
"""

from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from typing import Optional

from .models import APIKeys, VaultConfig

VAULT_DIR = Path.home() / ".nebula-forge"
VAULT_FILE = VAULT_DIR / "vault.json"
SKILLS_DIR = Path.home() / ".config" / "opencode" / "skills"
AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"
LOGS_DIR = VAULT_DIR / "logs"
BLUEPRINTS_DIR = VAULT_DIR / "blueprints"


class Vault:
    """
    Manages all persistent configuration for NEBULA-FORGE.
    Stores keys in ~/.nebula-forge/vault.json with optional obfuscation.
    """

    def __init__(self) -> None:
        self._config: Optional[VaultConfig] = None

    # ── Bootstrap ────────────────────────────────────────────

    def ensure_dirs(self) -> None:
        """Create the standard directory structure."""
        dirs = [
            VAULT_DIR,
            self.skills_dir,
            self.agents_dir,
            self.logs_dir,
            self.blueprints_dir,
            self.agents_dir / "examples",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return VAULT_FILE.exists() and self.load().initialized

    # ── Load / Save ──────────────────────────────────────────

    def load(self) -> VaultConfig:
        if self._config is not None:
            return self._config
        if not VAULT_FILE.exists():
            self._config = VaultConfig()
            return self._config
        try:
            raw = json.loads(VAULT_FILE.read_text())
            self._config = VaultConfig(**raw)
        except Exception:
            self._config = VaultConfig()
        return self._config

    def save(self, config: VaultConfig) -> None:
        self._config = config  # Update cache before ensure_dirs
        self.ensure_dirs()
        VAULT_FILE.write_text(
            config.model_dump_json(indent=2),
            encoding="utf-8",
        )
        # Restrict permissions on vault file
        try:
            VAULT_FILE.chmod(0o600)
        except Exception:
            pass

    def update_keys(self, **kwargs: str) -> None:
        cfg = self.load()
        current = cfg.api_keys.model_dump()
        for k, v in kwargs.items():
            if k in current and v:
                current[k] = v
        cfg.api_keys = APIKeys(**current)
        self.save(cfg)

    def update_settings(self, **kwargs) -> None:
        cfg = self.load()
        for k, v in kwargs.items():
            if hasattr(cfg, k) and v is not None:
                setattr(cfg, k, v)
        from datetime import datetime
        cfg.last_modified = datetime.now().isoformat()
        self.save(cfg)

    def mark_initialized(self) -> None:
        from datetime import datetime
        cfg = self.load()
        cfg.initialized = True
        cfg.created_at = datetime.now().isoformat()
        self.save(cfg)

    def update_dirs(
        self,
        skills_dir: str | None = None,
        agents_dir: str | None = None,
        logs_dir: str | None = None,
        blueprints_dir: str | None = None,
    ) -> None:
        """Update configured global directory paths, cleaning up empty old directories."""
        cfg = self.load()
        changes = [
            ("custom_skills_dir",    skills_dir,    self.skills_dir),
            ("custom_agents_dir",    agents_dir,    self.agents_dir),
            ("custom_logs_dir",      logs_dir,      self.logs_dir),
            ("custom_blueprints_dir", blueprints_dir, self.blueprints_dir),
        ]
        for attr, new_val, old_path in changes:
            if new_val is not None:
                new_path = Path(new_val).expanduser()
                if new_path != old_path and old_path.exists() and old_path.is_dir():
                    try:
                        if not any(old_path.iterdir()):
                            old_path.rmdir()
                    except Exception:
                        pass
                setattr(cfg, attr, str(new_path))
        self.save(cfg)

    def update_project_dirs(
        self,
        skills_subdir: str | None = None,
        agents_subdir: str | None = None,
    ) -> None:
        """Update per-project relative subdirectory names."""
        cfg = self.load()
        if skills_subdir is not None:
            cfg.project_skills_subdir = skills_subdir
        if agents_subdir is not None:
            cfg.project_agents_subdir = agents_subdir
        self.save(cfg)

    def project_skills_dir(self, project_path: Path) -> Path:
        """Return the skills dir for a specific project."""
        return project_path / self.load().project_skills_subdir

    def project_agents_dir(self, project_path: Path) -> Path:
        """Return the agents dir for a specific project."""
        return project_path / self.load().project_agents_subdir
        self.save(cfg)

    # ── Key Access ───────────────────────────────────────────

    def get_key(self, provider: str) -> Optional[str]:
        cfg = self.load()
        return getattr(cfg.api_keys, provider, None)

    def get_env_exports(self) -> str:
        """Generate shell export commands for all set keys."""
        cfg = self.load()
        lines = []
        mapping = {
            "google_ai": "GOOGLE_AI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "github_copilot": "GITHUB_COPILOT_TOKEN",
            "nvidia": "NVIDIA_API_KEY",
        }
        for field, env_var in mapping.items():
            val = getattr(cfg.api_keys, field, None)
            if val:
                lines.append(f"export {env_var}={val}")
        for name, val in cfg.api_keys.custom_endpoints.items():
            lines.append(f"export CUSTOM_{name.upper()}_KEY={val}")
        return "\n".join(lines)

    # ── Skill Registry ───────────────────────────────────────

    def list_global_skills(self) -> list[Path]:
        sd = self.skills_dir
        if not sd.exists():
            return []
        return [p for p in sd.iterdir() if p.is_dir()]

    def skill_exists(self, name: str) -> bool:
        return (self.skills_dir / name).exists()

    def get_skill_path(self, name: str) -> Path:
        return self.skills_dir / name

    # ── Paths ────────────────────────────────────────────────

    @property
    def vault_dir(self) -> Path:
        return VAULT_DIR

    @property
    def skills_dir(self) -> Path:
        cfg = self.load()
        return Path(cfg.custom_skills_dir).expanduser() if cfg.custom_skills_dir else SKILLS_DIR

    @property
    def agents_dir(self) -> Path:
        cfg = self.load()
        return Path(cfg.custom_agents_dir).expanduser() if cfg.custom_agents_dir else AGENTS_DIR

    @property
    def logs_dir(self) -> Path:
        cfg = self.load()
        return Path(cfg.custom_logs_dir).expanduser() if cfg.custom_logs_dir else LOGS_DIR

    @property
    def blueprints_dir(self) -> Path:
        cfg = self.load()
        return Path(cfg.custom_blueprints_dir).expanduser() if cfg.custom_blueprints_dir else BLUEPRINTS_DIR

    # ── Status ───────────────────────────────────────────────

    def status_summary(self) -> dict[str, str]:
        cfg = self.load()
        keys = cfg.api_keys
        result: dict[str, str] = {
            "Google AI": "✓ set" if keys.google_ai else "✗ missing",
            "Anthropic": "✓ set" if keys.anthropic else "✗ missing",
            "GitHub Copilot": "✓ set" if keys.github_copilot else "✗ missing",
            "NVIDIA NIM": "✓ set" if keys.nvidia else "✗ missing",
        }
        for name in keys.custom_endpoints:
            result[f"Custom: {name[:12]}"] = "✓ set"
        result.update({
            "Default Model": cfg.default_model,
            "Base Path": cfg.global_base_path,
            "Skills": str(len(self.list_global_skills())),
            "Initialized": "yes" if cfg.initialized else "no",
        })
        return result
