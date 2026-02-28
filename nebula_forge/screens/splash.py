"""
NEBULA-FORGE — Splash Screen
ASCII art + animated loading on startup.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, ProgressBar, Label
from textual.containers import Center, Middle, Vertical
from textual import work
from rich.text import Text
import asyncio

NEBULA_ASCII = r"""
███╗   ██╗███████╗██████╗ ██╗   ██╗██╗      █████╗        
████╗  ██║██╔════╝██╔══██╗██║   ██║██║     ██╔══██╗       
██╔██╗ ██║█████╗  ██████╔╝██║   ██║██║     ███████║       
██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║██║     ██╔══██║       
██║ ╚████║███████╗██████╔╝╚██████╔╝███████╗██║  ██║       
╚═╝  ╚═══╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝       
                                                            
███████╗ ██████╗ ██████╗  ██████╗ ███████╗                
██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝                
█████╗  ██║   ██║██████╔╝██║  ███╗█████╗                  
██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝                  
██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗                 
╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝                 
"""

BOOT_STEPS = [
    ("◈ Initializing Vault...         ", 0.12),
    ("◈ Loading Skill Registry...      ", 0.25),
    ("◈ Scanning Agent Manifests...    ", 0.40),
    ("◈ Connecting Providers...        ", 0.55),
    ("◈ Bootstrapping Provisioner...   ", 0.70),
    ("◈ Heating up Reasoning Core...   ", 0.85),
    ("◈ Nebula Forge is ready.         ", 1.00),
]


def _colorize_ascii(text: str) -> Text:
    """Apply gradient coloring to ASCII art lines."""
    colors = [
        "#7aa2f7", "#7aa2f7",
        "#7dcfff", "#7dcfff",
        "#bb9af7", "#bb9af7",
        "#9ece6a", "#9ece6a",
        "#7aa2f7",
        "#bb9af7", "#bb9af7", "#bb9af7",
        "#7dcfff", "#7dcfff", "#7dcfff",
    ]
    rich_text = Text()
    for i, line in enumerate(text.split("\n")):
        color = colors[i % len(colors)]
        rich_text.append(line + "\n", style=color)
    return rich_text


class SplashScreen(Screen):
    CSS_PATH = "../themes/tokyo_night.tcss"

    BINDINGS = [("enter", "dismiss_splash", "Continue")]

    def compose(self) -> ComposeResult:
        with Middle(id="splash-screen"):
            with Center():
                yield Static(_colorize_ascii(NEBULA_ASCII), id="splash-ascii")
            with Center():
                yield Static(
                    "  ◆  The Agentic Orchestrator  ·  v1.0.0  ◆",
                    id="splash-tagline",
                )
                yield Static(
                    "   Gemini 3.1 Pro  ·  Claude Opus 4.6  ·  GPT-5 Codex",
                    classes="label-dim",
                )
            with Center(id="splash-loading"):
                yield Static("", id="splash-status")
                yield ProgressBar(total=100, show_eta=False, id="splash-progress")

    def on_mount(self) -> None:
        self.run_boot_sequence()

    @work(exclusive=True)
    async def run_boot_sequence(self) -> None:
        progress = self.query_one("#splash-progress", ProgressBar)
        status = self.query_one("#splash-status", Static)
        for msg, pct in BOOT_STEPS:
            status.update(f"[#565f89]{msg}[/]")
            progress.progress = int(pct * 100)
            await asyncio.sleep(0.22)
        status.update("[#9ece6a]✓ System ready — press ENTER to launch[/]")

    def action_dismiss_splash(self) -> None:
        self.app.pop_screen()

    def on_key(self, event) -> None:
        self.app.pop_screen()
