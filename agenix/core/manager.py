from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
from typing import Iterable

import libtmux
from libtmux.constants import OptionScope, PaneDirection
from libtmux.pane import Pane
from libtmux.session import Session
from libtmux.window import Window

from agenix.utils.config import Config, ConfigError, PaneConfig, WorkspaceConfig


class SessionManagerError(RuntimeError):
    """Raised when tmux session management fails."""


@dataclass(frozen=True)
class StartResult:
    session_name: str
    created: bool


class SessionManager:
    def __init__(self, socket_name: str | None = None, tmux_bin: str | None = None):
        self.tmux_bin = tmux_bin or shutil.which("tmux")
        self.server = libtmux.Server(socket_name=socket_name, tmux_bin=self.tmux_bin)

    def ensure_tmux_available(self) -> None:
        if not self.tmux_bin:
            raise SessionManagerError(
                "tmux is not installed or not available on PATH. Install tmux first."
            )
        try:
            self.server.cmd("list-sessions")
        except Exception as exc:  # pragma: no cover - libtmux exception surface varies
            raise SessionManagerError(f"Unable to reach tmux: {exc}") from exc

    def start_workspace(
        self,
        workspace_name: str,
        config: Config,
        *,
        recreate: bool = False,
    ) -> StartResult:
        self.ensure_tmux_available()
        workspace = self._get_workspace(config, workspace_name)

        if recreate and self.server.has_session(workspace_name):
            self.kill_session(workspace_name)

        if self.server.has_session(workspace_name):
            return StartResult(session_name=workspace_name, created=False)

        session = self._create_session(workspace_name, workspace)
        self._configure_session(session, workspace)
        return StartResult(session_name=workspace_name, created=True)

    def attach_session(self, workspace_name: str) -> None:
        self.ensure_tmux_available()
        session = self._find_session(workspace_name)
        if session is None:
            raise SessionManagerError(f"Session '{workspace_name}' does not exist.")
        self.server.attach_session(target_session=workspace_name)

    def list_sessions(self) -> list[str]:
        self.ensure_tmux_available()
        return [session.session_name for session in self.server.sessions]

    def kill_session(self, workspace_name: str) -> None:
        self.ensure_tmux_available()
        session = self._find_session(workspace_name)
        if session is None:
            raise SessionManagerError(f"Session '{workspace_name}' does not exist.")
        session.kill()

    def broadcast_prompt(
        self,
        prompt: str,
        *,
        session_name: str | None = None,
        send_all: bool = False,
        role: str | None = None,
        pane_names: Iterable[str] | None = None,
    ) -> list[str]:
        self.ensure_tmux_available()
        session = self._resolve_session_for_send(session_name)
        panes = self._resolve_target_panes(
            session,
            send_all=send_all,
            role=role,
            pane_names=list(pane_names or []),
        )
        if not panes:
            raise SessionManagerError(
                f"No panes matched in session '{session.session_name}'."
            )

        delivered_to: list[str] = []
        for pane in panes:
            pane.send_keys(prompt, enter=True)
            delivered_to.append(self._pane_name(pane))
        return delivered_to

    def _create_session(self, workspace_name: str, workspace: WorkspaceConfig) -> Session:
        start_directory = None
        if workspace.cwd:
            start_directory = str(
                PaneConfig(
                    name="_workspace",
                    role="shell",
                    command="true",
                    cwd=workspace.cwd,
                ).resolved_cwd(base_dir=workspace.base_dir)
            )
        return self.server.new_session(
            session_name=workspace_name,
            attach=False,
            start_directory=start_directory,
        )

    def _configure_session(self, session: Session, workspace: WorkspaceConfig) -> None:
        window = session.active_window
        panes = self._build_layout(window, workspace)
        for pane, pane_config in zip(panes, workspace.panes, strict=True):
            self._configure_pane(pane, pane_config, workspace)

    def _build_layout(self, window: Window, workspace: WorkspaceConfig) -> list[Pane]:
        base_pane = window.active_pane
        panes = [base_pane]

        if workspace.layout == "duo":
            panes.append(base_pane.split(direction=PaneDirection.Right, size="50%"))
            return panes

        if workspace.layout == "trio":
            side_pane = base_pane.split(direction=PaneDirection.Right, size="50%")
            panes.append(side_pane)
            panes.append(side_pane.split(direction=PaneDirection.Below, size="50%"))
            return panes

        if workspace.layout == "quad":
            right_pane = base_pane.split(direction=PaneDirection.Right, size="50%")
            panes.append(right_pane)
            panes.append(base_pane.split(direction=PaneDirection.Below, size="50%"))
            panes.append(right_pane.split(direction=PaneDirection.Below, size="50%"))
            return panes

        if workspace.layout == "focus":
            side_seed = base_pane.split(direction=PaneDirection.Right, size="30%")
            panes.append(side_seed)
            for _ in range(len(workspace.panes) - 2):
                panes.append(side_seed.split(direction=PaneDirection.Below))
            window.select_layout("main-vertical")
            window.set_option("main-pane-width", "70%", scope=OptionScope.Window)
            return panes

        raise SessionManagerError(f"Unsupported layout '{workspace.layout}'.")

    def _configure_pane(
        self, pane: Pane, pane_config: PaneConfig, workspace: WorkspaceConfig
    ) -> None:
        pane_path = pane_config.resolved_cwd(workspace.cwd, workspace.base_dir)
        pane.set_title(pane_config.name)
        pane.set_option("@agenix_name", pane_config.name, scope=OptionScope.Pane)
        pane.set_option("@agenix_role", pane_config.role, scope=OptionScope.Pane)
        pane.send_keys(f"cd {self._shell_quote(str(pane_path))}", enter=True)
        pane.send_keys(pane_config.command, enter=True)

    def _resolve_session_for_send(self, session_name: str | None) -> Session:
        target_session = session_name or self._current_session_name()
        if not target_session:
            raise SessionManagerError(
                "Not inside a tmux session and no session specified. Pass --session NAME."
            )
        session = self._find_session(target_session)
        if session is None:
            raise SessionManagerError(f"Session '{target_session}' does not exist.")
        return session

    def _resolve_target_panes(
        self,
        session: Session,
        *,
        send_all: bool,
        role: str | None,
        pane_names: list[str],
    ) -> list[Pane]:
        panes = list(session.active_window.panes)
        if send_all:
            return panes

        if pane_names:
            matched = [pane for pane in panes if self._pane_name(pane) in set(pane_names)]
            missing = sorted(set(pane_names) - {self._pane_name(pane) for pane in matched})
            if missing:
                raise SessionManagerError(
                    f"Unknown pane names for session '{session.session_name}': {', '.join(missing)}."
                )
            return matched

        target_role = role or "agent"
        return [pane for pane in panes if self._pane_role(pane) == target_role]

    def _get_workspace(self, config: Config, workspace_name: str) -> WorkspaceConfig:
        workspace = config.workspaces.get(workspace_name)
        if workspace is None:
            raise ConfigError(f"Workspace '{workspace_name}' not found in config.")
        return workspace

    def _find_session(self, workspace_name: str) -> Session | None:
        return self.server.sessions.get(session_name=workspace_name)

    def _current_session_name(self) -> str | None:
        pane_id = os.environ.get("TMUX_PANE")
        if not pane_id:
            return None
        output = self.server.cmd("display-message", "-p", "-t", pane_id, "#{session_name}")
        if output.returncode != 0 or not output.stdout:
            return None
        return output.stdout[0].strip()

    @staticmethod
    def _pane_name(pane: Pane) -> str:
        return str(pane.show_option("@agenix_name", scope=OptionScope.Pane) or pane.pane_title)

    @staticmethod
    def _pane_role(pane: Pane) -> str:
        return str(pane.show_option("@agenix_role", scope=OptionScope.Pane) or "agent")

    @staticmethod
    def _shell_quote(value: str) -> str:
        return "'" + value.replace("'", "'\"'\"'") + "'"
