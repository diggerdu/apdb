---
name: apdb
description: Use when debugging Python code with apdb, agent-friendly pdb, remote pdb, TCP debugger commands, apdb_cli, or when a user asks an agent to inspect a paused Python process without an interactive pdb shell.
---

# apdb

## Overview

`apdb` is a Python debugger interface for coding agents. It keeps the target
program's call site close to `pdb`, but exposes debugger control through
newline-delimited JSON over TCP and the `apdb_cli` command.

## Quick Start

Add a breakpoint in the target process:

```python
import apdb

apdb.set_trace(port=8888)
```

When the process reaches that line it blocks, even if no client is connected.
Use the CLI from another shell or agent command:

```bash
apdb_cli ping --port 8888
apdb_cli state --port 8888
apdb_cli where --port 8888
apdb_cli locals --port 8888
apdb_cli eval 'some_expression' --port 8888
apdb_cli next --port 8888
apdb_cli step --port 8888
apdb_cli continue --port 8888
```

## Workflow

1. Add `apdb.set_trace(port=8888)` near the code path to inspect.
2. Run the target program until it blocks.
3. Check liveness with `apdb_cli ping --port 8888`.
4. Read `state`, `where`, and `locals` before evaluating expressions.
5. Use `eval` for expressions only. Use `exec-file` for multi-statement snippets
   when the installed `apdb` version supports it.
6. Release the process with `continue`, `next`, `step`, or `quit`.

## Command Notes

- Default host is `127.0.0.1`.
- There is no authentication. Do not bind to public interfaces unless the user
  explicitly accepts that risk.
- CLI responses are JSON. Parse them instead of scraping terminal formatting.
- Prefer a fixed port supplied by the user or repo docs. Use `8888` for examples.
- If response text may contain multiline strings, Unicode, or shell-sensitive
  characters, prefer CLI output-to-file support when available.

## Common Mistakes

- Do not assume an interactive pdb prompt exists.
- Do not use `eval` for statements such as assignments, imports, loops, or
  function definitions.
- Do not forget to send `continue` or another release command; the target
  process stays blocked until released.
- Do not paste API tokens, secrets, or credentials into `eval` or command logs.
