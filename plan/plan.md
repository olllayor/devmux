Solid idea — there's a real gap here. Everyone's juggling 3–5 AI agent terminals and alt-tabbing constantly. Here's my proposal:

**`devmux`** — a tmux session manager purpose-built for AI agent CLIs.

The core concept: one command to spin up a named workspace with agents in a tiled layout, with keyboard shortcuts to route prompts, monitor outputs, and kill/restart sessions without leaving the terminal.Here's the full architecture and UX proposal:

---

## Core features

**1. Workspace profiles (`devmux.yaml`)**
Define named workspaces — each with a layout, which agents to run, and startup flags. Run `devmux start backend` and it spawns a tmux session with Claude Code, Codex, and your log watcher already running in a tiled layout.

**2. Smart layouts**
Pre-built layout presets: `duo` (50/50 split), `trio` (main + two side panes), `quad` (4-way), `focus` (one agent fullscreen + collapsed sidebar for others). Switch layouts mid-session with a keybind.

**3. Prompt broadcast**
A killer feature: type a prompt once and send it to all agents simultaneously. Useful when you want to ask all agents the same question and compare outputs. Toggle broadcast mode with a prefix key.

**4. Session persistence**
Named sessions auto-save their state. `devmux resume backend` brings back exactly what you had — agents restarted, cwd preserved, scrollback intact.

**5. Agent health monitoring**
A status bar (bottom of screen) shows which panes have active agents, which are idle, and which have exited. Color-coded like a process monitor.

---

## CLI interface design

```bash
# Spin up a named workspace
devmux start backend

# Attach to existing session
devmux attach backend

# List all active sessions
devmux ls

# Kill a specific session
devmux kill backend

# Broadcast a prompt to all panes in current session
devmux send "refactor the auth module to use JWT"

# Save current layout as a profile
devmux save my-profile

# Add a new agent pane on the fly
devmux add codex --flags "--approval auto"
```

---

## Config example (`devmux.yaml`)

```yaml
workspaces:
  backend:
    layout: trio
    cwd: ~/projects/tapi
    agents:
      - name: claude
        cmd: claude
        flags: --dangerously-skip-permissions
      - name: codex
        cmd: codex
        flags: --approval auto
      - name: logs
        cmd: docker compose logs -f
    broadcast: false
    
  full-stack:
    layout: quad
    agents:
      - name: claude-fe
        cmd: claude
        cwd: ~/projects/frontend
      - name: claude-be
        cmd: claude
        cwd: ~/projects/tapi
      - name: opencode
        cmd: opencode
      - name: tests
        cmd: npm run test:watch
```

---

## Tech stack to build this

This is a straightforward shell project, but here's the right stack:

- **Core**: Bash or Python (Python preferred for config parsing and cross-platform portability)
- **tmux API**: `libtmux` (Python) — clean programmatic control over sessions/panes/windows
- **Config**: YAML via `PyYAML` or TOML
- **Distribution**: Single binary via `pyinstaller` or published to `pip` / a `curl | bash` installer
- **Optional TUI**: `textual` or `rich` for an interactive dashboard mode

---

## Phased build plan

**Phase 1 (MVP, ~1–2 days):** `start`, `attach`, `ls`, `kill` commands + YAML config parser + basic layouts. Enough to actually use daily.

**Phase 2 (~3 days):** Broadcast mode, `devmux send`, status bar with agent health indicators, session save/restore.

**Phase 3 (polish):** TUI dashboard, plugin system for new agent types, `devmux init` wizard that auto-detects installed agents.

---

Want me to scaffold the actual code for Phase 1? Given your stack (Python is already in your toolbox), I'd start with a `libtmux`-based Python CLI with `click` for the command interface
