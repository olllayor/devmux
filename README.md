# devmux

`devmux` is a tmux launcher for developers who use multiple AI agents in the CLI.

It gives you one command to open a repeatable coding cockpit with agent panes, tests, logs, and shell helpers in the right layout and working directories.

## Why it exists

If you already work with tools like Claude Code, Codex, Gemini CLI, Aider, test watchers, and logs, your terminal usually turns into a mess:

- too many panes to rebuild by hand
- prompts sent to the wrong place
- different repos and directories across panes
- no shared setup you can reuse every day

`devmux` fixes that by making your workflow reproducible.

## What it does

- Launch named workspaces from `devmux.yaml`
- Create real tmux layouts: `duo`, `trio`, `quad`, `focus`
- Route prompts safely by pane role or pane name
- Reuse existing sessions with idempotent `start`
- Rebuild a workspace with `--recreate`
- Scaffold starter configs with `devmux init`
- Keep runtime behavior generic while still supporting AI-heavy workflows

## Who it is for

`devmux` is best for developers who:

- already use tmux
- run 2 to 5 CLI agents or helper panes at once
- want one command to restore a known working setup
- want a simple, scriptable alternative to a full TUI dashboard

## Requirements

- macOS or Linux
- `tmux` installed and available on `PATH`
- Python 3.8+

Check tmux:

```bash
tmux -V
```

## Install

### Option 1: Install from PyPI

Use this after you publish `devmux` to PyPI:

```bash
python3 -m pip install devmux
```

### Option 2: Install from GitHub right now

If you want people to try it before a PyPI release:

```bash
python3 -m pip install "git+https://github.com/olllayor/devmux.git"
```

### Option 3: Install locally for development

```bash
git clone https://github.com/olllayor/devmux.git
cd devmux
python3 -m pip install -e ".[dev]"
```

## Quick start

Generate a starter config:

```bash
devmux init --preset backend
```

Start the workspace:

```bash
devmux start backend
```

Create or reuse a session without attaching:

```bash
devmux start backend --detach
```

Resume the same workspace later:

```bash
devmux resume backend
```

Send a prompt to all agent panes in the current session:

```bash
devmux send "review the auth flow"
```

Target a specific role or pane:

```bash
devmux send "show me errors" --role logs
devmux send "run tests" --pane tests
devmux send "status" --all
```

List or kill sessions:

```bash
devmux ls
devmux kill backend
```

## Config

Example `devmux.yaml`:

```yaml
workspaces:
  backend:
    layout: trio
    cwd: ~/projects/tapi
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
```

Accepted layouts:

- `duo`
- `trio`
- `quad`
- `focus`

Accepted roles:

- `agent`
- `logs`
- `tests`
- `shell`

Legacy `agents` configs are still accepted and mapped to `role: agent`.

## Commands

```bash
devmux init [--preset minimal|backend|full-stack] [--config PATH] [--force]
devmux start <workspace> [--config PATH] [--detach] [--recreate]
devmux attach <workspace>
devmux resume <workspace>
devmux ls
devmux kill <workspace>
devmux send "<prompt>" [--session NAME] [--all | --role ROLE | --pane NAME ...]
```

## Typical workflows

### Two-agent coding setup

```yaml
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
```

### Backend setup with logs

```yaml
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
```

### Full-stack setup with tests and logs

```yaml
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
```

## How to release it to the world

Use two distribution paths:

1. GitHub for discovery, source, issues, releases, and docs.
2. PyPI for the simplest install command: `python3 -m pip install devmux`.

Recommended rollout order:

1. Push this repo to GitHub with a clean README, license, and tagged release.
2. Push a version tag like `v0.2.0`; GitHub Actions creates the release and publishes to PyPI.
3. Share a short demo GIF/video showing `devmux init`, `devmux start`, and `devmux send`.
4. Post it in places where AI-heavy CLI devs already are: X, Reddit, Hacker News, tmux/devtools communities, Discord/Slack groups, and your own network.

The detailed publishing checklist is in [RELEASING.md](/Users/ollayor/Code/Projects/agenix/RELEASING.md).

## Development

Install dev dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Run tests:

```bash
python3 -m pytest
```

## Scope

`devmux` v0.2 is intentionally focused:

- no TUI yet
- no status bar or health dashboard
- no deep agent-specific integrations
- no full pane history or recovery system

The goal is to be a reliable painkiller for launching and routing multi-agent CLI sessions.
