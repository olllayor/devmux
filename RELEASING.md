# Releasing agenix

This guide covers how to ship `agenix` so users can discover it, install it, and start using it quickly.

## Before you release

Make sure these basics are in place:

- the README explains what the project is and who it is for
- the repo has a real license file
- `python3 -m pytest` passes
- `python3 -m pip install -e ".[dev]"` works in a clean environment
- `./venv/bin/agenix --help` or `agenix --help` works after install

## 1. Publish the GitHub repo

If the repo is not public yet:

1. Create a GitHub repository named `agenix`.
2. Push the code.
3. Add a short repo description:
   `A tmux launcher for multi-agent CLI development workflows`
4. Add topics such as:
   `tmux`, `cli`, `developer-tools`, `ai-agents`, `productivity`, `python`

## 2. Create a GitHub release

For each release:

1. Bump `version` in [pyproject.toml](/Users/ollayor/Code/Projects/agenix/pyproject.toml).
2. Update any README examples if behavior changed.
3. Run:

```bash
python3 -m pytest
```

4. Commit the release:

```bash
git add .
git commit -m "Release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

5. Create a GitHub Release for tag `v0.2.0`.

Release notes should include:

- what changed
- who it is useful for
- the install command
- one short example

## 3. Publish to PyPI

Create accounts first:

- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/) optional but recommended

Install build tools:

```bash
python3 -m pip install --upgrade build twine
```

Build the package:

```bash
python3 -m build
```

Upload to TestPyPI first:

```bash
python3 -m twine upload --repository testpypi dist/*
```

Test install from TestPyPI:

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple agenix
```

If that works, upload to PyPI:

```bash
python3 -m twine upload dist/*
```

After publish, verify:

```bash
python3 -m pip install agenix
agenix --help
```

## 4. What users should copy-paste

Put this in every launch post and release note:

```bash
python3 -m pip install agenix
agenix init --preset backend
agenix start backend
```

That is the shortest path from discovery to value.

## 5. How to get real adoption

Do not lead with features. Lead with the pain:

- “Run Claude, Codex, logs, and tests in one repeatable tmux workspace.”
- “One command to restore your AI coding cockpit.”
- “Stop rebuilding multi-agent terminal setups by hand.”

Best launch assets:

- a 20 to 40 second demo video or GIF
- one screenshot of the running tmux layout
- one minimal example config
- one install command

## 6. Recommended launch channels

- GitHub Release
- X / Twitter
- Hacker News “Show HN”
- Reddit communities for tmux, CLI tools, and AI coding
- Discord/Slack communities around devtools and AI agents
- direct outreach to friends who already use multiple CLI agents

## 7. Release checklist

- README is current
- version bumped
- tests pass
- build succeeds
- PyPI upload succeeds
- GitHub release created
- install command verified
- short demo asset posted
