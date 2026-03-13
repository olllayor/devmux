#!/usr/bin/env python3
"""devmux - A tmux session manager for AI agent CLIs."""

from __future__ import annotations

from pathlib import Path
import sys

import click

from devmux import __version__
from devmux.core.manager import SessionManager, SessionManagerError
from devmux.utils.config import Config, ConfigError, VALID_ROLES, render_preset


def _load_config(config_path: str) -> Config:
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file '{config_path}' not found.")
    return Config.load(path)


def _fail(exc: Exception) -> None:
    click.echo(f"Error: {exc}", err=True)
    raise SystemExit(1) from exc


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Launch reproducible tmux workspaces for AI-heavy CLI development."""


@cli.command()
@click.option(
    "--preset",
    type=click.Choice(["minimal", "backend", "full-stack"]),
    default="backend",
    show_default=True,
    help="Starter workspace template to scaffold.",
)
@click.option(
    "--config",
    "-c",
    default="devmux.yaml",
    show_default=True,
    help="Path to write the generated config file.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite the target config file if it already exists.",
)
def init(preset: str, config: str, force: bool) -> None:
    """Create a starter devmux config."""
    try:
        config_path = Path(config)
        if config_path.exists() and not force:
            raise ConfigError(
                f"Config file '{config}' already exists. Pass --force to overwrite it."
            )

        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(render_preset(preset), encoding="utf-8")
        click.echo(f"Wrote {preset} preset to '{config}'.")
    except Exception as exc:
        _fail(exc)


@cli.command()
@click.argument("workspace_name")
@click.option(
    "--config",
    "-c",
    default="devmux.yaml",
    show_default=True,
    help="Path to config file.",
)
@click.option(
    "--detach",
    is_flag=True,
    help="Create or reuse the session without attaching to it.",
)
@click.option(
    "--recreate",
    is_flag=True,
    help="Kill any existing session with the same name before creating it again.",
)
def start(workspace_name: str, config: str, detach: bool, recreate: bool) -> None:
    """Create or resume a named workspace."""
    try:
        cfg = _load_config(config)
        manager = SessionManager()
        result = manager.start_workspace(workspace_name, cfg, recreate=recreate)

        if detach:
            verb = "Created" if result.created else "Reusing"
            click.echo(f"{verb} detached session '{workspace_name}'.")
            return

        click.echo(f"Attaching to session '{workspace_name}'.")
        manager.attach_session(workspace_name)
    except Exception as exc:
        _fail(exc)


@cli.command(name="attach")
@click.argument("workspace_name")
def attach(workspace_name: str) -> None:
    """Attach to an existing session."""
    try:
        manager = SessionManager()
        manager.attach_session(workspace_name)
    except Exception as exc:
        _fail(exc)


@cli.command(name="resume")
@click.argument("workspace_name")
def resume(workspace_name: str) -> None:
    """Resume an existing session by name."""
    try:
        manager = SessionManager()
        manager.attach_session(workspace_name)
    except Exception as exc:
        _fail(exc)


@cli.command(name="ls")
def list_sessions() -> None:
    """List active tmux sessions."""
    try:
        manager = SessionManager()
        sessions = manager.list_sessions()
        if sessions:
            click.echo("Active sessions:")
            for session in sessions:
                click.echo(f"  - {session}")
        else:
            click.echo("No active sessions.")
    except Exception as exc:
        _fail(exc)


@cli.command()
@click.argument("workspace_name")
def kill(workspace_name: str) -> None:
    """Kill a named session."""
    try:
        manager = SessionManager()
        manager.kill_session(workspace_name)
        click.echo(f"Killed session '{workspace_name}'.")
    except Exception as exc:
        _fail(exc)


@cli.command()
@click.argument("prompt")
@click.option(
    "--session",
    "-s",
    help="Target session name. Defaults to the current tmux session.",
)
@click.option(
    "--all",
    "send_all",
    is_flag=True,
    help="Send to every pane in the target session.",
)
@click.option(
    "--role",
    type=click.Choice(sorted(VALID_ROLES)),
    help="Send only to panes with the selected role.",
)
@click.option(
    "--pane",
    "pane_names",
    multiple=True,
    help="Send only to the named pane. Repeat to target multiple panes.",
)
def send(
    prompt: str,
    session: str | None,
    send_all: bool,
    role: str | None,
    pane_names: tuple[str, ...],
) -> None:
    """Send a prompt to selected panes."""
    try:
        if send_all and (role or pane_names):
            raise click.ClickException(
                "--all cannot be combined with --role or --pane."
            )
        if role and pane_names:
            raise click.ClickException("--role cannot be combined with --pane.")

        manager = SessionManager()
        delivered_to = manager.broadcast_prompt(
            prompt,
            session_name=session,
            send_all=send_all,
            role=role,
            pane_names=pane_names,
        )
        click.echo(f"Delivered prompt to: {', '.join(delivered_to)}")
    except Exception as exc:
        _fail(exc)


def main() -> int:
    cli()
    return 0


if __name__ == "__main__":
    sys.exit(main())
