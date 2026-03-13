from __future__ import annotations

import os
import time

import pytest

from devmux.core.manager import SessionManagerError
from devmux.utils.config import Config


def _capture_text(pane) -> str:
    return "\n".join(pane.capture_pane(start="-", end="-"))


@pytest.mark.parametrize(
    ("layout", "pane_count"),
    [("duo", 2), ("trio", 3), ("quad", 4), ("focus", 4)],
)
def test_start_workspace_creates_expected_panes(manager, write_config, layout, pane_count) -> None:
    pane_defs = "\n".join(
        f"""              - name: pane-{index}
                role: {'agent' if index < 2 else 'logs'}
                command: "cat"
"""
        for index in range(pane_count)
    )
    config_path = write_config(
        f"""
        workspaces:
          demo:
            layout: {layout}
            cwd: .
            panes:
{pane_defs}
        """
    )
    config = Config.load(config_path)

    result = manager.start_workspace("demo", config)

    assert result.created is True
    session = manager.server.sessions.get(session_name="demo")
    assert session is not None
    panes = list(session.active_window.panes)
    assert len(panes) == pane_count
    assert {pane.pane_title for pane in panes} == {f"pane-{index}" for index in range(pane_count)}


def test_start_workspace_is_idempotent_and_recreate_rebuilds(manager, write_config) -> None:
    config_path = write_config(
        """
        workspaces:
          demo:
            layout: duo
            cwd: .
            panes:
              - name: planner
                role: agent
                command: "cat"
              - name: builder
                role: agent
                command: "cat"
        """
    )
    config = Config.load(config_path)

    first = manager.start_workspace("demo", config)
    first_session = manager.server.sessions.get(session_name="demo")
    assert first_session is not None
    first_session.active_window.split()
    second = manager.start_workspace("demo", config)
    recreated = manager.start_workspace("demo", config, recreate=True)
    recreated_session = manager.server.sessions.get(session_name="demo")

    assert first.created is True
    assert second.created is False
    assert recreated.created is True
    assert recreated_session is not None
    assert len(recreated_session.active_window.panes) == 2
    assert {pane.pane_title for pane in recreated_session.active_window.panes} == {
        "planner",
        "builder",
    }


def test_send_targets_agent_panes_by_default_and_supports_explicit_targets(
    manager, write_config, monkeypatch
) -> None:
    config_path = write_config(
        """
        workspaces:
          demo:
            layout: trio
            cwd: .
            panes:
              - name: planner
                role: agent
                command: "cat"
              - name: builder
                role: agent
                command: "cat"
              - name: logs
                role: logs
                command: "cat"
        """
    )
    config = Config.load(config_path)
    manager.start_workspace("demo", config)
    session = manager.server.sessions.get(session_name="demo")
    assert session is not None

    delivered = manager.broadcast_prompt("status", session_name="demo")
    time.sleep(0.1)

    panes = {pane.pane_title: pane for pane in session.active_window.panes}
    assert delivered == ["planner", "builder"]
    assert "status" in _capture_text(panes["planner"])
    assert "status" in _capture_text(panes["builder"])
    assert "status" not in _capture_text(panes["logs"])

    delivered = manager.broadcast_prompt("logs please", session_name="demo", role="logs")
    time.sleep(0.1)
    assert delivered == ["logs"]
    assert "logs please" in _capture_text(panes["logs"])

    delivered = manager.broadcast_prompt(
        "builder only",
        session_name="demo",
        pane_names=["builder"],
    )
    time.sleep(0.1)
    assert delivered == ["builder"]
    assert "builder only" in _capture_text(panes["builder"])

    monkeypatch.delenv("TMUX_PANE", raising=False)
    with pytest.raises(SessionManagerError, match="no session specified"):
        manager.broadcast_prompt("missing session")


def test_send_rejects_unknown_pane_name(manager, write_config) -> None:
    config_path = write_config(
        """
        workspaces:
          demo:
            layout: duo
            cwd: .
            panes:
              - name: planner
                role: agent
                command: "cat"
              - name: builder
                role: agent
                command: "cat"
        """
    )
    config = Config.load(config_path)
    manager.start_workspace("demo", config)

    with pytest.raises(SessionManagerError, match="Unknown pane names"):
        manager.broadcast_prompt("hello", session_name="demo", pane_names=["missing"])
