"""
NEBULA-FORGE — Command Center Wizard
First-launch onboarding: keys, paths, preferences.
"""

from __future__ import annotations
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Button, Input, Label, Static, Select, Switch, ProgressBar
)
from textual.containers import (
    Vertical, Horizontal, Container, Center, ScrollableContainer
)
from textual.reactive import reactive
from textual import work
import asyncio

from ..vault import Vault, VAULT_DIR, SKILLS_DIR, AGENTS_DIR, LOGS_DIR
from ..models import VaultConfig, APIKeys

MODELS = [
    ("copilot/claude-opus-4-6", "copilot/claude-opus-4-6"),
    ("copilot/gpt-5.1-codex-max", "copilot/gpt-5.1-codex-max"),
    ("copilot/gemini-3.1-pro-preview", "copilot/gemini-3.1-pro-preview"),
    ("nvidia/devstral-2-123b-instruct-2512", "nvidia/devstral-2-123b-instruct-2512"),
    ("opencodezen/minimax-m2-5", "opencodezen/minimax-m2-5"),
]

STEP_TITLES = [
    "Welcome to NEBULA-FORGE",
    "API Key Configuration",
    "Workspace Settings",
    "Review & Initialize",
]
STEP_DESCS = [
    "The Agentic Orchestrator for SWE Workflows",
    "Configure your AI provider keys — stored locally in ~/.nebula-forge/vault.json",
    "Set up your global workspace and default model preferences",
    "Review your configuration before initializing the Command Center",
]


class WizardScreen(Screen):
    CSS_PATH = "../themes/tokyo_night.tcss"
    BINDINGS = [("escape", "cancel_wizard", "Exit")]

    current_step: reactive[int] = reactive(0)

    def __init__(self, vault: Vault, on_complete=None) -> None:
        super().__init__()
        self.vault = vault
        self._on_complete = on_complete
        self._form_data: dict = {
            "github_copilot": "",
            "google_ai": "",
            "anthropic": "",
            "nvidia": "",
            "base_path": str(VAULT_DIR.parent),
            "default_model": "copilot/claude-opus-4-6",
        }

    # ── Compose ──────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Container(classes="wizard-screen"):
            with Center():
                with Vertical(classes="wizard-panel", id="wizard-panel"):
                    yield Static("", id="wizard-step-indicator")
                    yield Static("", id="wizard-title", classes="wizard-title")
                    yield Static("", id="wizard-desc", classes="wizard-subtitle")
                    yield Static("─" * 60, classes="label-dim")
                    yield Container(id="wizard-body")
                    yield Static("─" * 60, classes="label-dim")
                    with Horizontal(id="wizard-buttons"):
                        yield Button("← Back", id="btn-back", classes="btn-ghost")
                        yield Button("", id="btn-next", classes="btn-primary")

    def on_mount(self) -> None:
        self._render_step()

    # ── Step Rendering ────────────────────────────────────────

    def _render_step(self) -> None:
        s = self.current_step
        self.query_one("#wizard-step-indicator", Static).update(
            f"[#565f89]Step {s+1} of {len(STEP_TITLES)}[/]"
        )
        self.query_one("#wizard-title", Static).update(
            f"[bold #7dcfff]{STEP_TITLES[s]}[/]"
        )
        self.query_one("#wizard-desc", Static).update(
            f"[#565f89]{STEP_DESCS[s]}[/]"
        )
        body = self.query_one("#wizard-body")
        body.remove_children()

        next_btn = self.query_one("#btn-next", Button)
        back_btn = self.query_one("#btn-back", Button)
        back_btn.display = s > 0
        next_btn.label = "Next →" if s < len(STEP_TITLES) - 1 else "⚡ Initialize!"

        if s == 0:
            self._render_welcome(body)
        elif s == 1:
            self._render_keys(body)
        elif s == 2:
            self._render_workspace(body)
        elif s == 3:
            self._render_review(body)

    def _render_welcome(self, body) -> None:
        body.mount(
            Static(
                "\n"
                "[bold #7aa2f7]NEBULA-FORGE[/] is your central command hub for\n"
                "orchestrating AI agents across SWE workflows.\n\n"
                "This wizard will set up:\n"
                "[#9ece6a]  ◈[/] [#c0caf5]API keys for GitHub Copilot, Google AI, Anthropic, NVIDIA[/]\n"
                "[#9ece6a]  ◈[/] [#c0caf5]Global skill registry at ~/.claude/skills/[/]\n"
                "[#9ece6a]  ◈[/] [#c0caf5]Agent workspace at ~/.nebula/agents/[/]\n"
                "[#9ece6a]  ◈[/] [#c0caf5]Secure vault at ~/.nebula-forge/vault.json[/]\n\n"
                "[#565f89]All keys are stored locally. Nothing is transmitted.[/]",
            )
        )

    def _render_keys(self, body) -> None:
        fields = [
            ("github_copilot", "GitHub Copilot Token  [#565f89](REQUIRED — powers Copilot models)[/]", "ghp_..."),
            ("google_ai", "Google AI (Gemini)  [#565f89](optional)[/]", "AIza..."),
            ("anthropic", "Anthropic  [#565f89](optional — Claude via API)[/]", "sk-ant-..."),
            ("nvidia", "NVIDIA NIM  [#565f89](optional — free 1000 calls/month)[/]", "nvapi-..."),
        ]
        for key, label, ph in fields:
            body.mount(Static(label, classes="form-label"))
            inp = Input(
                placeholder=ph,
                password=True,
                id=f"inp-{key}",
                classes="form-row",
            )
            if self._form_data.get(key):
                inp.value = self._form_data[key]
            body.mount(inp)

    def _render_workspace(self, body) -> None:
        body.mount(Static("Global Base Path  [#565f89](parent of your projects)[/]", classes="form-label"))
        body.mount(Input(
            value=self._form_data["base_path"],
            id="inp-base-path",
            classes="form-row",
        ))
        body.mount(Static("Default Model", classes="form-label"))
        body.mount(Select(
            options=MODELS,
            value=self._form_data["default_model"],
            id="sel-model",
        ))
        body.mount(Static(
            "\n[#565f89]Directory structure that will be created:[/]\n"
            "[#9ece6a]  ~/.nebula-forge/vault.json[/]\n"
            "[#9ece6a]  ~/.claude/skills/[/]\n"
            "[#9ece6a]  ~/.nebula/agents/[/]\n"
            "[#9ece6a]  ~/.nebula/logs/[/]\n"
            "[#9ece6a]  ~/.nebula/blueprints/[/]"
        ))

    def _render_review(self, body) -> None:
        cfg = self._build_config()
        lines = [
            "\n[#7dcfff bold]Configuration Summary[/]\n",
            f"[#bb9af7]GitHub Copilot:[/] {'[#9ece6a]✓ set[/]' if cfg.api_keys.github_copilot else '[#f7768e]✗ NOT SET[/]'}",
            f"[#bb9af7]Google AI:     [/] {'[#9ece6a]✓ set[/]' if cfg.api_keys.google_ai else '[#565f89]— skipped[/]'}",
            f"[#bb9af7]Anthropic:     [/] {'[#9ece6a]✓ set[/]' if cfg.api_keys.anthropic else '[#565f89]— skipped[/]'}",
            f"[#bb9af7]NVIDIA NIM:    [/] {'[#9ece6a]✓ set[/]' if cfg.api_keys.nvidia else '[#565f89]— skipped[/]'}",
            f"[#bb9af7]Default Model: [/] [#7aa2f7]{cfg.default_model}[/]",
            f"[#bb9af7]Base Path:     [/] [#565f89]{cfg.global_base_path}[/]",
            "\n[#565f89]Press [bold]⚡ Initialize![/] to create all directories and save config.[/]",
        ]
        body.mount(Static("\n".join(lines)))

    def _build_config(self) -> VaultConfig:
        return VaultConfig(
            api_keys=APIKeys(
                github_copilot=self._form_data.get("github_copilot") or None,
                google_ai=self._form_data.get("google_ai") or None,
                anthropic=self._form_data.get("anthropic") or None,
                nvidia=self._form_data.get("nvidia") or None,
            ),
            global_base_path=self._form_data.get("base_path", str(VAULT_DIR.parent)),
            default_model=self._form_data.get("default_model", "copilot/claude-opus-4-6"),
        )

    # ── Events ────────────────────────────────────────────────

    def _collect_current_inputs(self) -> None:
        """Save current step's inputs before navigating away."""
        s = self.current_step
        if s == 1:
            for key in ("github_copilot", "google_ai", "anthropic", "nvidia"):
                try:
                    inp = self.query_one(f"#inp-{key}", Input)
                    self._form_data[key] = inp.value.strip()
                except Exception:
                    pass
        elif s == 2:
            try:
                self._form_data["base_path"] = self.query_one("#inp-base-path", Input).value.strip()
            except Exception:
                pass
            try:
                sel = self.query_one("#sel-model", Select)
                if sel.value and sel.value != Select.BLANK:
                    self._form_data["default_model"] = str(sel.value)
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-next":
            self._collect_current_inputs()
            if self.current_step == len(STEP_TITLES) - 1:
                self._do_initialize()
            else:
                self.current_step = min(self.current_step + 1, len(STEP_TITLES) - 1)
                self._render_step()
        elif event.button.id == "btn-back":
            self._collect_current_inputs()
            self.current_step = max(0, self.current_step - 1)
            self._render_step()

    def _do_initialize(self) -> None:
        self.run_init()

    @work(exclusive=True)
    async def run_init(self) -> None:
        body = self.query_one("#wizard-body")
        body.remove_children()
        body.mount(Static("\n[#7dcfff]Initializing NEBULA-FORGE...[/]"))
        pb = ProgressBar(total=100, show_eta=False)
        body.mount(pb)
        status = Static("[#565f89]Starting...[/]")
        body.mount(status)

        steps = [
            ("Creating vault directory...", 20),
            ("Saving configuration...", 40),
            ("Creating skill registry...", 60),
            ("Creating agent workspace...", 80),
            ("Finalizing...", 100),
        ]
        cfg = self._build_config()

        for msg, pct in steps:
            status.update(f"[#7aa2f7]{msg}[/]")
            pb.progress = pct
            await asyncio.sleep(0.2)

        self.vault.ensure_dirs()
        cfg.initialized = True
        from datetime import datetime
        cfg.created_at = datetime.now().isoformat()
        self.vault.save(cfg)

        status.update("[#9ece6a]✓ NEBULA-FORGE initialized successfully![/]")
        await asyncio.sleep(0.8)

        if self._on_complete:
            self._on_complete()
        self.dismiss()

    def action_cancel_wizard(self) -> None:
        self.dismiss()
