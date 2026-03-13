from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from devmux.cli.main import cli, main
from devmux.core.manager import StartResult


class FakeManager:
    def __init__(self):
        self.started = []
        self.attached = []
        self.sent = None

    def start_workspace(self, workspace_name, config, recreate=False):
        self.started.append((workspace_name, recreate, sorted(config.workspaces)))
        return StartResult(session_name=workspace_name, created=True)

    def attach_session(self, workspace_name):
        self.attached.append(workspace_name)

    def list_sessions(self):
        return ["alpha", "beta"]

    def kill_session(self, workspace_name):
        self.attached.append(f"killed:{workspace_name}")

    def broadcast_prompt(self, prompt, session_name=None, send_all=False, role=None, pane_names=()):
        self.sent = (prompt, session_name, send_all, role, tuple(pane_names))
        return ["planner", "builder"]


def test_init_writes_expected_preset(tmp_path: Path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "devmux.yaml"

    result = runner.invoke(cli, ["init", "--preset", "minimal", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "Wrote minimal preset" in result.output
    assert "layout: duo" in config_path.read_text(encoding="utf-8")


def test_resume_calls_attach(monkeypatch) -> None:
    runner = CliRunner()
    fake_manager = FakeManager()
    monkeypatch.setattr("devmux.cli.main.SessionManager", lambda: fake_manager)

    result = runner.invoke(cli, ["resume", "backend"])

    assert result.exit_code == 0
    assert fake_manager.attached == ["backend"]


def test_attach_missing_session_shows_real_error(monkeypatch) -> None:
    runner = CliRunner()

    class MissingManager:
        def attach_session(self, workspace_name):
            raise RuntimeError(f"Session '{workspace_name}' does not exist.")

    monkeypatch.setattr("devmux.cli.main.SessionManager", lambda: MissingManager())

    result = runner.invoke(cli, ["attach", "codex"])

    assert result.exit_code == 1
    assert "Session 'codex' does not exist." in result.output


def test_start_with_detach_uses_idempotent_manager(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    fake_manager = FakeManager()
    monkeypatch.setattr("devmux.cli.main.SessionManager", lambda: fake_manager)
    config_path = tmp_path / "devmux.yaml"
    config_path.write_text(
        """
workspaces:
  backend:
    layout: duo
    cwd: .
    panes:
      - name: planner
        role: agent
        command: "claude"
      - name: builder
        role: agent
        command: "codex --approval auto"
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["start", "backend", "--config", str(config_path), "--detach", "--recreate"],
    )

    assert result.exit_code == 0
    assert fake_manager.started == [("backend", True, ["backend"])]
    assert "detached session 'backend'" in result.output


def test_send_enforces_safe_flag_combinations(monkeypatch) -> None:
    runner = CliRunner()
    fake_manager = FakeManager()
    monkeypatch.setattr("devmux.cli.main.SessionManager", lambda: fake_manager)

    result = runner.invoke(cli, ["send", "hello", "--all", "--role", "logs"])

    assert result.exit_code == 1
    assert "--all cannot be combined" in result.output


def test_send_routes_to_expected_targets(monkeypatch) -> None:
    runner = CliRunner()
    fake_manager = FakeManager()
    monkeypatch.setattr("devmux.cli.main.SessionManager", lambda: fake_manager)

    result = runner.invoke(cli, ["send", "hello", "--session", "backend", "--pane", "builder"])

    assert result.exit_code == 0
    assert fake_manager.sent == ("hello", "backend", False, None, ("builder",))
    assert "planner, builder" in result.output


def test_main_entrypoint_returns_zero(monkeypatch) -> None:
    monkeypatch.setattr("devmux.cli.main.cli", lambda: None)
    assert main() == 0
