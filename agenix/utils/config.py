from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Any

import yaml


VALID_LAYOUTS = {"duo", "trio", "quad", "focus"}
VALID_ROLES = {"agent", "logs", "tests", "shell"}


class ConfigError(ValueError):
    """Raised when agenix configuration is invalid."""


@dataclass(frozen=True)
class PaneConfig:
    name: str
    role: str
    command: str
    cwd: str | None = None

    def resolved_cwd(
        self, workspace_cwd: str | None = None, base_dir: Path | None = None
    ) -> Path:
        cwd = Path(os.path.expanduser(self.cwd or workspace_cwd or "."))
        if cwd.is_absolute():
            return cwd.resolve()
        anchor = base_dir or Path.cwd()
        return (anchor / cwd).resolve()


@dataclass(frozen=True)
class WorkspaceConfig:
    layout: str
    cwd: str | None = None
    panes: list[PaneConfig] = field(default_factory=list)
    base_dir: Path = field(default_factory=Path.cwd)

    def validate(self, name: str) -> None:
        if self.layout not in VALID_LAYOUTS:
            raise ConfigError(
                f"Workspace '{name}' uses unsupported layout '{self.layout}'. "
                f"Choose one of: {', '.join(sorted(VALID_LAYOUTS))}."
            )

        pane_count = len(self.panes)
        if pane_count == 0:
            raise ConfigError(f"Workspace '{name}' must define at least one pane.")

        layout_bounds = {
            "duo": {2},
            "trio": {3},
            "quad": {4},
            "focus": {2, 3, 4, 5},
        }
        if pane_count not in layout_bounds[self.layout]:
            allowed = ", ".join(str(count) for count in sorted(layout_bounds[self.layout]))
            raise ConfigError(
                f"Workspace '{name}' layout '{self.layout}' supports pane counts: {allowed}. "
                f"Found {pane_count}."
            )

        seen_names: set[str] = set()
        for pane in self.panes:
            if not pane.name.strip():
                raise ConfigError(f"Workspace '{name}' contains a pane with an empty name.")
            if pane.name in seen_names:
                raise ConfigError(
                    f"Workspace '{name}' defines duplicate pane name '{pane.name}'."
                )
            seen_names.add(pane.name)

            if pane.role not in VALID_ROLES:
                raise ConfigError(
                    f"Pane '{pane.name}' in workspace '{name}' uses unsupported role "
                    f"'{pane.role}'. Choose one of: {', '.join(sorted(VALID_ROLES))}."
                )
            if not pane.command.strip():
                raise ConfigError(
                    f"Pane '{pane.name}' in workspace '{name}' must define a non-empty command."
                )
            resolved_cwd = pane.resolved_cwd(self.cwd, self.base_dir)
            if not resolved_cwd.exists():
                raise ConfigError(
                    f"Pane '{pane.name}' in workspace '{name}' references missing cwd "
                    f"'{resolved_cwd}'."
                )


@dataclass(frozen=True)
class Config:
    workspaces: dict[str, WorkspaceConfig] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Config":
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        if not isinstance(data, dict):
            raise ConfigError("The config file must contain a top-level mapping.")

        workspaces_data = data.get("workspaces", {})
        if not isinstance(workspaces_data, dict):
            raise ConfigError("'workspaces' must be a mapping.")

        workspaces: dict[str, WorkspaceConfig] = {}
        for workspace_name, raw_workspace in workspaces_data.items():
            if not isinstance(raw_workspace, dict):
                raise ConfigError(
                    f"Workspace '{workspace_name}' must be defined as a mapping."
                )

            layout = str(raw_workspace.get("layout", "")).strip()
            workspace_cwd = raw_workspace.get("cwd")

            panes = cls._parse_panes(raw_workspace)
            workspace = WorkspaceConfig(
                layout=layout,
                cwd=workspace_cwd,
                panes=panes,
                base_dir=path.parent.resolve(),
            )
            workspace.validate(workspace_name)
            workspaces[workspace_name] = workspace

        return cls(workspaces=workspaces)

    @staticmethod
    def _parse_panes(raw_workspace: dict[str, Any]) -> list[PaneConfig]:
        if "panes" in raw_workspace:
            raw_panes = raw_workspace["panes"]
        else:
            raw_agents = raw_workspace.get("agents", [])
            raw_panes = [
                {
                    "name": agent.get("name", ""),
                    "role": "agent",
                    "command": Config._legacy_agent_command(agent),
                    "cwd": agent.get("cwd"),
                }
                for agent in raw_agents
            ]

        if not isinstance(raw_panes, list):
            raise ConfigError("'panes' must be a list.")

        panes: list[PaneConfig] = []
        for raw_pane in raw_panes:
            if not isinstance(raw_pane, dict):
                raise ConfigError("Each pane definition must be a mapping.")

            name = str(raw_pane.get("name", "")).strip()
            role = str(raw_pane.get("role", "agent")).strip()
            command = str(raw_pane.get("command", "")).strip()
            cwd = raw_pane.get("cwd")

            panes.append(PaneConfig(name=name, role=role, command=command, cwd=cwd))

        return panes

    @staticmethod
    def _legacy_agent_command(agent: dict[str, Any]) -> str:
        cmd = str(agent.get("cmd", "")).strip()
        flags = str(agent.get("flags", "")).strip()
        return " ".join(part for part in [cmd, flags] if part)


def render_preset(preset: str) -> str:
    presets = {
        "minimal": """# agenix v0.2 example config
# Replace the example commands below with the agent CLIs you use daily.
workspaces:
  minimal:
    layout: duo
    cwd: .
    panes:
      - name: claude
        role: agent
        command: "claude"
      - name: codex
        role: agent
        command: "codex --approval auto"
""",
        "backend": """# agenix v0.2 example config
# The commands are generic examples. Swap in Claude, Codex, Gemini, Aider, tests, or logs as needed.
workspaces:
  backend:
    layout: trio
    cwd: .
    panes:
      - name: planner
        role: agent
        command: "claude"
      - name: builder
        role: agent
        command: "codex --approval auto"
      - name: logs
        role: logs
        command: "docker compose logs -f"
""",
        "full-stack": """# agenix v0.2 example config
# The layout is tuned for two agents plus live tests and logs.
workspaces:
  full-stack:
    layout: quad
    cwd: .
    panes:
      - name: frontend
        role: agent
        command: "claude"
      - name: backend
        role: agent
        command: "codex --approval auto"
      - name: tests
        role: tests
        command: "npm test"
      - name: logs
        role: logs
        command: "docker compose logs -f"
""",
    }
    if preset not in presets:
        raise ConfigError(
            f"Unknown preset '{preset}'. Choose one of: minimal, backend, full-stack."
        )
    return presets[preset]
