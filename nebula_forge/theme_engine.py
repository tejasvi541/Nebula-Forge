"""
NEBULA-FORGE — Theme Engine (Foundation)
Provides theme metadata and CSS override path resolution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeOption:
    key: str
    label: str
    override_css: str


THEMES: list[ThemeOption] = [
    ThemeOption("tokyo_night", "Tokyo Night (default)", "themes/overrides/tokyo_night.tcss"),
    ThemeOption("dracula", "Dracula", "themes/overrides/dracula.tcss"),
    ThemeOption("nord", "Nord", "themes/overrides/nord.tcss"),
    ThemeOption("gruvbox", "Gruvbox", "themes/overrides/gruvbox.tcss"),
]


class ThemeEngine:
    """Resolve and validate available themes."""

    def list_themes(self) -> list[ThemeOption]:
        return THEMES

    def get_theme(self, key: str) -> ThemeOption:
        for t in THEMES:
            if t.key == key:
                return t
        return THEMES[0]

    def css_paths_for(self, key: str) -> list[str]:
        theme = self.get_theme(key)
        return ["themes/tokyo_night.tcss", theme.override_css]
