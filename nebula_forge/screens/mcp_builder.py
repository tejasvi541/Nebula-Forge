"""
NEBULA-FORGE — MCP Plugin Builder Screen
Wizard-like generator for custom MCP servers.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Button, Input, Static, TextArea

from ..mcp_builder import MCPPluginBuilder, MCPTool


class MCPBuilderScreen(Container):
    """Build and scaffold MCP plugins from plain-language descriptions."""

    def __init__(self) -> None:
        super().__init__()
        self.builder = MCPPluginBuilder()
        self._tools: list[MCPTool] = []

    def compose(self) -> ComposeResult:
        cwd = Path.cwd()
        yield Static("  ⬡  MCP PLUGIN BUILDER", classes="section-title")
        yield ScrollableContainer(
            Static("[bold #7dcfff]Generate Custom MCP Server[/]"),
            Static("[#565f89]Describe capabilities, analyze tools, preview, then generate files.[/]\n"),
            Static("[#bb9af7]Project Path[/]"),
            Input(value=str(cwd), id="mcp-project-path"),
            Static("[#bb9af7]Plugin Name[/]"),
            Input(value="notion-mcp", id="mcp-plugin-name"),
            Static("[#bb9af7]Description[/]"),
            TextArea(
                id="mcp-description",
                text="Query our internal Notion workspace to search, read, create, and update pages.",
            ),
            Horizontal(
                Button("Analyze", id="btn-mcp-analyze", classes="btn-primary"),
                Button("Generate Plugin", id="btn-mcp-generate", classes="btn-success"),
            ),
            Container(id="mcp-tools-view"),
            Container(id="mcp-preview-view"),
            classes="panel",
        )

    def on_mount(self) -> None:
        self._analyze()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "btn-mcp-analyze":
            self._analyze()
        elif bid == "btn-mcp-generate":
            self._generate()

    def _analyze(self) -> None:
        desc = self.query_one("#mcp-description", TextArea).text.strip()
        self._tools = self.builder.analyze_description(desc)

        host = self.query_one("#mcp-tools-view", Container)
        host.remove_children()
        host.mount(Static("\n[bold #7dcfff]Detected Tools[/]"))
        for t in self._tools:
            host.mount(Static(f"[#9ece6a]☑[/] [#c0caf5]{t.name}[/] [#565f89]— {t.description}[/]"))

        self._render_preview()

    def _render_preview(self) -> None:
        name = self.query_one("#mcp-plugin-name", Input).value.strip() or "mcp-plugin"
        ts_server = self.builder.generate_typescript_server(name, self._tools)

        host = self.query_one("#mcp-preview-view", Container)
        host.remove_children()
        host.mount(Static("\n[bold #7dcfff]Generation Preview[/]"))
        host.mount(Static("[#565f89]Files: package.json, tsconfig.json, src/server.ts[/]"))
        host.mount(Static(f"[#3b4261]{ts_server[:1800]}[/]"))

    def _generate(self) -> None:
        path_text = self.query_one("#mcp-project-path", Input).value.strip()
        plugin_name = self.query_one("#mcp-plugin-name", Input).value.strip()
        project_path = Path(path_text).expanduser()

        if not project_path.exists() or not project_path.is_dir():
            self.app.notify(f"Invalid project path: {project_path}", severity="error")
            return
        if not plugin_name:
            self.app.notify("Plugin name required", severity="warning")
            return
        if not self._tools:
            self._analyze()

        ok, msg, root = self.builder.write_plugin(project_path, plugin_name, self._tools)
        if ok:
            self.app.notify(f"✓ {msg} → {root}", severity="information")
        else:
            self.app.notify(f"Generate failed: {msg}", severity="error")
