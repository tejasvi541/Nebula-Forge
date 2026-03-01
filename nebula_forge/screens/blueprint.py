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
        self._studio_answers: dict[str, str] = {}
        self._studio_template_id: str = "refactor"
        self._studio_index: int = 0
        self._studio_questions: list[tuple[str, str, str]] = self._studio_questions_for("refactor")

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
            with TabPane("  Studio  ", id="tab-studio"):
                yield self._build_studio_tab()

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

    # ── Blueprint Studio (Interview Mode) ────────────────────────

    def _build_studio_tab(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Blueprint Studio — AI Interview (Foundation)[/]"),
            Static("[#565f89]Answer guided questions. Confidence increases with completion.[/]\n"),
            Static("[#bb9af7]Goal[/]"),
            Input(
                placeholder="Describe the objective (e.g., migrate REST to GraphQL)",
                id="studio-goal",
            ),
            Static("[#bb9af7]Template[/]"),
            Select(
                options=[
                    ("Massive Refactor", "refactor"),
                    ("Legacy Migration", "migration"),
                    ("System Architecture", "architecture"),
                ],
                value="refactor",
                id="studio-template",
            ),
            Static("", id="studio-progress"),
            Static("", id="studio-question"),
            Input(placeholder="Type your answer...", id="studio-answer"),
            Horizontal(
                Button("Next", id="btn-studio-next", classes="btn-primary"),
                Button("Skip", id="btn-studio-skip", classes="btn-ghost"),
                Button("Reset", id="btn-studio-reset", classes="btn-ghost"),
            ),
            Horizontal(
                Button("Generate Plan", id="btn-studio-generate", classes="btn-success"),
            ),
            Container(id="studio-summary"),
            classes="panel",
        )

    def _studio_questions_for(self, template_id: str) -> list[tuple[str, str, str]]:
        if template_id == "migration":
            return [
                ("project", "Project name?", "my-platform"),
                ("from_tech", "Current stack?", "REST monolith"),
                ("to_tech", "Target stack?", "GraphQL services"),
                ("timeline", "Timeline?", "3 months"),
                ("risks", "Top risks?", "auth, data consistency"),
                ("rollback", "Rollback strategy?", "feature flags"),
            ]
        if template_id == "architecture":
            return [
                ("project", "Project name?", "new-platform"),
                ("system_name", "System name?", "Payments Service"),
                ("scope", "Scope?", "Core billing"),
                ("availability", "Availability target?", "99.9%"),
                ("latency", "Latency target?", "p99 < 200ms"),
                ("security", "Security requirement?", "SOC2"),
            ]
        return [
            ("project", "Project name?", "my-app"),
            ("module", "Target module/path?", "src/auth"),
            ("objective", "Main objective?", "improve modularity"),
            ("coverage", "Current test coverage?", "~60%"),
            ("critical_paths", "Critical user paths?", "login, checkout"),
            ("success", "Success criteria?", "tests green, no regressions"),
        ]

    def on_mount(self) -> None:
        self._refresh_studio_ui()

    def _refresh_studio_ui(self) -> None:
        total = max(len(self._studio_questions), 1)
        answered = sum(1 for k, _, _ in self._studio_questions if self._studio_answers.get(k))
        confidence = int((answered / total) * 100)

        try:
            self.query_one("#studio-progress", Static).update(
                f"[#565f89]Interview:[/] [#7aa2f7]{answered}/{total}[/]  "
                f"[#565f89]Confidence:[/] [#9ece6a]{confidence}%[/]"
            )
        except Exception:
            pass

        if 0 <= self._studio_index < len(self._studio_questions):
            key, label, hint = self._studio_questions[self._studio_index]
            try:
                self.query_one("#studio-question", Static).update(
                    f"\n[bold #bb9af7]Q{self._studio_index + 1}:[/] [#c0caf5]{label}[/]"
                )
                inp = self.query_one("#studio-answer", Input)
                inp.placeholder = hint
                inp.value = self._studio_answers.get(key, "")
            except Exception:
                pass
        else:
            try:
                self.query_one("#studio-question", Static).update("\n[#9ece6a]Interview complete. Generate your plan.[/]")
                self.query_one("#studio-answer", Input).value = ""
            except Exception:
                pass

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

        elif bid == "btn-studio-next":
            self._studio_capture_current(skip=False)
        elif bid == "btn-studio-skip":
            self._studio_capture_current(skip=True)
        elif bid == "btn-studio-reset":
            self._studio_answers = {}
            self._studio_index = 0
            self._refresh_studio_ui()
        elif bid == "btn-studio-generate":
            self._studio_generate_blueprint()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "studio-template":
            val = event.value
            if val == Select.BLANK:
                return
            self._studio_template_id = str(val)
            self._studio_questions = self._studio_questions_for(self._studio_template_id)
            self._studio_answers = {}
            self._studio_index = 0
            self._refresh_studio_ui()

    def _studio_capture_current(self, *, skip: bool) -> None:
        if self._studio_index >= len(self._studio_questions):
            return
        key, _, _ = self._studio_questions[self._studio_index]
        try:
            answer = self.query_one("#studio-answer", Input).value.strip()
        except Exception:
            answer = ""

        if not skip and answer:
            self._studio_answers[key] = answer

        self._studio_index += 1
        self._refresh_studio_ui()

    def _studio_generate_blueprint(self) -> None:
        try:
            goal = self.query_one("#studio-goal", Input).value.strip()
        except Exception:
            goal = ""

        vars_from_interview = dict(self._studio_answers)
        if goal and not vars_from_interview.get("objective"):
            vars_from_interview["objective"] = goal
        if goal and not vars_from_interview.get("project"):
            vars_from_interview["project"] = goal.split()[0].lower().strip("-_") or "project"

        project_name = vars_from_interview.get("project", "MyProject")
        self.run_generate(self._studio_template_id, vars_from_interview, project_name)

        try:
            summary = self.query_one("#studio-summary", Container)
            total = max(len(self._studio_questions), 1)
            answered = sum(1 for k, _, _ in self._studio_questions if self._studio_answers.get(k))
            confidence = int((answered / total) * 100)
            summary.remove_children()
            summary.mount(Static(
                f"\n[#565f89]Generated from Studio interview — answered {answered}/{total} · confidence {confidence}%[/]"
            ))
        except Exception:
            pass

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
