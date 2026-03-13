## [ERR-20260313-001] pip_install_system_python

**Logged**: 2026-03-13T23:46:00+05:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Installing Python build/test dependencies with the Homebrew-managed system interpreter failed due to PEP 668 protections.

### Error
```text
error: externally-managed-environment
```

### Context
- Command attempted: `python3 -m pip install -e '.[dev]' build`
- Repo: `/Users/ollayor/Code/Projects/agenix`
- Environment: macOS with Homebrew-managed Python

### Suggested Fix
Use an isolated virtual environment for local verification commands in this repo, for example `.venv/bin/python -m pip ...`, instead of installing into the system interpreter.

### Metadata
- Reproducible: yes
- Related Files: pyproject.toml

---
