"""
NEBULA-FORGE — Data Models
All configuration and state managed via Pydantic for strict validation.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class APIKeys(BaseModel):
    google_ai: Optional[str] = None
    anthropic: Optional[str] = None
    github_copilot: Optional[str] = None
    nvidia: Optional[str] = None
    opencode_zen: Optional[str] = None
    custom_endpoints: Dict[str, str] = Field(default_factory=dict)

    def masked(self) -> Dict[str, str]:
        """Return keys with values masked for display."""
        result = {}
        for field_name, value in self.model_dump().items():
            if field_name == "custom_endpoints":
                result[field_name] = {k: "••••••••" for k in value}
            elif value:
                result[field_name] = value[:8] + "••••••••"
            else:
                result[field_name] = "⚠ NOT SET"
        return result


class VaultConfig(BaseModel):
    api_keys: APIKeys = Field(default_factory=APIKeys)
    global_base_path: str = str(Path.home())
    default_model: str = "copilot/claude-opus-4-6"
    default_provider: str = "github_copilot"
    initialized: bool = False
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    theme: str = "tokyo_night"
    # Custom global directory overrides (None = use built-in defaults)
    custom_skills_dir: Optional[str] = None
    custom_agents_dir: Optional[str] = None
    custom_logs_dir: Optional[str] = None
    custom_blueprints_dir: Optional[str] = None
    # Per-project relative subdirs (relative to project root)
    project_skills_subdir: str = ".opencode/skills"
    project_agents_subdir: str = ".opencode/agents"

    @field_validator("global_base_path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return str(Path(v).expanduser())


class SkillMetadata(BaseModel):
    name: str
    category: str
    model_preference: str = "copilot/claude-opus-4-6"
    description: str
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    author: str = "nebula-forge"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: Optional[str] = None
    is_global: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        import re
        clean = re.sub(r"[^\w-]", "-", v.lower().strip())
        if not clean:
            raise ValueError("Skill name cannot be empty")
        return clean


class AgentConfig(BaseModel):
    name: str
    model: str = "copilot/claude-opus-4-6"
    description: str = ""
    skills: List[str] = Field(default_factory=list)
    project_path: Optional[str] = None
    thinking_mode: str = "auto"
    max_tokens: int = 64000
    temperature: float = 0.2
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class BlueprintVariable(BaseModel):
    key: str
    label: str
    placeholder: str = ""
    required: bool = True
    default: str = ""


class BlueprintTemplate(BaseModel):
    id: str
    name: str
    description: str
    template_type: str  # refactor | migration | architecture
    variables: List[BlueprintVariable] = Field(default_factory=list)
    thinking_mode: str = "ultra"
    model_context: str = "high_effort"
    preferred_model: str = "copilot/claude-opus-4-6"
    icon: str = "◈"


class OpenCodePlugin(BaseModel):
    name: str                 # npm package name
    display: str              # human name
    description: str
    category: str = "general" # mcp | auth | workflow | ui | memory | notify
    npm_install: str = ""     # e.g. "npx -y opencode-daytona"
    config_snippet: Dict[str, object] = Field(default_factory=dict)


# ── OpenCode Plugin Catalogue ─────────────────────────────────────────────────
OPENCODE_PLUGINS: List[OpenCodePlugin] = [
    OpenCodePlugin(
        name="opencode-daytona",
        display="Daytona Sandboxes",
        description="Run OpenCode sessions in isolated Daytona sandboxes with git sync.",
        category="workflow",
        npm_install="npx -y opencode-daytona",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-daytona"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-dynamic-context-pruning",
        display="Dynamic Context Pruning",
        description="Optimize token usage by pruning obsolete tool outputs.",
        category="workflow",
        npm_install="npx -y opencode-dynamic-context-pruning",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-dynamic-context-pruning"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-morph-fast-apply",
        display="Morph Fast Apply",
        description="10x faster code editing with Morph Fast Apply API and lazy edit markers.",
        category="workflow",
        npm_install="npx -y opencode-morph-fast-apply",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-morph-fast-apply"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-websearch-cited",
        display="Web Search (Cited)",
        description="Native websearch with Google grounded-style citations.",
        category="workflow",
        npm_install="npx -y opencode-websearch-cited",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-websearch-cited"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-pty",
        display="PTY (Background Processes)",
        description="Enable AI agents to run background processes in a PTY.",
        category="workflow",
        npm_install="npx -y opencode-pty",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-pty"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-shell-strategy",
        display="Shell Strategy",
        description="Instructions for non-interactive shell — prevents TTY hangs.",
        category="workflow",
        npm_install="npx -y opencode-shell-strategy",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-shell-strategy"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-supermemory",
        display="Supermemory",
        description="Persistent memory across sessions using Supermemory.",
        category="memory",
        npm_install="npx -y opencode-supermemory",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-supermemory"], "enabled": True},
    ),
    OpenCodePlugin(
        name="oh-my-opencode",
        display="Oh My OpenCode",
        description="Background agents, LSP/AST/MCP tools, curated agents, Claude Code compatible.",
        category="workflow",
        npm_install="npx -y oh-my-opencode",
        config_snippet={"type": "local", "command": ["npx", "-y", "oh-my-opencode"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-workspace",
        display="Workspace (Multi-Agent)",
        description="Bundled multi-agent orchestration harness — 16 components, one install.",
        category="workflow",
        npm_install="npx -y opencode-workspace",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-workspace"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-background-agents",
        display="Background Agents",
        description="Claude Code-style background agents with async delegation.",
        category="workflow",
        npm_install="npx -y opencode-background-agents",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-background-agents"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-helicone-session",
        display="Helicone Session",
        description="Auto-inject Helicone session headers for request grouping.",
        category="mcp",
        npm_install="npx -y opencode-helicone-session",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-helicone-session"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-openai-codex-auth",
        display="OpenAI Codex Auth",
        description="Use ChatGPT Plus/Pro subscription instead of API credits.",
        category="auth",
        npm_install="npx -y opencode-openai-codex-auth",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-openai-codex-auth"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-gemini-auth",
        display="Gemini Auth",
        description="Use existing Gemini plan instead of API billing.",
        category="auth",
        npm_install="npx -y opencode-gemini-auth",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-gemini-auth"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-antigravity-auth",
        display="Antigravity Auth",
        description="Use Antigravity's free models instead of API billing.",
        category="auth",
        npm_install="npx -y opencode-antigravity-auth",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-antigravity-auth"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-devcontainers",
        display="Dev Containers",
        description="Multi-branch devcontainer isolation with shallow clones.",
        category="workflow",
        npm_install="npx -y opencode-devcontainers",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-devcontainers"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-worktree",
        display="Git Worktrees",
        description="Zero-friction git worktrees for OpenCode.",
        category="workflow",
        npm_install="npx -y opencode-worktree",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-worktree"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-wakatime",
        display="WakaTime",
        description="Track OpenCode usage with WakaTime.",
        category="ui",
        npm_install="npx -y opencode-wakatime",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-wakatime"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-notify",
        display="Notifications",
        description="Native OS notifications — know when tasks complete.",
        category="notify",
        npm_install="npx -y opencode-notify",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-notify"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-scheduler",
        display="Scheduler",
        description="Schedule recurring jobs with cron syntax (launchd/systemd).",
        category="workflow",
        npm_install="npx -y opencode-scheduler",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-scheduler"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-skillful",
        display="Skillful",
        description="Lazy load prompts on demand with skill discovery and injection.",
        category="workflow",
        npm_install="npx -y opencode-skillful",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-skillful"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-type-inject",
        display="Type Inject",
        description="Auto-inject TypeScript/Svelte types into file reads.",
        category="workflow",
        npm_install="npx -y opencode-type-inject",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-type-inject"], "enabled": True},
    ),
    OpenCodePlugin(
        name="opencode-md-table-formatter",
        display="Markdown Table Formatter",
        description="Clean up markdown tables produced by LLMs.",
        category="ui",
        npm_install="npx -y opencode-md-table-formatter",
        config_snippet={"type": "local", "command": ["npx", "-y", "opencode-md-table-formatter"], "enabled": True},
    ),
]


class ProvisionEntry(BaseModel):
    path: str
    content: str
    action: str = "create"  # create | modify | symlink
    description: str = ""


class ProvisionPlan(BaseModel):
    """Ghost provisioning — show diff BEFORE writing."""
    title: str
    entries: List[ProvisionEntry] = Field(default_factory=list)
    total_files: int = 0
    total_dirs: int = 0
    description: str = ""
    project_path: Optional[str] = None

    def summary(self) -> str:
        creates = sum(1 for e in self.entries if e.action == "create")
        modifies = sum(1 for e in self.entries if e.action == "modify")
        symlinks = sum(1 for e in self.entries if e.action == "symlink")
        lines = [f"  [cyan]Create[/]  {creates} files/dirs"]
        if modifies:
            lines.append(f"  [yellow]Modify[/]  {modifies} files")
        if symlinks:
            lines.append(f"  [purple]Symlink[/] {symlinks} skills")
        return "\n".join(lines)


class ProjectContext(BaseModel):
    """Detected project information."""
    path: str
    name: str
    has_git: bool = False
    has_package_json: bool = False
    has_pyproject: bool = False
    # OpenCode-first rules files
    has_agents_md: bool = False
    has_opencode_json: bool = False
    has_opencode_dir: bool = False
    # Legacy compat flags
    has_claude_md: bool = False
    has_gemini_json: bool = False
    has_nebula_agents: bool = False
    detected_stack: List[str] = Field(default_factory=list)
    available_skills: List[str] = Field(default_factory=list)
