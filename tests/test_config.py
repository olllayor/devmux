from __future__ import annotations

import pytest

from agenix.utils.config import Config, ConfigError


def test_loads_new_panes_schema(write_config) -> None:
    config_path = write_config(
        """
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
                command: "tail -f logs/app.log"
        """
    )

    config = Config.load(config_path)

    workspace = config.workspaces["backend"]
    assert workspace.layout == "trio"
    assert [pane.name for pane in workspace.panes] == ["planner", "builder", "logs"]
    assert [pane.role for pane in workspace.panes] == ["agent", "agent", "logs"]
    assert workspace.panes[1].command == "codex --approval auto"


def test_loads_legacy_agents_schema_as_agent_panes(write_config) -> None:
    config_path = write_config(
        """
        workspaces:
          backend:
            layout: duo
            cwd: .
            agents:
              - name: planner
                cmd: claude
              - name: builder
                cmd: codex
                flags: --approval auto
        """
    )

    config = Config.load(config_path)

    workspace = config.workspaces["backend"]
    assert [pane.name for pane in workspace.panes] == ["planner", "builder"]
    assert all(pane.role == "agent" for pane in workspace.panes)
    assert workspace.panes[1].command == "codex --approval auto"


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        (
            """
            workspaces:
              bad:
                layout: pentagon
                cwd: .
                panes:
                  - name: one
                    role: agent
                    command: "claude"
                  - name: two
                    role: agent
                    command: "codex"
            """,
            "unsupported layout",
        ),
        (
            """
            workspaces:
              bad:
                layout: duo
                cwd: .
                panes:
                  - name: duplicate
                    role: agent
                    command: "claude"
                  - name: duplicate
                    role: tests
                    command: "pytest -f"
            """,
            "duplicate pane name",
        ),
        (
            """
            workspaces:
              bad:
                layout: duo
                cwd: .
                panes:
                  - name: one
                    role: agent
                    command: "claude"
                  - name: two
                    role: tests
                    command: ""
            """,
            "non-empty command",
        ),
    ],
)
def test_invalid_config_raises_actionable_errors(write_config, contents, message) -> None:
    config_path = write_config(contents)

    with pytest.raises(ConfigError, match=message):
        Config.load(config_path)
