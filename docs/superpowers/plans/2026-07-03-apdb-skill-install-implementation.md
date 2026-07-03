# apdb Skill Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `apdb_cli skills install` for Codex and Claude Code user/project skill installation.

**Architecture:** Add a small stdlib installer module that resolves agent/scope destinations and copies the packaged skill directory. Extend `apdb.cli` with nested `skills install` parsing while preserving existing debugger commands.

**Tech Stack:** Python standard library only: `argparse`, `json`, `os`, `pathlib`, `shutil`, `subprocess`, `sys`, `unittest`, `tempfile`.

---

### Task 1: Installer Core

**Files:**
- Create: `apdb/skill_installer.py`
- Test: `tests/test_skill_installer.py`

- [ ] Write failing tests for user and project destination resolution.
- [ ] Write failing tests for install, existing destination error, and force overwrite.
- [ ] Implement destination resolution and copy behavior.
- [ ] Verify `python3 -m unittest tests.test_skill_installer -v`.

### Task 2: CLI Integration

**Files:**
- Modify: `apdb/cli.py`
- Test: `tests/test_cli.py`

- [ ] Write failing tests for `apdb_cli skills install` JSON output.
- [ ] Implement nested `skills install` parsing.
- [ ] Preserve all existing debugger commands.
- [ ] Verify `python3 -m unittest tests.test_cli -v`.

### Task 3: Packaging and Docs

**Files:**
- Create: `apdb/bundled_skill/apdb/SKILL.md`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Test: `tests/test_skill.py`

- [ ] Add packaged skill copy and package-data config.
- [ ] Test canonical and packaged skill copies are identical.
- [ ] Document install commands in README.
- [ ] Verify `python3 -m unittest discover -v` and `python3 -m build`.
