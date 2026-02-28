"""
NEBULA-FORGE — Blueprint Generator
Dynamic markdown generation for SWE workflows.
"""

from __future__ import annotations
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import (
    Button, Input, Static, TabbedContent, TabPane,
    TextArea, Select, ProgressBar
)
from textual.containers import (
    Vertical, Horizontal, Container, ScrollableContainer, Grid
)
from textual.reactive import reactive
from textual import work
import asyncio

from ..vault import Vault
from ..provisioner import Provisioner
from ..models import BlueprintTemplate, BlueprintVariable

TEMPLATES: list[BlueprintTemplate] = [
    BlueprintTemplate(
        id="refactor",
        name="Massive Refactor",
        description="Multi-file refactor with test safety net, phased approach, and conventional commits.",
        template_type="refactor",
        icon="◉",
        thinking_mode="ultra",
        model_context="high_effort",
        preferred_model="copilot/claude-opus-4-6",
        variables=[
            BlueprintVariable(key="project", label="Project Name", placeholder="MyApp"),
            BlueprintVariable(key="module", label="Target Module/Path", placeholder="src/auth/"),
            BlueprintVariable(key="objective", label="Refactor Objective", placeholder="Improve modularity"),
            BlueprintVariable(key="complexity", label="Complexity", default="High"),
            BlueprintVariable(key="coverage", label="Current Test Coverage", placeholder="~60%"),
            BlueprintVariable(key="test_cmd", label="Test Command", placeholder="npm test"),
            BlueprintVariable(key="issues", label="Known Issues", placeholder="High coupling, no types"),
            BlueprintVariable(key="goal1", label="Goal 1", placeholder="Add TypeScript types"),
            BlueprintVariable(key="goal2", label="Goal 2", placeholder="Reduce file size"),
            BlueprintVariable(key="goal3", label="Goal 3", placeholder="Add unit tests"),
            BlueprintVariable(key="critical_paths", label="Critical Paths", placeholder="login, checkout"),
            BlueprintVariable(key="success", label="Success Criteria", placeholder="All tests pass"),
            BlueprintVariable(key="model", label="Preferred Model", default="copilot/claude-opus-4-6"),
        ],
    ),
    BlueprintTemplate(
        id="migration",
        name="Legacy Migration",
        description="Strangler fig pattern migration from legacy to modern stack with rollback strategy.",
        template_type="migration",
        icon="⟲",
        thinking_mode="ultra",
        model_context="high_effort",
        preferred_model="copilot/gemini-3.1-pro-preview",
        variables=[
            BlueprintVariable(key="project", label="Project Name", placeholder="LegacyApp"),
            BlueprintVariable(key="from_tech", label="From Technology", placeholder="PHP Monolith"),
            BlueprintVariable(key="to_tech", label="To Technology", placeholder="Node.js Microservices"),
            BlueprintVariable(key="timeline", label="Timeline", placeholder="Q1 2026"),
            BlueprintVariable(key="risks", label="High Risk Areas", placeholder="auth, payments"),
            BlueprintVariable(key="domain1", label="Domain 1", placeholder="Auth"),
            BlueprintVariable(key="domain2", label="Domain 2", placeholder="Products"),
            BlueprintVariable(key="domain3", label="Domain 3", placeholder="Orders"),
            BlueprintVariable(key="error_threshold", label="Rollback Error Threshold", default="1%"),
            BlueprintVariable(key="soak_period", label="Soak Period", default="2 weeks"),
            BlueprintVariable(key="rollback", label="Rollback Strategy", placeholder="Feature flags"),
            BlueprintVariable(key="model", label="Preferred Model", default="copilot/gemini-3.1-pro-preview"),
        ],
    ),
    BlueprintTemplate(
        id="architecture",
        name="System Architecture",
        description="C4 model system design with NFRs, data model, API design, and infrastructure plan.",
        template_type="architecture",
        icon="⬡",
        thinking_mode="ultra",
        model_context="high_effort",
        preferred_model="copilot/claude-opus-4-6",
        variables=[
            BlueprintVariable(key="project", label="Project Name", placeholder="NewPlatform"),
            BlueprintVariable(key="system_name", label="System Name", placeholder="Payment Service"),
            BlueprintVariable(key="scope", label="Scope", placeholder="Core Platform"),
            BlueprintVariable(key="req1", label="Requirement 1", placeholder="Users can register"),
            BlueprintVariable(key="req2", label="Requirement 2", placeholder="Process payments"),
            BlueprintVariable(key="req3", label="Requirement 3", placeholder="Send notifications"),
            BlueprintVariable(key="availability", label="Availability SLA", default="99.9%"),
            BlueprintVariable(key="latency", label="Latency Target", default="p99 < 200ms"),
            BlueprintVariable(key="scale", label="Scale Target", default="10k concurrent users"),
            BlueprintVariable(key="security", label="Security Requirements", default="SOC2"),
            BlueprintVariable(key="api_tech", label="API Gateway Tech", placeholder="Kong"),
            BlueprintVariable(key="app_tech", label="App Tech", placeholder="FastAPI"),
            BlueprintVariable(key="db_tech", label="Database", placeholder="PostgreSQL"),
            BlueprintVariable(key="cache_tech", label="Cache", default="Redis"),
            BlueprintVariable(key="queue_tech", label="Queue", default="SQS"),
            BlueprintVariable(key="api_style", label="API Style", default="REST"),
            BlueprintVariable(key="auth", label="Auth Method", default="JWT + OAuth2"),
            BlueprintVariable(key="cloud", label="Cloud Provider", default="AWS"),
            BlueprintVariable(key="deploy_target", label="Deploy Target", default="ECS"),
            BlueprintVariable(key="adr1", label="ADR 1", placeholder="Why PostgreSQL"),
            BlueprintVariable(key="adr2", label="ADR 2", placeholder="Sync vs async"),
            BlueprintVariable(key="question1", label="Open Question 1", placeholder="Sharding strategy?"),
            BlueprintVariable(key="question2", label="Open Question 2", placeholder="Cache invalidation?"),
            BlueprintVariable(key="model", label="Preferred Model", default="copilot/claude-opus-4-6"),
        ],
    ),
]


class BlueprintScreen(Container):
    """Blueprint Generator — high-fidelity SWE markdown with agent triggers."""

    selected_template: reactive[str | None] = reactive(None)

    def __init__(self, vault: Vault, provisioner: Provisioner) -> None:
        super().__init__()
        self.vault = vault
        self.provisioner = provisioner
        self._current_template: BlueprintTemplate | None = None
        self._generated_content: str = ""

    def compose(self) -> ComposeResult:
        yield Static("  ◈  BLUEPRINT GENERATOR  —  Agent Scratchpad", classes="section-title")
        with TabbedContent(id="bp-tabs"):
            with TabPane("  Templates  ", id="tab-templates"):
                yield self._build_templates()
            with TabPane("  Configure  ", id="tab-configure"):
                yield Container(
                    Static("[#565f89]Select a template first.[/]"),
                    id="configure-view",
                )
            with TabPane("  Preview  ", id="tab-preview"):
                yield Container(
                    Static("[#565f89]Fill in the form, then click Generate Blueprint.[/]"),
                    id="preview-view",
                )

    # ── Templates ─────────────────────────────────────────────

    def _build_templates(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Choose a Blueprint Template[/]"),
            Static("[#565f89]Each template generates a Markdown file with [thinking_mode: ultra] triggers.[/]\n"),
            *[self._make_template_card(t) for t in TEMPLATES],
            classes="panel",
        )

    def _make_template_card(self, tmpl: BlueprintTemplate) -> Container:
        return Container(
            Horizontal(
                Static(f"[bold #bb9af7]{tmpl.icon}  {tmpl.name}[/]", classes="blueprint-name"),
                Static(f"[#9ece6a]{tmpl.thinking_mode}[/]  [#7dcfff]{tmpl.preferred_model.split('/')[-1]}[/]"),
            ),
            Static(f"[#565f89]{tmpl.description}[/]", classes="blueprint-desc"),
            Static(
                f"[#3b4261]{len(tmpl.variables)} variables  ·  "
                f"[thinking_mode: {tmpl.thinking_mode}]  ·  "
                f"[model_context: {tmpl.model_context}][/]"
            ),
            Button(
                f"Configure {tmpl.icon} {tmpl.name}",
                id=f"select-tmpl-{tmpl.id}",
                classes="btn-primary",
            ),
            classes="blueprint-card",
            id=f"tmpl-card-{tmpl.id}",
        )

    # ── Configure Tab ─────────────────────────────────────────

    def _build_configure_for(self, tmpl: BlueprintTemplate) -> ScrollableContainer:
        var_widgets: list = [
            Static(f"[bold #7dcfff]{tmpl.icon}  {tmpl.name}[/]"),
            Static(
                f"[#565f89]{tmpl.description}[/]\n"
                f"[#3b4261]Model: {tmpl.preferred_model}  ·  "
                f"thinking_mode: {tmpl.thinking_mode}[/]\n"
            ),
        ]
        for var in tmpl.variables:
            label = f"[#bb9af7]{var.label}[/]"
            if not var.required:
                label += " [#565f89](optional)[/]"
            var_widgets.append(Static(label))
            var_widgets.append(Input(
                placeholder=var.placeholder or var.default,
                value=var.default,
                id=f"var-{var.key}",
            ))
        var_widgets.extend([
            Static(""),
            Horizontal(
                Button("⚡  Generate Blueprint", id="btn-generate", classes="btn-success"),
                Button("← Back", id="btn-back-templates", classes="btn-ghost"),
            ),
        ])
        return ScrollableContainer(*var_widgets, id="configure-inner")

    # ── Events ────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid.startswith("select-tmpl-"):
            tmpl_id = bid[12:]
            tmpl = next((t for t in TEMPLATES if t.id == tmpl_id), None)
            if tmpl:
                self._current_template = tmpl
                self._load_configure(tmpl)

        elif bid == "btn-generate":
            self._generate()

        elif bid == "btn-back-templates":
            try:
                self.query_one("#bp-tabs", TabbedContent).active = "tab-templates"
            except Exception:
                pass

        elif bid == "btn-save-blueprint":
            self._save_blueprint()

        elif bid == "btn-copy-preview":
            self.app.notify("Use Save to file — clipboard not available in TUI", severity="warning")

    def _load_configure(self, tmpl: BlueprintTemplate) -> None:
        try:
            configure_view = self.query_one("#configure-view")
            configure_view.remove_children()
            configure_view.mount(self._build_configure_for(tmpl))
            self.query_one("#bp-tabs", TabbedContent).active = "tab-configure"
        except Exception as e:
            self.app.notify(f"Error loading template: {e}", severity="error")

    def _generate(self) -> None:
        if not self._current_template:
            self.app.notify("Select a template first", severity="warning")
            return

        variables: dict[str, str] = {}
        for var in self._current_template.variables:
            try:
                inp = self.query_one(f"#var-{var.key}", Input)
                variables[var.key] = inp.value.strip() or var.default
            except Exception:
                variables[var.key] = var.default

        project_name = variables.get("project", "MyProject")
        self.run_generate(self._current_template.id, variables, project_name)

    @work(exclusive=True)
    async def run_generate(self, tmpl_id: str, variables: dict, project_name: str) -> None:
        try:
            preview_view = self.query_one("#preview-view")
            preview_view.remove_children()
            preview_view.mount(Static("[#7dcfff]Generating blueprint...[/]"))
            pb = ProgressBar(total=100, show_eta=False)
            preview_view.mount(pb)

            for i in range(0, 101, 20):
                pb.progress = i
                await asyncio.sleep(0.1)

            content = self.provisioner.generate_blueprint(tmpl_id, variables, project_name)
            self._generated_content = content

            preview_view.remove_children()
            tmpl = self._current_template
            preview_view.mount(Static(
                f"[bold #9ece6a]✓ Blueprint generated:[/] "
                f"[#7dcfff]{tmpl.name}[/]  [#565f89]· {len(content.split(chr(10)))} lines[/]\n"
            ))

            # Preview with syntax highlighting style
            lines = content.split("\n")
            preview_chunks = []
            chunk = []
            for line in lines:
                chunk.append(line)
                if len(chunk) >= 30:
                    preview_chunks.append("\n".join(chunk))
                    chunk = []
            if chunk:
                preview_chunks.append("\n".join(chunk))

            scroll = ScrollableContainer()
            for chunk_text in preview_chunks:
                # Color YAML frontmatter
                colored = self._colorize_md(chunk_text)
                scroll.mount(Static(colored))

            preview_view.mount(scroll)
            preview_view.mount(Horizontal(
                Button("💾  Save Blueprint", id="btn-save-blueprint", classes="btn-success"),
                Button("📋  Copy", id="btn-copy-preview", classes="btn-ghost"),
            ))

            self.query_one("#bp-tabs", TabbedContent).active = "tab-preview"
            self.app.notify("✓ Blueprint ready", severity="information")

        except Exception as e:
            self.app.notify(f"Generation failed: {e}", severity="error")

    def _colorize_md(self, text: str) -> str:
        """Apply simple color markup for markdown display."""
        lines = text.split("\n")
        result = []
        in_frontmatter = False
        for i, line in enumerate(lines):
            if i == 0 and line == "---":
                in_frontmatter = True
                result.append(f"[#565f89]{line}[/]")
            elif in_frontmatter and line == "---":
                in_frontmatter = False
                result.append(f"[#565f89]{line}[/]")
            elif in_frontmatter:
                if ":" in line:
                    k, _, v = line.partition(":")
                    result.append(f"[#bb9af7]{k}:[/][#c0caf5]{v}[/]")
                else:
                    result.append(f"[#565f89]{line}[/]")
            elif line.startswith("# "):
                result.append(f"[bold #7dcfff]{line}[/]")
            elif line.startswith("## "):
                result.append(f"[bold #7aa2f7]{line}[/]")
            elif line.startswith("### "):
                result.append(f"[#bb9af7]{line}[/]")
            elif line.startswith("- [ ]"):
                result.append(f"[#565f89]{line}[/]")
            elif line.startswith("> "):
                result.append(f"[#e0af68]{line}[/]")
            elif line.startswith("```"):
                result.append(f"[#3b4261]{line}[/]")
            else:
                result.append(f"[#c0caf5]{line}[/]")
        return "\n".join(result)

    def _save_blueprint(self) -> None:
        if not self._generated_content or not self._current_template:
            self.app.notify("Nothing to save", severity="warning")
            return
        tmpl = self._current_template
        import re
        from datetime import datetime
        slug = re.sub(r"[^\w-]", "-", tmpl.name.lower())
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        filename = f"{slug}-{ts}"
        path = self.provisioner.save_blueprint(self._generated_content, filename)
        self.app.notify(f"✓ Saved to {path}", severity="information")
