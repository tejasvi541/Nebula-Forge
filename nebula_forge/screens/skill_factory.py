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
from ..models import MarketplaceSkill, SkillMetadata
from ..marketplace import SkillMarketplace
from ..skill_scorer import score_skill
from ..sync import ForgeSync
from ..cookbook import COOKBOOK_ENTRIES, SkillCookbookEntry, search_cookbook

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
        self._marketplace = SkillMarketplace(vault)
        self._sync = ForgeSync(vault)
        self._market_index: list[MarketplaceSkill] = []
        self._market_lookup: dict[str, MarketplaceSkill] = {}
        self._composer_preview_md: str = ""
        self._cookbook_lookup: dict[str, SkillCookbookEntry] = {e.id: e for e in COOKBOOK_ENTRIES}

    def compose(self) -> ComposeResult:
        yield Static("  ◈  GLOBAL SKILL FACTORY", classes="section-title")
        with TabbedContent(id="skill-tabs"):
            with TabPane("  Registry  ", id="tab-registry"):
                yield self._build_registry()
            with TabPane("  Create Skill  ", id="tab-create"):
                yield self._build_create_form()
            with TabPane("  Preview  ", id="tab-preview"):
                yield self._build_preview_tab()
            with TabPane("  Composer  ", id="tab-composer"):
                yield self._build_composer_tab()
            with TabPane("  Marketplace  ", id="tab-marketplace"):
                yield self._build_marketplace_tab()
            with TabPane("  Cookbook  ", id="tab-cookbook"):
                yield self._build_cookbook_tab()
            with TabPane("  Forge Sync  ", id="tab-sync"):
                yield self._build_sync_tab()

    def on_mount(self) -> None:
        self.run_refresh_marketplace()
        self._refresh_composer_preview()
        self._render_cookbook_results()
        self._refresh_sync_status()

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

    def _build_marketplace_tab(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Skill Marketplace[/]"),
            Static(
                "[#565f89]Browse community skills. Install to global or local scope.[/]\n"
                "[#3b4261]Source: skills.nebula-forge.dev (falls back to local cache).[/]"
            ),
            Horizontal(
                Input(placeholder="Search skills, tags, author...", id="market-query"),
                Button("Search", id="btn-market-search", classes="btn-ghost"),
                Button("Refresh", id="btn-market-refresh", classes="btn-primary"),
            ),
            Container(id="market-status"),
            Container(id="market-results"),
            classes="panel",
        )

    def _build_composer_tab(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Skill Composer[/]"),
            Static("[#565f89]Build SKILL.md with live preview and quality score.[/]\n"),
            Static("[#bb9af7]Name[/]"),
            Input(value="", placeholder="code-reviewer", id="comp-name"),
            Horizontal(
                Container(
                    Static("[#bb9af7]Category[/]"),
                    Input(value="general", id="comp-category"),
                ),
                Container(
                    Static("[#bb9af7]Model[/]"),
                    Input(value="copilot/claude-opus-4-6", id="comp-model"),
                ),
            ),
            Static("[#bb9af7]Description[/]"),
            Input(value="", placeholder="What this skill does", id="comp-description"),
            Static("[#bb9af7]Tags (comma-separated)[/]"),
            Input(value="", placeholder="review, security", id="comp-tags"),
            Static("[#bb9af7]Trigger Description[/]"),
            TextArea(id="comp-trigger", text="Use when user asks for this specialized task."),
            Static("[#bb9af7]Instructions[/]"),
            TextArea(id="comp-instructions", text="1. Analyze context\n2. Propose plan\n3. Execute safely"),
            Static("[#bb9af7]Output Format[/]"),
            TextArea(id="comp-output", text="Return sections: Summary, Steps, Risks, Final Output"),
            Static("[#bb9af7]Scope[/]"),
            Select(options=[("Global", "global"), ("Local (CWD)", "local")], value="global", id="comp-scope"),
            Horizontal(
                Button("Refresh Preview", id="btn-comp-refresh", classes="btn-ghost"),
                Button("Save Skill", id="btn-comp-save", classes="btn-success"),
            ),
            Container(id="comp-score"),
            Container(id="comp-preview"),
            classes="panel",
        )

    def _build_sync_tab(self) -> ScrollableContainer:
        cfg = self.vault.load()
        return ScrollableContainer(
            Static("[bold #7dcfff]Forge Sync[/]"),
            Static(
                "[#565f89]Sync global skills with your shared team registry (git).[/]\n"
                "[#3b4261]Repository layout: skills/<skill-name>/SKILL.md[/]"
            ),
            Static("[#bb9af7]Repository URL[/]"),
            Input(
                value=cfg.sync_repo_url or "",
                placeholder="git@github.com:org/nebula-skills.git",
                id="sync-repo-url",
            ),
            Horizontal(
                Container(
                    Static("[#bb9af7]Branch[/]"),
                    Input(value=cfg.sync_branch or "main", id="sync-branch"),
                ),
                Container(
                    Static("[#bb9af7]Auto Sync[/]"),
                    Select(
                        options=[("Off", "off"), ("On", "on")],
                        value="on" if cfg.sync_auto else "off",
                        id="sync-auto",
                    ),
                ),
            ),
            Horizontal(
                Button("Save Config", id="btn-sync-save", classes="btn-ghost"),
                Button("Pull", id="btn-sync-pull", classes="btn-primary"),
                Button("Push", id="btn-sync-push", classes="btn-success"),
                Button("Refresh", id="btn-sync-refresh", classes="btn-ghost"),
            ),
            Container(id="sync-status"),
            classes="panel",
        )

    def _build_cookbook_tab(self) -> ScrollableContainer:
        return ScrollableContainer(
            Static("[bold #7dcfff]Skills Cookbook[/]"),
            Static(
                "[#565f89]Curated skills from PRDv2 with one-click install and composer preload.[/]\n"
                "[#3b4261]Great starting points for team-standard skill quality.[/]"
            ),
            Horizontal(
                Input(placeholder="Search cookbook examples...", id="cookbook-query"),
                Button("Search", id="btn-cookbook-search", classes="btn-ghost"),
                Button("Refresh", id="btn-cookbook-refresh", classes="btn-primary"),
            ),
            Container(id="cookbook-results"),
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

        elif bid == "btn-market-refresh":
            self.run_refresh_marketplace()

        elif bid == "btn-market-search":
            self._render_marketplace_results()

        elif bid.startswith("market-install-global-"):
            skill_id = bid[len("market-install-global-"):]
            self._install_market_skill(skill_id, "global")

        elif bid.startswith("market-install-local-"):
            skill_id = bid[len("market-install-local-"):]
            self._install_market_skill(skill_id, "local")

        elif bid == "btn-comp-refresh":
            self._refresh_composer_preview()

        elif bid == "btn-comp-save":
            self._save_from_composer()

        elif bid == "btn-sync-save":
            self._save_sync_config()

        elif bid == "btn-sync-pull":
            self.run_sync_pull()

        elif bid == "btn-sync-push":
            self.run_sync_push()

        elif bid == "btn-sync-refresh":
            self._refresh_sync_status()

        elif bid == "btn-cookbook-search":
            self._render_cookbook_results()

        elif bid == "btn-cookbook-refresh":
            self._render_cookbook_results()

        elif bid.startswith("cookbook-install-global-"):
            cid = bid[len("cookbook-install-global-"):]
            self._install_cookbook_skill(cid, "global")

        elif bid.startswith("cookbook-install-local-"):
            cid = bid[len("cookbook-install-local-"):]
            self._install_cookbook_skill(cid, "local")

        elif bid.startswith("cookbook-load-"):
            cid = bid[len("cookbook-load-"):]
            self._load_cookbook_into_composer(cid)

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

    @work(exclusive=True)
    async def run_refresh_marketplace(self) -> None:
        try:
            status = self.query_one("#market-status", Container)
            status.remove_children()
            status.mount(Static("[#7aa2f7]Fetching marketplace index...[/]"))
        except Exception:
            pass

        await asyncio.sleep(0.05)
        self._market_index = self._marketplace.fetch_index()
        self._market_lookup = {s.id: s for s in self._market_index}

        try:
            status = self.query_one("#market-status", Container)
            status.remove_children()
            status.mount(Static(f"[#565f89]{len(self._market_index)} skill(s) loaded[/]"))
        except Exception:
            pass

        self._render_marketplace_results()

    def _render_marketplace_results(self) -> None:
        try:
            query = self.query_one("#market-query", Input).value.strip()
            results = self._marketplace.search(query)
            host = self.query_one("#market-results", Container)
            host.remove_children()

            if not results:
                host.mount(Static("[#565f89]No skills found for this query.[/]"))
                return

            for skill in results:
                verified = " [#9ece6a]✓ verified[/]" if skill.verified else ""
                tags = ", ".join(skill.tags[:4]) if skill.tags else "general"
                host.mount(Container(
                    Horizontal(
                        Static(f"[bold #c0caf5]{skill.name}[/]"),
                        Static(f"[#bb9af7]{skill.author}[/]  [#e0af68]★ {skill.stars:.1f}[/]  [#7dcfff]↓ {skill.downloads}[/]{verified}"),
                    ),
                    Static(f"[#565f89]{skill.description}[/]"),
                    Static(f"[#3b4261]tags: {tags}  ·  category: {skill.category}[/]"),
                    Horizontal(
                        Button("Install Global", id=f"market-install-global-{skill.id}", classes="btn-ghost"),
                        Button("Install Local", id=f"market-install-local-{skill.id}", classes="btn-primary"),
                    ),
                    classes="plugin-card",
                ))
        except Exception as e:
            self.app.notify(f"Marketplace render error: {e}", severity="error")

    def _install_market_skill(self, skill_id: str, scope: str) -> None:
        skill = self._market_lookup.get(skill_id)
        if not skill:
            self.app.notify("Skill not found in marketplace index", severity="error")
            return

        cwd = Path(os.getcwd())
        ok, msg = self._marketplace.install(skill, scope, cwd)
        if ok:
            if scope == "global":
                target = self.vault.skills_dir / skill.name
            else:
                target = self.vault.project_skills_dir(cwd) / skill.name
            self.app.notify(f"✓ {msg} → {target}", severity="information")
        else:
            self.app.notify(f"Install failed: {msg}", severity="error")

    def on_input_changed(self, event: Input.Changed) -> None:
        iid = event.input.id or ""
        if iid.startswith("comp-"):
            self._refresh_composer_preview()
        elif iid == "cookbook-query":
            self._render_cookbook_results()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if (event.text_area.id or "").startswith("comp-"):
            self._refresh_composer_preview()

    def _composer_value(self, widget_id: str, default: str = "") -> str:
        try:
            return self.query_one(f"#{widget_id}", Input).value.strip() or default
        except Exception:
            return default

    def _composer_text(self, widget_id: str, default: str = "") -> str:
        try:
            text = self.query_one(f"#{widget_id}", TextArea).text
            return text.strip() or default
        except Exception:
            return default

    def _refresh_composer_preview(self) -> None:
        name = self._composer_value("comp-name", "new-skill")
        category = self._composer_value("comp-category", "general")
        model = self._composer_value("comp-model", "copilot/claude-opus-4-6")
        description = self._composer_value("comp-description", "No description")
        tags_raw = self._composer_value("comp-tags", "general")
        trigger = self._composer_text("comp-trigger", "")
        instructions = self._composer_text("comp-instructions", "")
        output = self._composer_text("comp-output", "")

        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        frontmatter = {
            "name": name,
            "category": category,
            "model_preference": model,
            "description": description,
            "tags": ", ".join(tags) if tags else "general",
        }

        score = score_skill(frontmatter, instructions, trigger, output)

        self._composer_preview_md = "\n".join([
            "---",
            f"name: {name}",
            f"category: {category}",
            "version: 1.0.0",
            "author: nebula-forge",
            f"model_preference: {model}",
            "thinking_mode: auto",
            f"tags: {', '.join(tags) if tags else 'general'}",
            "description: >",
            f"  {description}",
            "---",
            "",
            f"# Skill: {name}",
            "",
            "## Purpose",
            description,
            "",
            "## When to Use This Skill",
            trigger,
            "",
            "## Instructions",
            instructions,
            "",
            "## Output Format",
            output,
            "",
            "## Examples",
            "### Input",
            "```",
            "<!-- Example input -->",
            "```",
            "",
            "### Output",
            "```",
            "<!-- Example output -->",
            "```",
        ])

        try:
            score_host = self.query_one("#comp-score", Container)
            score_host.remove_children()
            score_host.mount(Static(
                f"\n[bold #7dcfff]Quality Score[/]  [#9ece6a]{score.total}/100[/]"
            ))
            if score.suggestions:
                score_host.mount(Static("[#565f89]Suggestions:[/]"))
                for s in score.suggestions[:5]:
                    score_host.mount(Static(f"[#e0af68]•[/] [#565f89]{s}[/]"))

            preview_host = self.query_one("#comp-preview", Container)
            preview_host.remove_children()
            preview_host.mount(Static("\n[bold #7dcfff]Preview[/]"))
            preview_host.mount(Static(f"[#c0caf5]{self._composer_preview_md[:5000]}[/]"))
        except Exception:
            pass

    def _save_from_composer(self) -> None:
        self._refresh_composer_preview()

        name = self._composer_value("comp-name", "")
        description = self._composer_value("comp-description", "")
        category = self._composer_value("comp-category", "general")
        model = self._composer_value("comp-model", "copilot/claude-opus-4-6")
        tags_raw = self._composer_value("comp-tags", "general")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not name or not description:
            self.app.notify("Composer requires name and description", severity="error")
            return

        scope_sel = self.query_one("#comp-scope", Select)
        scope = str(scope_sel.value) if scope_sel.value != Select.BLANK else "global"
        if scope == "local":
            target_dir: Path | None = Path(os.getcwd()) / self.vault.load().project_skills_subdir
        else:
            target_dir = None

        meta = SkillMetadata(
            name=name,
            category=category,
            model_preference=model,
            description=description,
            tags=tags,
            author="nebula-forge",
        )

        plan = self.provisioner.plan_skill_creation(meta, target_dir=target_dir)
        # overwrite default template with composer preview content
        for entry in plan.entries:
            if Path(entry.path).name == "SKILL.md":
                entry.content = self._composer_preview_md
                entry.description = "SKILL.md generated by Composer"

        ok = self.provisioner.execute_skill_creation(plan)
        if ok:
            self.app.notify(f"✓ Skill '{name}' saved from Composer", severity="information")
        else:
            self.app.notify("Failed to save composed skill", severity="error")

    def _render_cookbook_results(self) -> None:
        try:
            query = self.query_one("#cookbook-query", Input).value.strip()
            host = self.query_one("#cookbook-results", Container)
            host.remove_children()

            results = search_cookbook(query)
            if not results:
                host.mount(Static("[#565f89]No cookbook entries matched your query.[/]"))
                return

            host.mount(Static(f"[#565f89]{len(results)} cookbook skill(s)[/]"))
            for entry in results:
                tags = ", ".join(entry.tags[:5]) if entry.tags else "general"
                host.mount(Container(
                    Horizontal(
                        Static(f"[bold #c0caf5]{entry.title}[/]  [#bb9af7]{entry.name}[/]"),
                        Static(f"[#7aa2f7]{entry.category}[/]  [#9ece6a]{entry.model_preference.split('/')[-1]}[/]"),
                    ),
                    Static(f"[#565f89]{entry.description}[/]"),
                    Static(f"[#3b4261]tags: {tags}[/]"),
                    Horizontal(
                        Button("Load into Composer", id=f"cookbook-load-{entry.id}", classes="btn-ghost"),
                        Button("Install Global", id=f"cookbook-install-global-{entry.id}", classes="btn-ghost"),
                        Button("Install Local", id=f"cookbook-install-local-{entry.id}", classes="btn-primary"),
                    ),
                    classes="plugin-card",
                ))
        except Exception as e:
            self.app.notify(f"Cookbook render error: {e}", severity="error")

    def _install_cookbook_skill(self, cookbook_id: str, scope: str) -> None:
        entry = self._cookbook_lookup.get(cookbook_id)
        if not entry:
            self.app.notify("Cookbook entry not found", severity="error")
            return

        if scope == "local":
            target_root = self.vault.project_skills_dir(Path(os.getcwd()))
        else:
            target_root = self.vault.skills_dir
        target = target_root / entry.name

        if target.exists():
            self.app.notify(f"Skill already exists: {target}", severity="warning")
            return

        try:
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text(entry.markdown, encoding="utf-8")
            self.app.notify(f"✓ Installed cookbook skill '{entry.name}' → {target}", severity="information")
        except Exception as e:
            self.app.notify(f"Cookbook install failed: {e}", severity="error")

    def _load_cookbook_into_composer(self, cookbook_id: str) -> None:
        entry = self._cookbook_lookup.get(cookbook_id)
        if not entry:
            self.app.notify("Cookbook entry not found", severity="error")
            return

        try:
            self.query_one("#comp-name", Input).value = entry.name
            self.query_one("#comp-category", Input).value = entry.category
            self.query_one("#comp-model", Input).value = entry.model_preference
            self.query_one("#comp-description", Input).value = entry.description
            self.query_one("#comp-tags", Input).value = ", ".join(entry.tags)
            self.query_one("#comp-trigger", TextArea).text = "Use when this workflow appears in user request."
            self.query_one("#comp-instructions", TextArea).text = (
                "1. Analyze context\n2. Apply cookbook conventions\n"
                "3. Return actionable, structured output"
            )
            self.query_one("#comp-output", TextArea).text = "Sections: Summary, Actions, Risks, Next Steps"
            self._refresh_composer_preview()

            tabs = self.query_one("#skill-tabs", TabbedContent)
            tabs.active = "tab-composer"
            self.app.notify(f"✓ Loaded '{entry.name}' into Composer", severity="information")
        except Exception as e:
            self.app.notify(f"Could not load into Composer: {e}", severity="error")

    def _save_sync_config(self) -> None:
        try:
            repo = self.query_one("#sync-repo-url", Input).value.strip()
            branch = self.query_one("#sync-branch", Input).value.strip() or "main"
            auto_sel = self.query_one("#sync-auto", Select)
            auto_value = str(auto_sel.value) if auto_sel.value != Select.BLANK else "off"
            auto = auto_value == "on"
        except Exception as e:
            self.app.notify(f"Sync form error: {e}", severity="error")
            return

        ok, msg = self._sync.configure(repo, branch, auto)
        if ok:
            self.app.notify(f"✓ {msg}", severity="information")
            self._refresh_sync_status()
        else:
            self.app.notify(msg, severity="error")

    def _fmt_time(self, value: str) -> str:
        if not value or value == "never":
            return "never"
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return value

    def _refresh_sync_status(self) -> None:
        try:
            host = self.query_one("#sync-status", Container)
            host.remove_children()
            st = self._sync.status()

            conn = "[#9ece6a]connected[/]" if st.connected else "[#f7768e]not connected[/]"
            configured = "[#9ece6a]yes[/]" if st.configured else "[#f7768e]no[/]"

            host.mount(Static("\n[bold #7dcfff]Sync Status[/]"))
            host.mount(Static(f"[#565f89]Configured:[/] {configured}  ·  [#565f89]Git:[/] {conn}"))
            host.mount(Static(f"[#565f89]Repo:[/] {st.repo_url or '—'}"))
            host.mount(Static(f"[#565f89]Branch:[/] {st.branch}  ·  [#565f89]Auto:[/] {'on' if st.auto else 'off'}"))
            host.mount(Static(f"[#565f89]Skills:[/] local {st.local_skills}  ·  remote {st.remote_skills}"))
            host.mount(Static(f"[#565f89]Last pull:[/] {self._fmt_time(st.last_pull)}"))
            host.mount(Static(f"[#565f89]Last push:[/] {self._fmt_time(st.last_push)}"))
        except Exception:
            pass

    @work(exclusive=True)
    async def run_sync_pull(self) -> None:
        self._refresh_sync_status()
        ok, msg = await asyncio.to_thread(self._sync.pull)
        if ok:
            self.app.notify(f"✓ {msg}", severity="information")
        else:
            self.app.notify(f"Pull failed: {msg}", severity="error")
        self._refresh_sync_status()

    @work(exclusive=True)
    async def run_sync_push(self) -> None:
        self._refresh_sync_status()
        ok, msg = await asyncio.to_thread(self._sync.push)
        if ok:
            self.app.notify(f"✓ {msg}", severity="information")
        else:
            self.app.notify(f"Push failed: {msg}", severity="error")
        self._refresh_sync_status()
