# apdb

`apdb` is an agent-friendly Python debugger inspired by `remote-pdb`.
It keeps the Python call site close to `pdb`, but exposes debugger control
through a small TCP interface that coding agents can call without using an
interactive shell.

The runtime and CLI use only the Python standard library.

## Install

```bash
python -m pip install -U apdb
```

## Python API

```python
import apdb

answer = 41
apdb.set_trace(port=8888)
print(answer + 1)
```

`set_trace()` blocks the target process whether or not a client is connected.
The process resumes only after you send a release command such as `continue`,
`next`, `step`, or `quit`.

By default, `apdb` binds to `127.0.0.1` and uses no authentication:

```python
apdb.set_trace(port=8888, host="127.0.0.1")
```

## CLI

The package installs `apdb_cli`:

```bash
apdb_cli ping --port 8888
apdb_cli state --port 8888
apdb_cli where --port 8888
apdb_cli locals --port 8888
apdb_cli history --port 8888
apdb_cli eval 'answer + 1' --port 8888
apdb_cli eval 'answer + 1' --port 8888 --output result.json
apdb_cli exec-file snippet.py --port 8888
apdb_cli exec-file snippet.py --port 8888 --output result.json
apdb_cli next --port 8888
apdb_cli step --port 8888
apdb_cli continue --port 8888
```

The CLI prints one JSON response to stdout and exits nonzero for connection
failures or API errors.

## TCP interface

The CLI is a wrapper around the TCP interface. Each request and response is one
JSON object followed by a newline.

Request:

```json
{"id": 1, "cmd": "state"}
```

Response:

```json
{"id": 1, "ok": true, "result": {"status": "paused"}}
```

Commands:

- `ping`
- `state`
- `where`
- `locals`
- `history`
- `eval`
- `exec`
- `next`
- `step`
- `continue`
- `quit`

`history` returns commands sent during the current paused debugging session.
Each entry includes the sequence number, request id, command, success flag,
error code for failed commands, and compact `eval`/`exec` input summaries.

## Security

`apdb` has no authentication. Debugger access can inspect and evaluate code
inside the target process. Bind to `127.0.0.1` unless you explicitly want to
expose that control surface.

## Agent Skill

This repository includes a bundled agent skill at `skills/apdb/SKILL.md`.
Install that skill through `apdb_cli` when you want a coding agent to remember
the `apdb` workflow.

Codex:

```bash
apdb_cli skills install --agent codex --scope user
apdb_cli skills install --agent codex --scope project
```

Claude Code:

```bash
apdb_cli skills install --agent claude-code --scope user
apdb_cli skills install --agent claude-code --scope project
```

Both:

```bash
apdb_cli skills install --agent all --scope user
apdb_cli skills install --agent all --scope project
```

Use `--force` to overwrite an existing installed skill. `--scope global` is an
alias for `--scope user`.
