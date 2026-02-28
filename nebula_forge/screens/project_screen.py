"""
NEBULA-FORGE — Project Provisioner
Detect project, inject skills, bootstrap agent config.
"""

from __future__ import annotations
import os
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import (
    Button, Input, Label, Static, TabbedContent, TabPane,
    Checkbox, ProgressBar, Switch
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

    def compose(self) -> ComposeResult:
        yield Static("  ◈  PROJECT PROVISIONER", classes="section-title")
        with TabbedContent(id="project-tabs"):
            with TabPane("  Detect  ", id="tab-detect"):
                yield self._build_detect()
            with TabPane("  Inject Skills  ", id="tab-inject"):
                yield self._build_inject()
            with TabPane("  Plugins  ", id="tab-plugins"):
                yield self._build_plugins_tab()
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
            ("Git Repository",   ctx.has_git),
            ("CLAUDE.md",        ctx.has_claude_md),
            ("gemini.json",      ctx.has_gemini_json),
            ("Nebula Agents",    ctx.has_nebula_agents),
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

        widgets: list = [
            Static("[bold #7dcfff]OpenCode Plugin Catalogue[/]"),
            Static(
                "[#565f89]Install plugins into your project's [#9ece6a]opencode.json[/][#565f89] "
                "or the [#9ece6a]global[/][#565f89] ~/.config/opencode/opencode.json."
                " Plugins are added as MCP entries — no code required.[/]\n"
            ),
            Horizontal(
                Button("📁  Project: " + (cwd.name or "?"), id="btn-scope-project", classes="btn-primary"),
                Button("🌐  Global Config", id="btn-scope-global", classes="btn-ghost"),
                id="plugin-scope-bar",
            ),
            Static("", id="plugin-scope-label"),
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
                    Static(f"[#3b4261]cmd: {plugin.npm_install}[/]"),
                    Static(""),
                    classes="skill-card",
                    id=f"plugin-card-{plugin.name.replace('@','').replace('/','_')}",
                ))

        return ScrollableContainer(*widgets, id="plugins-panel", classes="panel")

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
                f"[#565f89]CLAUDE.md, gemini.json, and .nebula/ have been created.[/]"
            ))
            self.app.notify(f"✓ {self._ctx.name} bootstrapped!", severity="information")
        else:
            status.update(f"[#f7768e]✗ Bootstrap failed: {msg}[/]")
            self.app.notify("Bootstrap failed", severity="error")
