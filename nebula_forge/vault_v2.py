"""
NEBULA-FORGE — Vault v2 Foundation
Profile-aware vault manager with migration helpers and encryption-ready hooks.

NOTE:
- This is a compatibility-focused foundation layer.
- It keeps current behavior stable and introduces a clear migration path.
- Strong encryption can be enabled later when `cryptography` is added as a runtime dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import VaultConfig
from .vault import Vault


@dataclass
class VaultV2Status:
    active_profile: str
    profile_count: int
    encryption_enabled: bool
    auto_lock_minutes: int


class VaultV2Manager:
    """Thin manager for v2 profile metadata and migration state."""

    def __init__(self, vault: Vault) -> None:
        self.vault = vault

    def migrate_if_needed(self) -> VaultConfig:
        """Ensure profile metadata exists and save once if migration occurred."""
        cfg = self.vault.load()
        changed = False

        if not cfg.key_profiles:
            cfg.key_profiles = {"default": cfg.api_keys}
            changed = True

        if cfg.active_profile not in cfg.key_profiles:
            cfg.active_profile = "default"
            changed = True

        if changed:
            self.vault.save(cfg)

        return cfg

    def status(self) -> VaultV2Status:
        cfg = self.migrate_if_needed()
        return VaultV2Status(
            active_profile=cfg.active_profile,
            profile_count=len(cfg.key_profiles),
            encryption_enabled=cfg.encryption_enabled,
            auto_lock_minutes=cfg.auto_lock_minutes,
        )

    def enable_encryption(self, passphrase: str) -> tuple[bool, str]:
        """Encryption-ready hook (no-op until cryptography backend is integrated)."""
        if not passphrase.strip():
            return False, "Passphrase is required"

        cfg = self.migrate_if_needed()
        cfg.encryption_enabled = True
        self.vault.save(cfg)
        return True, "Encryption mode flagged (backend integration pending)"

    def disable_encryption(self) -> tuple[bool, str]:
        cfg = self.migrate_if_needed()
        cfg.encryption_enabled = False
        self.vault.save(cfg)
        return True, "Encryption mode disabled"

    def set_auto_lock(self, minutes: int) -> tuple[bool, str]:
        if minutes < 1:
            return False, "Auto-lock must be >= 1 minute"
        cfg = self.migrate_if_needed()
        cfg.auto_lock_minutes = minutes
        self.vault.save(cfg)
        return True, f"Auto-lock set to {minutes} minute(s)"
