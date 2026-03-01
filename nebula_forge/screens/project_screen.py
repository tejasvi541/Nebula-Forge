"""
NEBULA-FORGE — Project Provisioner
Detect project, inject skills, bootstrap agent config.
"""

from __future__ import annotations
import os
import difflib
from pathlib import Path
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import (
    Button, Input, Label, Static, TabbedContent, TabPane,
    Checkbox, ProgressBar, Switch, TextArea
)
from textual.containers import (
    Vertical, Horizontal, Container, ScrollableContainer
)
from textual.reactive import reactive
from textual import work
import asyncio

from ..vault import Vault
from ..provisioner import Provisioner
from ..models import ProjectContext, OPENCODE_PLUGINS


class ProjectScreen(Container):
    """Project-Specific Provisioner — one-click agent bootstrap."""

    def __init__(self, vault: Vault, provisioner: Provisioner) -> None:
        super().__init__()
        self.vault = vault
        self.provisioner = provisioner
        self._ctx: ProjectContext | None = None
        self._selected_skills: list[str] = []
        self._pending_agents_write_path: Path | None = None
        self._pending_agents_write_content: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("  ◈  PROJECT PROVISIONER", classes="section-title")
        with TabbedContent(id="project-tabs"):
            with TabPane("  Detect  ", id="tab-detect"):
                yield self._build_detect()
            with TabPane("  Inject Skills  ", id="tab-inject"):
                yield self._build_inject()
            with TabPane("  Plugins  ", id="tab-plugins"):
                yield self._build_plugins_tab()
            with TabPane("  Context Architect  ", id="tab-architect"):
                yield self._build_architect_tab()
            with TabPane("  Ghost Diff  ", id="tab-diff"):
                yield Container(
                    Static("[#565f89]Run detection first, then click 'Preview Plan'[/]"),
                    id="diff-view",
                )
            with TabPane("  Execute  ", id="tab-execute"):
                yield Container(
                    Static("[#565f89]Review the Ghost Diff, then click 'Bootstrap Project'[/]"),
                    id="execute-view",
                )

    # ── Detect Tab ────────────────────────────────────────────

    def _build_detect(self) -> ScrollableContainer:
        cwd = Path(os.getcwd())
        return ScrollableContainer(
            Static("[bold #7dcfff]Project Detection[/]"),
            Static("[#565f89]NEBULA-FORGE scans your current directory for project signals.[/]\n"),
            Static("[#bb9af7]Project Path[/]"),
            Input(value=str(cwd), id="project-path"),
            Horizontal(
                Button("🔍  Scan Project", id="btn-scan", classes="btn-primary"),
                Button("📁  Use CWD", id="btn-use-cwd", classes="btn-ghost"),
            ),
            Container(id="detect-results"),
            classes="panel",
        )

    def _build_detect_results(self, ctx: ProjectContext) -> Container:
        stack_str = ", ".join(ctx.detected_stack) if ctx.detected_stack else "Unknown"

        status_items = [
            ("Git Repository",      ctx.has_git),
            ("AGENTS.md",           ctx.has_agents_md),
            ("opencode.json",       ctx.has_opencode_json),
            (".opencode/ dir",      ctx.has_opencode_dir),
            ("CLAUDE.md (legacy)",  ctx.has_claude_md),
        ]
        lines = "\n[bold #7dcfff]Status Checklist[/]\n"
        for label, present in status_items:
            icon = "[#9ece6a]✓[/]" if present else "[#f7768e]✗[/]"
            note = "" if present else "[#565f89](will be created)[/]"
            lines += f"  {icon}  [#c0caf5]{label:20}[/] {note}\n"

        return Container(
            Static(f"\n[bold #7dcfff]Project: {ctx.name}[/]  [#565f89]{ctx.path}[/]"),
            Static(f"[#bb9af7]Stack:[/]  [#9ece6a]{stack_str}[/]"),
            Static(lines),
            Static(f"\n[#565f89]{len(ctx.available_skills)} global skills available for injection[/]"),
            Horizontal(
                Button("◈  Preview Provision Plan", id="btn-preview-plan", classes="btn-primary"),
                Button("⇢  Go to Inject Skills", id="btn-goto-inject", classes="btn-ghost"),
            ),
        )

    # ── Inject Skills Tab ─────────────────────────────────────

    def _build_inject(self) -> ScrollableContainer:
        skills = self.vault.list_global_skills()
        skill_widgets: list = [
            Static("[bold #7dcfff]Select Skills to Inject[/]"),
            Static("[#565f89]Selected skills will be copied into the project skills dir.[/]\n"),
        ]
        if not skills:
            skill_widgets.append(Static("[#565f89]No global skills found. Create skills in the Skill Factory first.[/]"))
        else:
            for skill_path in sorted(skills):
                skill_widgets.append(Checkbox(f"  {skill_path.name}", id=f"inject-{skill_path.name}"))
            skill_widgets.append(Static(""))
            skill_widgets.append(Button("✓  Confirm Selection", id="btn-confirm-skills", classes="btn-success"))
        return ScrollableContainer(*skill_widgets, classes="panel")

    # ── Plugins Tab ────────────────────────────────────────────────

    def _build_plugins_tab(self) -> ScrollableContainer:
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
            cwd = Path(path_str).expanduser() if path_str else Path(os.getcwd())
        except Exception:
            cwd = Path(os.getcwd())
        installed = self.provisioner.get_installed_plugins(cwd, scope="project")
        installed_global = self.provisioner.get_installed_plugins(cwd, scope="global")

        CATEGORY_LABELS = {
            "workflow": "⚡ Workflow",
            "mcp":      "🔌 MCP",
            "auth":     "🔑 Auth",
            "memory":   "🧠 Memory",
            "ui":       "💻 UI",
            "notify":   "🔔 Notify",
            "general":  "◈ General",
        }

        proj_installed = len(installed)
        glob_installed = len(installed_global)

        widgets: list = [
            Static("[bold #7dcfff]OpenCode Plugin Catalogue[/]"),
            Static(
                "[#565f89]Plugins are added as MCP entries into [#9ece6a]opencode.json[/] — no code required.\n"
                f"[#bb9af7]+P[/] [#565f89]= install into project  [/][#7aa2f7]+G[/] [#565f89]= install globally[/]\n"
            ),
            Static(
                f"[#565f89]Project:[/]  [#c0caf5]{cwd}[/]  "
                f"[#9ece6a]{proj_installed} proj[/]  [#7aa2f7]{glob_installed} global[/]"
            ),
            Static(""),
        ]

        # Group plugins by category
        by_cat: dict[str, list] = {}
        for p in OPENCODE_PLUGINS:
            by_cat.setdefault(p.category, []).append(p)

        for cat, plugins in by_cat.items():
            widgets.append(Static(f"[bold #bb9af7]{CATEGORY_LABELS.get(cat, cat)}[/]"))
            for plugin in plugins:
                in_proj   = plugin.name in installed
                in_global = plugin.name in installed_global
                status = "[#9ece6a]✓ project[/]" if in_proj else (
                    "[#7aa2f7]✓ global[/]" if in_global else "[#565f89]not installed[/]"
                )
                widgets.append(Container(
                    Horizontal(
                        Static(f"[bold #c0caf5]{plugin.display}[/]  {status}", classes="plugin-name"),
                        Button("+P", id=f"plug-proj-{plugin.name}", classes="btn-ghost"),
                        Button("+G", id=f"plug-glob-{plugin.name}", classes="btn-ghost"),
                        Button("✕P", id=f"plug-rm-proj-{plugin.name}", classes="btn-danger") if in_proj else Static(""),
                        Button("✕G", id=f"plug-rm-glob-{plugin.name}", classes="btn-danger") if in_global else Static(""),
                    ),
                    Static(f"[#565f89]{plugin.description}[/]"),
                    Static(f"[#3b4261]{plugin.npm_install}[/]"),
                    classes="plugin-card",
                    id=f"plugin-card-{plugin.name.replace('@','').replace('/','_')}",
                ))

        return ScrollableContainer(*widgets, id="plugins-panel", classes="panel")

    # ── Context Architect ─────────────────────────────────────────

    def _build_architect_tab(self) -> ScrollableContainer:
        cwd = Path(os.getcwd())
        project_name = cwd.name or "my-project"
        stack_hint = "Unknown"
        if self._ctx and self._ctx.detected_stack:
            stack_hint = ", ".join(self._ctx.detected_stack)

        return ScrollableContainer(
            Static("[bold #7dcfff]AGENTS.md Context Architect[/]"),
            Static("[#565f89]Structured editor for AGENTS.md with preview before write.[/]\n"),
            Static("[#bb9af7]Project Name[/]"),
            Input(value=project_name, id="arch-project-name"),
            Static("[#bb9af7]Project Description[/]"),
            Input(placeholder="What does this project do?", id="arch-project-desc"),
            Horizontal(
                Container(
                    Static("[#bb9af7]Primary Language[/]"),
                    Input(value="Python", id="arch-language"),
                ),
                Container(
                    Static("[#bb9af7]Framework[/]"),
                    Input(value=stack_hint, id="arch-framework"),
                ),
            ),
            Horizontal(
                Container(
                    Static("[#bb9af7]Backend[/]"),
                    Input(placeholder="FastAPI / Node / Django", id="arch-backend"),
                ),
                Container(
                    Static("[#bb9af7]Database[/]"),
                    Input(placeholder="PostgreSQL / MongoDB", id="arch-database"),
                ),
            ),
            Static("[#bb9af7]Conventions (one per line)[/]"),
            TextArea(id="arch-conventions", text="Use type hints\nWrite tests for new behavior"),
            Static("[#bb9af7]Rules (one per line)[/]"),
            TextArea(id="arch-rules", text="Never commit secrets\nKeep changes focused and reviewable"),
            Static("[#bb9af7]Memory Bank Facts (one per line)[/]"),
            TextArea(id="arch-memory", text="Project uses .opencode/skills for local skills"),
            Static("[#bb9af7]Danger Zones (paths, one per line)[/]"),
            TextArea(id="arch-danger", text="migrations/\ninfra/production"),
            Horizontal(
                Button("Preview AGENTS.md", id="btn-arch-preview", classes="btn-primary"),
                Button("View Diff", id="btn-arch-diff", classes="btn-ghost"),
                Button("Write AGENTS.md", id="btn-arch-write", classes="btn-success"),
            ),
            Container(id="arch-preview-view"),
            classes="panel",
        )

    def _build_agents_from_architect(self, project_path: Path) -> str:
        def _value(input_id: str, default: str = "") -> str:
            try:
                return self.query_one(f"#{input_id}", Input).value.strip() or default
            except Exception:
                return default

        def _lines(area_id: str) -> list[str]:
            try:
                raw = self.query_one(f"#{area_id}", TextArea).text
            except Exception:
                raw = ""
            return [line.strip() for line in raw.splitlines() if line.strip()]

        name = _value("arch-project-name", project_path.name)
        desc = _value("arch-project-desc", "Project overview pending")
        language = _value("arch-language", "Unknown")
        framework = _value("arch-framework", "Unknown")
        backend = _value("arch-backend", "Unknown")
        database = _value("arch-database", "Unknown")

        conventions = _lines("arch-conventions")
        rules = _lines("arch-rules")
        memory = _lines("arch-memory")
        danger = _lines("arch-danger")
        conventions_md = "\n".join(f"- {x}" for x in conventions) or "- (none defined)"
        rules_md = "\n".join(f"- {x}" for x in rules) or "- (none defined)"
        memory_md = "\n".join(f"- {x}" for x in memory) or "- (none defined)"
        danger_md = "\n".join(f"- `{x}`" for x in danger) or "- (none defined)"

        stack = ", ".join(x for x in [language, framework, backend, database] if x and x != "Unknown") or "Unknown"

        return (
            "# AGENTS.md — Project Rules & Memory Bank\n"
            "# Generated by NEBULA-FORGE Context Architect\n\n"
            "## Project Identity\n\n"
            f"**Name:** {name}\n"
            f"**Path:** {project_path}\n"
            f"**Stack:** {stack}\n\n"
            "### Description\n"
            f"{desc}\n\n"
            "## Conventions\n"
            f"{conventions_md}\n\n"
            "## Rules\n"
            f"{rules_md}\n\n"
            "## Memory Bank\n"
            f"{memory_md}\n\n"
            "## Danger Zones\n"
            f"{danger_md}\n\n"
            "## Agent Instructions\n"
            "1. Read this file before planning edits\n"
            "2. Prefer project-local skills in `.opencode/skills/`\n"
            "3. Keep plans explicit and test-driven\n\n"
            "## Changelog\n"
            "| Date | Change | Author |\n"
            "|------|--------|--------|\n"
            f"| {datetime.now().strftime('%Y-%m-%d')} | Context Architect update | nebula-forge |\n"
        )

    def _preview_architect_agents(self) -> None:
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
        except Exception:
            path_str = str(Path(os.getcwd()))
        project_path = Path(path_str).expanduser()
        content = self._build_agents_from_architect(project_path)

        host = self.query_one("#arch-preview-view", Container)
        host.remove_children()
        host.mount(Static("\n[bold #7dcfff]AGENTS.md Preview[/]"))
        host.mount(Static(f"[#565f89]{(project_path / 'AGENTS.md')}[/]"))
        host.mount(Static(f"[#c0caf5]{content[:5000]}[/]"))

    def _diff_stats(self, before: str, after: str) -> tuple[int, int, int]:
        adds = dels = mods = 0
        for line in difflib.ndiff(before.splitlines(), after.splitlines()):
            if line.startswith("+ "):
                adds += 1
            elif line.startswith("- "):
                dels += 1
            elif line.startswith("? "):
                mods += 1
        return adds, dels, mods

    def _mount_side_by_side_diff(
        self,
        host: Container,
        *,
        target_path: Path,
        before: str,
        after: str,
        title: str,
    ) -> None:
        adds, dels, mods = self._diff_stats(before, after)

        before_text = before.strip() or "(file does not exist yet)"
        after_text = after.strip() or "(empty)"

        host.mount(Static(f"\n[bold #7dcfff]{title}[/]"))
        host.mount(Static(f"[#565f89]{target_path}[/]"))
        host.mount(Horizontal(
            Container(
                Static("[bold #bb9af7]BEFORE[/]"),
                Static(f"[#3b4261]{before_text[:3200]}[/]"),
                classes="panel",
            ),
            Container(
                Static("[bold #9ece6a]AFTER[/]"),
                Static(f"[#c0caf5]{after_text[:3200]}[/]"),
                classes="panel",
            ),
        ))
        host.mount(Static(
            f"[#565f89]+ {adds} additions  ·  - {dels} removals  ·  ~ {mods} modifications[/]"
        ))

    def _show_architect_diff(self, project_path: Path, content: str, *, with_confirm: bool) -> None:
        diff_view = self.query_one("#diff-view")
        diff_view.remove_children()

        target = project_path / "AGENTS.md"
        before = target.read_text(encoding="utf-8") if target.exists() else ""

        self._mount_side_by_side_diff(
            diff_view,
            target_path=target,
            before=before,
            after=content,
            title="GHOST DIFF — AGENTS.md",
        )

        if with_confirm:
            self._pending_agents_write_path = target
            self._pending_agents_write_content = content
            diff_view.mount(Horizontal(
                Button("✅ Confirm Write", id="btn-arch-confirm-write", classes="btn-success"),
                Button("← Back to Architect", id="btn-goto-architect", classes="btn-ghost"),
            ))

        try:
            self.query_one("#project-tabs", TabbedContent).active = "tab-diff"
        except Exception:
            pass

    def _write_architect_agents(self) -> None:
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
        except Exception:
            path_str = str(Path(os.getcwd()))
        project_path = Path(path_str).expanduser()
        if not project_path.exists() or not project_path.is_dir():
            self.app.notify(f"Invalid project path: {project_path}", severity="error")
            return

        content = self._build_agents_from_architect(project_path)
        self._show_architect_diff(project_path, content, with_confirm=True)
        self.app.notify("Review Ghost Diff, then confirm write.", severity="warning")

    def _confirm_write_architect_agents(self) -> None:
        target = self._pending_agents_write_path
        content = self._pending_agents_write_content
        if not target or content is None:
            self.app.notify("No pending AGENTS.md write to confirm", severity="warning")
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.app.notify(f"✓ Wrote AGENTS.md via Context Architect → {target}", severity="information")
        self._pending_agents_write_path = None
        self._pending_agents_write_content = None
        self._preview_architect_agents()

    # ── Events ────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid == "btn-scan":
            self._scan_project()
        elif bid == "btn-use-cwd":
            try:
                self.query_one("#project-path", Input).value = str(Path(os.getcwd()))
            except Exception:
                pass
        elif bid == "btn-preview-plan":
            self._preview_plan()
        elif bid == "btn-goto-inject":
            try:
                self.query_one("#project-tabs", TabbedContent).active = "tab-inject"
            except Exception:
                pass
        elif bid == "btn-confirm-skills":
            self._collect_skills()
        elif bid == "btn-bootstrap":
            self._execute_bootstrap()
        elif bid == "btn-goto-execute":
            try:
                self.query_one("#project-tabs", TabbedContent).active = "tab-execute"
            except Exception:
                pass
        elif bid.startswith("plug-proj-"):
            self._install_plugin(bid[len("plug-proj-"):], scope="project")
        elif bid.startswith("plug-glob-"):
            self._install_plugin(bid[len("plug-glob-"):], scope="global")
        elif bid.startswith("plug-rm-proj-"):
            self._remove_plugin(bid[len("plug-rm-proj-"):], scope="project")
        elif bid.startswith("plug-rm-glob-"):
            self._remove_plugin(bid[len("plug-rm-glob-"):], scope="global")
        elif bid == "btn-arch-preview":
            self._preview_architect_agents()
        elif bid == "btn-arch-diff":
            try:
                path_str = self.query_one("#project-path", Input).value.strip()
            except Exception:
                path_str = str(Path(os.getcwd()))
            project_path = Path(path_str).expanduser()
            self._show_architect_diff(project_path, self._build_agents_from_architect(project_path), with_confirm=False)
        elif bid == "btn-arch-write":
            self._write_architect_agents()
        elif bid == "btn-arch-confirm-write":
            self._confirm_write_architect_agents()
        elif bid == "btn-goto-architect":
            try:
                self.query_one("#project-tabs", TabbedContent).active = "tab-architect"
            except Exception:
                pass

    def _install_plugin(self, plugin_name: str, scope: str) -> None:
        plugin = next((p for p in OPENCODE_PLUGINS if p.name == plugin_name), None)
        if not plugin:
            self.app.notify(f"Plugin not found: {plugin_name}", severity="error")
            return
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
        except Exception:
            path_str = str(Path(os.getcwd()))
        cwd = Path(path_str).expanduser()
        ok, msg = self.provisioner.install_plugin_to_project(
            cwd, plugin_name, plugin.config_snippet, scope=scope
        )
        self.app.notify(msg, severity="information" if ok else "error")
        self._refresh_plugins_tab()

    def _remove_plugin(self, plugin_name: str, scope: str) -> None:
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
        except Exception:
            path_str = str(Path(os.getcwd()))
        cwd = Path(path_str).expanduser()
        ok, msg = self.provisioner.remove_plugin_from_project(cwd, plugin_name, scope=scope)
        self.app.notify(msg, severity="information" if ok else "error")
        self._refresh_plugins_tab()

    def _refresh_plugins_tab(self) -> None:
        try:
            panel = self.query_one("#plugins-panel")
            panel.remove()
        except Exception:
            pass
        try:
            tab = self.query_one("#tab-plugins")
            tab.mount(self._build_plugins_tab())
        except Exception:
            pass

    def _scan_project(self) -> None:
        try:
            path_str = self.query_one("#project-path", Input).value.strip()
        except Exception:
            path_str = str(Path(os.getcwd()))

        path = Path(path_str).expanduser()
        if not path.exists():
            self.app.notify(f"Path not found: {path}", severity="error")
            return

        self._ctx = self.provisioner.detect_project(path)
        results = self.query_one("#detect-results")
        results.remove_children()
        results.mount(self._build_detect_results(self._ctx))
        self.app.notify(f"✓ Scanned: {self._ctx.name}", severity="information")

    def _collect_skills(self) -> None:
        self._selected_skills = []
        for skill_path in self.vault.list_global_skills():
            name = skill_path.name
            try:
                cb = self.query_one(f"#inject-{name}", Checkbox)
                if cb.value:
                    self._selected_skills.append(name)
            except Exception:
                pass
        n = len(self._selected_skills)
        self.app.notify(f"✓ {n} skill{'s' if n != 1 else ''} selected for injection")

    def _preview_plan(self) -> None:
        if not self._ctx:
            self.app.notify("Scan a project first", severity="warning")
            return

        plan = self.provisioner.plan_project_bootstrap(self._ctx, self._selected_skills)
        diff_view = self.query_one("#diff-view")
        diff_view.remove_children()

        diff_view.mount(Static(f"[bold #7dcfff]Ghost Diff: {plan.title}[/]\n"))
        diff_view.mount(Static(f"[#565f89]{plan.description}[/]\n"))
        diff_view.mount(Static("[bold #7dcfff]Files & Directories:[/]"))

        for entry in plan.entries:
            p = Path(entry.path)
            if entry.action == "create":
                icon = "📁" if not p.suffix else "📄"
                color = "#9ece6a"
                tag = "CREATE"
            elif entry.action == "symlink":
                icon = "🔗"
                color = "#bb9af7"
                tag = "INJECT"
            else:
                icon = "✏"
                color = "#e0af68"
                tag = "MODIFY"

            diff_view.mount(Static(
                f"  [{color}]{icon} [{tag}][/] [#c0caf5]{p.name}[/]  "
                f"[#565f89]{entry.description or str(p.parent)[:50]}[/]"
            ))

        # Feature 12 foundation: side-by-side diffs for AGENTS.md and opencode.json
        for entry in plan.entries:
            p = Path(entry.path)
            if p.name not in ("AGENTS.md", "opencode.json"):
                continue
            before = p.read_text(encoding="utf-8") if p.exists() else ""
            self._mount_side_by_side_diff(
                diff_view,
                target_path=p,
                before=before,
                after=entry.content,
                title=f"GHOST DIFF — {p.name}",
            )

        diff_view.mount(Static(f"\n[#565f89]{plan.summary()}[/]"))
        diff_view.mount(Horizontal(
            Button("⚡  Bootstrap Project", id="btn-bootstrap", classes="btn-success"),
            Button("← Adjust", id="btn-goto-inject", classes="btn-ghost"),
        ))

        try:
            self.query_one("#project-tabs", TabbedContent).active = "tab-diff"
        except Exception:
            pass

    def _execute_bootstrap(self) -> None:
        if not self._ctx:
            self.app.notify("No project context. Scan first.", severity="error")
            return
        plan = self.provisioner.plan_project_bootstrap(self._ctx, self._selected_skills)
        self.run_bootstrap(plan)

    @work(exclusive=True)
    async def run_bootstrap(self, plan) -> None:
        try:
            self.query_one("#project-tabs", TabbedContent).active = "tab-execute"
        except Exception:
            pass

        exec_view = self.query_one("#execute-view")
        exec_view.remove_children()
        exec_view.mount(Static(f"[bold #7dcfff]Bootstrapping: {plan.title}[/]\n"))
        pb = ProgressBar(total=100, show_eta=False)
        exec_view.mount(pb)
        status = Static("[#565f89]Starting...[/]")
        exec_view.mount(status)
        log_area = ScrollableContainer()
        exec_view.mount(log_area)

        def on_progress(msg: str, pct: float) -> None:
            pb.progress = int(pct * 100)
            status.update(f"[#7aa2f7]{msg}[/]")
            log_area.mount(Static(f"  [#9ece6a]✓[/] [#565f89]{msg}[/]"))

        ok, msg = self.provisioner.execute_plan(plan, on_progress)
        await asyncio.sleep(0.2)

        if ok:
            pb.progress = 100
            status.update("[#9ece6a]✓ Bootstrap complete![/]")
            exec_view.mount(Static(
                f"\n[bold #9ece6a]Project {self._ctx.name} is ready![/]\n"
                f"[#565f89]AGENTS.md, opencode.json, and .opencode/ have been created.[/]"
            ))
            self.app.notify(f"✓ {self._ctx.name} bootstrapped!", severity="information")
        else:
            status.update(f"[#f7768e]✗ Bootstrap failed: {msg}[/]")
            self.app.notify("Bootstrap failed", severity="error")
