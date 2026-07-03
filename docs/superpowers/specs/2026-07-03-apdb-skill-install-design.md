# apdb Skill Install Design

Date: 2026-07-03

## Goal

`apdb_cli` should install the bundled `apdb` agent skill for Codex and Claude
Code without requiring users to know each agent's skill directory layout.

## CLI

Supported commands:

```bash
apdb_cli skills install --agent codex --scope user
apdb_cli skills install --agent codex --scope project
apdb_cli skills install --agent claude-code --scope user
apdb_cli skills install --agent claude-code --scope project
apdb_cli skills install --agent all --scope user
apdb_cli skills install --agent all --scope project
```

`--scope global` is an alias for `--scope user`.

`--force` overwrites an existing installed skill. Without `--force`, an existing
destination is a structured error.

The command prints JSON, like the rest of `apdb_cli`.

## Destinations

User/global installs:

- Codex: `${CODEX_HOME:-~/.codex}/skills/apdb`
- Claude Code: `~/.claude/skills/apdb`

Project installs:

- Codex: `<project-root>/.codex/skills/apdb`
- Claude Code: `<project-root>/.claude/skills/apdb`

For project scope, `<project-root>` is the Git root when available. Outside a
Git repository, it is the current working directory.

## Packaging

The PyPI wheel must include the skill content. The repository keeps the canonical
source at `skills/apdb/SKILL.md` for GitHub skill installers, and the package
includes an identical copy at `apdb/bundled_skill/apdb/SKILL.md`.

Tests verify that both copies stay identical.
