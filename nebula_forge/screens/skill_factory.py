"""
NEBULA-FORGE — Skill Factory
Browse, create, and manage global skills.
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import (
    Button, Input, Label, Static, TextArea,
    TabbedContent, TabPane, DataTable, Select, ProgressBar
)
from textual.containers import (
    Vertical, Horizontal, Container, ScrollableContainer, Grid
)
from textual.reactive import reactive
from textual import work
import asyncio

from ..vault import Vault
from ..provisioner import Provisioner
from ..models import SkillMetadata

CATEGORIES = [
    ("Code Generation", "code-gen"),
    ("Code Review", "code-review"),
    ("Testing", "testing"),
    ("Documentation", "docs"),
    ("DevOps", "devops"),
    ("Security", "security"),
    ("Architecture", "architecture"),
    ("Performance", "performance"),
    ("Data", "data"),
    ("General", "general"),
]

MODELS = [
    ("copilot/claude-opus-4-6", "copilot/claude-opus-4-6"),
    ("copilot/gpt-5.1-codex-max", "copilot/gpt-5.1-codex-max"),
    ("copilot/gemini-3.1-pro-preview", "copilot/gemini-3.1-pro-preview"),
    ("nvidia/devstral-2-123b-instruct-2512", "nvidia/devstral-2-123b-instruct-2512"),
    ("opencodezen/minimax-m2-5", "opencodezen/minimax-m2-5"),
    ("copilot/claude-sonnet-4-5", "copilot/claude-sonnet-4-5"),
]


class SkillFactoryScreen(Container):
    """Global Skill Factory — Registry, creation, copy to project."""

    view: reactive[str] = reactive("registry")

    def __init__(self, vault: Vault, provisioner: Provisioner) -> None:
        super().__init__()
        self.vault = vault
        self.provisioner = provisioner
        self._selected_skill: str | None = None
        self._skill_scope: str = "global"  # "global" | "local"

    def compose(self) -> ComposeResult:
        yield Static("  ◈  GLOBAL SKILL FACTORY", classes="section-title")
        with TabbedContent(id="skill-tabs"):
            with TabPane("  Registry  ", id="tab-registry"):
                yield self._build_registry()
            with TabPane("  Create Skill  ", id="tab-create"):
                yield self._build_create_form()
            with TabPane("  Preview  ", id="tab-preview"):
                yield self._build_preview_tab()

    # ── Registry ──────────────────────────────────────────────

    def _build_registry(self) -> ScrollableContainer:
        skills = self.vault.list_global_skills()

        header = Horizontal(
            Static(f"[bold #7dcfff]{len(skills)} skills registered[/]  "
                   f"[#565f89]in {self.vault.skills_dir}[/]"),
            Button("＋ Create New Skill", id="btn-goto-create", classes="btn-primary"),
            id="registry-header",
        )

        if not skills:
            return ScrollableContainer(
                header,
                Static(
                    f"\n[#565f89]No skills yet. Click '＋ Create New Skill' to add your first skill.[/]\n\n"
                    f"[#3b4261]Skills are stored in {self.vault.skills_dir}/[skill-name]/SKILL.md\n"
                    "They can be injected into any project context.[/]"
                ),
                classes="panel",
            )
        else:
            return ScrollableContainer(
                header,
                *[self._make_skill_card(p) for p in sorted(skills)],
                classes="panel",
            )

    def _make_skill_card(self, skill_path: Path) -> Container:
        skill_md = skill_path / "SKILL.md"
        name = skill_path.name
        category = "general"
        model = "—"
        desc = "No description"

        if skill_md.exists():
            try:
                content = skill_md.read_text()
                for line in content.split("\n"):
                    if line.startswith("category:"):
                        category = line.split(":", 1)[1].strip()
                    elif line.startswith("model_preference:"):
                        model = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        if desc.startswith(">"):
                            desc = desc[1:].strip()
            except Exception:
                pass

        return Container(
            Horizontal(
                Static(f"[bold #7dcfff]◈  {name}[/]", classes="skill-name"),
                Static(f"[#bb9af7]{category}[/]", classes="skill-category"),
            ),
            Static(f"[#9ece6a]⊕  {model}[/]", classes="skill-model"),
            Static(
                f"[#565f89]{desc[:80]}...[/]" if len(desc) > 80 else f"[#565f89]{desc}[/]",
                classes="skill-desc",
            ),
            Horizontal(
                Button("👁 Preview", id=f"preview-{name}", classes="btn-ghost"),
                Button("📋 Copy to Project", id=f"copy-{name}", classes="btn-ghost"),
                Button("🗑 Delete", id=f"delete-{name}", classes="btn-danger"),
            ),
            classes="skill-card",
            id=f"card-{name}",
        )

    # ── Create Form ───────────────────────────────────────────

    def _build_create_form(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Zero-Touch Skill Provision[/]"),
            Static("[#565f89]Fill out the form and hit Create — NEBULA-FORGE does the rest.[/]\n"),
            Static("[#bb9af7]Skill Name  [#565f89](kebab-case, e.g. code-review-senior)[/][/]"),
            Input(placeholder="my-skill-name", id="skill-name"),
            Static("[#bb9af7]Category[/]"),
            Select(options=CATEGORIES, value="general", id="skill-category"),
            Static("[#bb9af7]Model Preference[/]"),
            Select(options=MODELS, value="copilot/claude-opus-4-6", id="skill-model"),
            Static("[#bb9af7]Description  [#565f89](one clear sentence)[/][/]"),
            Input(placeholder="What does this skill do?", id="skill-desc"),
            Static("[#bb9af7]Tags  [#565f89](comma-separated)[/][/]"),
            Input(placeholder="code, review, typescript", id="skill-tags"),
            Static("[#bb9af7]Author[/]"),
            Input(placeholder="your-name", id="skill-author", value="nebula-forge"),
            Static("\n[bold #7dcfff]Skill Scope[/]"),
            Static(
                "[#565f89]Global → ~/.config/opencode/skills/  (shared across all projects)\n"
                "Local  → <cwd>/.opencode/skills/  (only for the project where you launched nf)[/]"
            ),
            Horizontal(
                Button("🌐  Global", id="btn-scope-global-skill", classes="btn-primary"),
                Button("📁  Local (CWD)", id="btn-scope-local-skill", classes="btn-ghost"),
                id="skill-scope-bar",
            ),
            Static("", id="skill-scope-label"),
            Static(""),
            Horizontal(
                Button("⚡ Create Skill", id="btn-create-skill", classes="btn-primary"),
                Button("Reset", id="btn-reset-form", classes="btn-ghost"),
            ),
            Container(id="create-progress-area"),
            classes="panel",
        )

    def _build_preview_tab(self) -> Container:
        if self._selected_skill:
            skill_path = self.vault.skills_dir / self._selected_skill
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text()[:3000]
                return Container(
                    Static(f"[bold #7dcfff]Preview: {self._selected_skill}[/]\n"),
                    Static(f"[#565f89]{skill_path}[/]\n"),
                    Static(f"[#c0caf5]{content}[/]", classes="panel"),
                    classes="panel",
                )
            return Container(
                Static("[#f7768e]Skill file not found.[/]"),
                classes="panel",
            )
        return Container(
            Static("[#565f89]Select a skill from the Registry tab to preview it here.[/]"),
            classes="panel",
        )

    # ── Events ────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""

        if bid == "btn-goto-create":
            try:
                tabs = self.query_one("#skill-tabs", TabbedContent)
                tabs.active = "tab-create"
            except Exception:
                pass

        elif bid == "btn-create-skill":
            self._create_skill()

        elif bid == "btn-reset-form":
            for fid in ("skill-name", "skill-desc", "skill-tags", "skill-author"):
                try:
                    self.query_one(f"#{fid}", Input).value = ""
                except Exception:
                    pass

        elif bid == "btn-scope-global-skill":
            self._skill_scope = "global"
            try:
                self.query_one("#btn-scope-global-skill", Button).add_class("btn-primary")
                self.query_one("#btn-scope-global-skill", Button).remove_class("btn-ghost")
                self.query_one("#btn-scope-local-skill", Button).remove_class("btn-primary")
                self.query_one("#btn-scope-local-skill", Button).add_class("btn-ghost")
                self.query_one("#skill-scope-label", Static).update(
                    f"[#565f89]→ {self.vault.skills_dir}[/]"
                )
            except Exception:
                pass

        elif bid == "btn-scope-local-skill":
            self._skill_scope = "local"
            try:
                self.query_one("#btn-scope-local-skill", Button).add_class("btn-primary")
                self.query_one("#btn-scope-local-skill", Button).remove_class("btn-ghost")
                self.query_one("#btn-scope-global-skill", Button).remove_class("btn-primary")
                self.query_one("#btn-scope-global-skill", Button).add_class("btn-ghost")
                cwd = Path(os.getcwd())
                subdir = self.vault.load().project_skills_subdir
                self.query_one("#skill-scope-label", Static).update(
                    f"[#565f89]→ {cwd / subdir}[/]"
                )
            except Exception:
                pass

        elif bid.startswith("preview-"):
            self._selected_skill = bid[8:]
            self._refresh_preview()

        elif bid.startswith("copy-"):
            skill_name = bid[5:]
            self._copy_to_project(skill_name)

        elif bid.startswith("delete-"):
            skill_name = bid[7:]
            self._delete_skill(skill_name)

    def _create_skill(self) -> None:
        try:
            name = self.query_one("#skill-name", Input).value.strip()
            desc = self.query_one("#skill-desc", Input).value.strip()
            tags_raw = self.query_one("#skill-tags", Input).value.strip()
            author = self.query_one("#skill-author", Input).value.strip()

            cat_sel = self.query_one("#skill-category", Select)
            cat = str(cat_sel.value) if cat_sel.value != Select.BLANK else "general"

            mod_sel = self.query_one("#skill-model", Select)
            model = str(mod_sel.value) if mod_sel.value != Select.BLANK else "copilot/claude-opus-4-6"
        except Exception as e:
            self.app.notify(f"Form error: {e}", severity="error")
            return

        if not name:
            self.app.notify("Skill name is required", severity="error")
            return
        if not desc:
            self.app.notify("Description is required", severity="error")
            return

        if self.vault.skill_exists(name):
            self.app.notify(f"Skill '{name}' already exists", severity="warning")
            return

        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        meta = SkillMetadata(
            name=name,
            category=cat,
            model_preference=model,
            description=desc,
            tags=tags,
            author=author or "nebula-forge",
        )

        if self._skill_scope == "local":
            cwd = Path(os.getcwd())
            subdir = self.vault.load().project_skills_subdir
            target_dir: Path | None = cwd / subdir
        else:
            target_dir = None  # uses vault.skills_dir (global)
        self.run_provision_skill(meta, target_dir)

    @work(exclusive=True)
    async def run_provision_skill(self, meta: SkillMetadata, target_dir: Path | None = None) -> None:
        area = self.query_one("#create-progress-area")
        area.remove_children()
        area.mount(Static(f"\n[#7dcfff]Provisioning skill: {meta.name}[/]"))
        pb = ProgressBar(total=100, show_eta=False)
        area.mount(pb)
        status = Static("[#565f89]Starting...[/]")
        area.mount(status)

        plan = self.provisioner.plan_skill_creation(meta, target_dir=target_dir)

        # Show ghost diff
        area.mount(Static("\n[bold #7dcfff]Ghost Preview — Files to Create:[/]"))
        for entry in plan.entries:
            icon = "📁" if not Path(entry.path).suffix else "📄"
            area.mount(Static(f"  [#9ece6a]{icon} {Path(entry.path).name}[/]  [#565f89]{entry.description}[/]"))

        await asyncio.sleep(0.5)
        status.update("[#7aa2f7]Writing files...[/]")

        def on_progress(msg: str, pct: float) -> None:
            pb.progress = int(pct * 100)
            status.update(f"[#7aa2f7]{msg}[/]")

        success = self.provisioner.execute_skill_creation(plan, on_progress)
        await asyncio.sleep(0.3)

        if success:
            pb.progress = 100
            dest = str(target_dir) if target_dir else str(self.vault.skills_dir)
            status.update(f"[#9ece6a]✓ Skill '{meta.name}' created at {dest}/{meta.name}[/]")
            self.app.notify(f"✓ Skill '{meta.name}' provisioned!", severity="information")
        else:
            status.update("[#f7768e]✗ Provisioning failed.[/]")
            self.app.notify("Skill creation failed", severity="error")

    def _refresh_preview(self) -> None:
        try:
            tabs = self.query_one("#skill-tabs", TabbedContent)
            tab = tabs.query_one("#tab-preview")
            tab.remove_children()
            tab.mount(self._build_preview_tab())
            tabs.active = "tab-preview"
        except Exception:
            pass

    def _copy_to_project(self, skill_name: str) -> None:
        cwd = Path(os.getcwd())
        plan = self.provisioner.copy_skill_to_project(skill_name, cwd)
        ok, msg = self.provisioner.execute_plan(plan)
        if ok:
            subdir = self.vault.load().project_skills_subdir
            self.app.notify(f"✓ '{skill_name}' → {cwd.name}/{subdir}/", severity="information")
        else:
            self.app.notify(f"Copy failed: {msg}", severity="error")

    def _delete_skill(self, skill_name: str) -> None:
        import shutil
        skill_path = self.vault.skills_dir / skill_name
        try:
            shutil.rmtree(skill_path)
            self.app.notify(f"✓ Skill '{skill_name}' deleted", severity="information")
        except Exception as e:
            self.app.notify(f"Delete failed: {e}", severity="error")
