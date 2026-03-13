from __future__ import annotations

from pathlib import Path
import shutil
import textwrap
import uuid

import pytest

from devmux.core.manager import SessionManager


pytestmark = pytest.mark.skipif(
    shutil.which("tmux") is None,
    reason="tmux is required for devmux integration tests",
)


@pytest.fixture
def tmux_socket_name() -> str:
    return f"devmux-test-{uuid.uuid4().hex}"


@pytest.fixture
def manager(tmux_socket_name: str) -> SessionManager:
    session_manager = SessionManager(socket_name=tmux_socket_name)
    yield session_manager
    try:
        session_manager.server.cmd("kill-server")
    except Exception:
        pass


@pytest.fixture
def write_config(tmp_path: Path):
    def _write(contents: str, file_name: str = "devmux.yaml") -> Path:
        path = tmp_path / file_name
        path.write_text(textwrap.dedent(contents).strip() + "\n", encoding="utf-8")
        return path

    return _write
