# Releasing devmux

This guide covers how to ship `devmux` so users can discover it, install it, and start using it quickly.

## Trusted Publisher settings

For the PyPI Trusted Publisher form, use:

- `PyPI Project Name`: `devmux`
- `Owner`: `olllayor`
- `Repository name`: `devmux`
- `Workflow name`: `publish.yml`
- `Environment name`: `pypi`

The workflow file for that form now exists at [.github/workflows/publish.yml](/Users/ollayor/Code/Projects/agenix/.github/workflows/publish.yml).

## Before you release

Make sure these basics are in place:

- the README explains what the project is and who it is for
- the repo has a real license file
- `python3 -m pytest` passes
- `python3 -m pip install -e ".[dev]"` works in a clean environment
- `./venv/bin/devmux --help` or `devmux --help` works after install

## 1. Publish the GitHub repo

If the repo is not public yet:

1. Create a GitHub repository named `devmux`.
2. Push the code.
3. Add a short repo description:
   `A tmux launcher for multi-agent CLI development workflows`
4. Add topics such as:
   `tmux`, `cli`, `developer-tools`, `ai-agents`, `productivity`, `python`

## 2. Release flow

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

5. Stop there. GitHub Actions now does the rest automatically:

- builds the package
- creates the GitHub Release from the tag
- publishes to PyPI through Trusted Publishing

You do not need to draft the GitHub Release manually anymore.

## 3. Publish to PyPI

PyPI publishing is now automated by GitHub Actions on tag push.

Create accounts first:

- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/) optional but recommended

### Automatic publish path

The intended release command is:

```bash
git add .
git commit -m "Release v0.2.0"
git tag v0.2.0
git push origin main --tags
```

After that:

- GitHub creates the release
- GitHub publishes `devmux` to PyPI

### Optional local build check

If you want to sanity-check the build before pushing the tag:

```bash
python3 -m pip install --upgrade build twine
```

Build the package locally:

```bash
python3 -m build
```

After the automated publish finishes, verify:

```bash
python3 -m pip install devmux
devmux --help
```

## 4. What users should copy-paste

Put this in every launch post and release note:

```bash
python3 -m pip install devmux
devmux init --preset backend
devmux start backend
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
- tag pushed
- GitHub Actions release job succeeds
- GitHub Actions PyPI publish job succeeds
- install command verified
- short demo asset posted
