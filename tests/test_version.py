from __future__ import annotations

from pathlib import Path
import tomllib

from devmux import __version__


def test_package_version_matches_pyproject() -> None:
    with Path("pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert __version__ == pyproject["project"]["version"]
