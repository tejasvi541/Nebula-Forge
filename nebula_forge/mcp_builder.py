"""
NEBULA-FORGE — MCP Plugin Builder (Foundation)
Heuristic tool extraction + local TypeScript server scaffolding.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MCPTool:
    name: str
    description: str


class MCPPluginBuilder:
    """Generate a minimal MCP server scaffold from natural-language intent."""

    def analyze_description(self, description: str) -> list[MCPTool]:
        text = description.lower()
        candidates: list[MCPTool] = []

        keyword_map = {
            "search": "search_records",
            "read": "read_record",
            "get": "read_record",
            "create": "create_record",
            "update": "update_record",
            "delete": "delete_record",
            "list": "list_records",
            "find": "search_records",
        }

        seen = set()
        for key, tool in keyword_map.items():
            if key in text and tool not in seen:
                seen.add(tool)
                candidates.append(MCPTool(name=tool, description=f"Auto-detected from keyword: {key}"))

        if not candidates:
            candidates = [
                MCPTool(name="run_task", description="Generic task execution tool"),
                MCPTool(name="get_status", description="Generic status retrieval tool"),
            ]

        return candidates

    def generate_typescript_server(self, plugin_name: str, tools: list[MCPTool]) -> str:
        handlers = []
        tool_decls = []

        for tool in tools:
            tool_decls.append(
                """      {
        name: \"{name}\",
        description: \"{desc}\",
        inputSchema: {
          type: \"object\",
          properties: {
            input: { type: \"string\" }
          },
          required: [\"input\"]
        }
      }""".format(name=tool.name, desc=tool.description.replace('"', "'"))
            )
            handlers.append(
                """  if (name === \"{name}\") {{
    return {{
      content: [
        {{ type: \"text\", text: `[{plugin}] {name} executed with input: ${{args?.input ?? \"\"}}` }}
      ]
    }};
  }}""".format(name=tool.name, plugin=plugin_name)
            )

        return """import {{ Server }} from \"@modelcontextprotocol/sdk/server/index.js\";
import {{ StdioServerTransport }} from \"@modelcontextprotocol/sdk/server/stdio.js\";
import {{ CallToolRequestSchema, ListToolsRequestSchema }} from \"@modelcontextprotocol/sdk/types.js\";

const server = new Server(
  {{ name: \"{plugin}\", version: \"1.0.0\" }},
  {{ capabilities: {{ tools: {{}} }} }}
);

server.setRequestHandler(ListToolsRequestSchema, async () => {{
  return {{
    tools: [
{tools}
    ]
  }};
}});

server.setRequestHandler(CallToolRequestSchema, async (request) => {{
  const name = request.params.name;
  const args = request.params.arguments as Record<string, unknown> | undefined;

{handlers}

  throw new Error(`Unknown tool: ${{name}}`);
}});

const transport = new StdioServerTransport();
await server.connect(transport);
""".format(
            plugin=plugin_name,
            tools=",\n".join(tool_decls),
            handlers="\n\n".join(handlers),
        )

    def generate_package_json(self, plugin_name: str) -> str:
        pkg = {
            "name": plugin_name,
            "version": "1.0.0",
            "type": "module",
            "private": True,
            "scripts": {
                "build": "tsc -p .",
                "start": "node dist/server.js"
            },
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0"
            },
            "devDependencies": {
                "typescript": "^5.5.4"
            }
        }
        return json.dumps(pkg, indent=2)

    def generate_tsconfig(self) -> str:
        return json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2022",
                    "module": "NodeNext",
                    "moduleResolution": "NodeNext",
                    "outDir": "dist",
                    "rootDir": "src",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                },
                "include": ["src"]
            },
            indent=2,
        )

    def write_plugin(self, project_path: Path, plugin_name: str, tools: list[MCPTool]) -> tuple[bool, str, Path]:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", plugin_name.strip().lower()) or "mcp-plugin"
        root = project_path / ".opencode" / "mcp-servers" / safe
        src = root / "src"
        try:
            src.mkdir(parents=True, exist_ok=True)
            (src / "server.ts").write_text(self.generate_typescript_server(safe, tools), encoding="utf-8")
            (root / "package.json").write_text(self.generate_package_json(safe), encoding="utf-8")
            (root / "tsconfig.json").write_text(self.generate_tsconfig(), encoding="utf-8")
            self._register_opencode(project_path, safe)
            return True, f"Generated MCP plugin '{safe}'", root
        except Exception as e:
            return False, str(e), root

    def _register_opencode(self, project_path: Path, plugin_name: str) -> None:
        config_path = project_path / "opencode.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                config = {}
        else:
            config = {
                "$schema": "https://opencode.ai/config.json",
                "mcp": {},
            }

        config.setdefault("mcp", {})
        config["mcp"][plugin_name] = {
            "type": "local",
            "command": ["npm", "run", "start", "--prefix", f".opencode/mcp-servers/{plugin_name}"],
            "enabled": True,
        }
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
