# apdb Agent Debugger Design

Date: 2026-07-03

## Goal

`apdb` is a fork-style Python debugger package inspired by `remote-pdb`.
The package keeps the Python call site close to vanilla `pdb`, but replaces the
human-oriented interactive shell with a TCP API that coding agents can drive.

The PyPI package name is `apdb`.

## Public Python API

User code pauses execution with:

```python
import apdb

apdb.set_trace(port=8888)
```

`set_trace()` starts a no-auth TCP API service and blocks the target process.
The process stays blocked whether or not a client is connected. It only resumes
when a client sends a release debugger command, such as `continue`, `next`,
`step`, or `quit`.

The v0 API shape is:

```python
apdb.set_trace(port=8888, host="127.0.0.1", header=None)
```

Defaults and constraints:

- `host` defaults to `127.0.0.1`.
- `port` is required for v0.
- There is no authentication.
- Blocking behavior is always enabled.
- Runtime code uses only the Python standard library.

## CLI

The package installs a console command named `apdb_cli`.

Examples:

```bash
apdb_cli ping --port 8888
apdb_cli state --port 8888
apdb_cli where --port 8888
apdb_cli locals --port 8888
apdb_cli eval --port 8888 'some_expr'
apdb_cli next --port 8888
apdb_cli step --port 8888
apdb_cli continue --port 8888
```

The CLI is a thin wrapper around the TCP API. It is not an interactive shell in
v0. It prints JSON by default so that agents can parse results directly.

## TCP Protocol

The TCP service uses newline-delimited JSON over a plain TCP socket. Each
request is one JSON object ending in `\n`. Each response is one JSON object
ending in `\n`.

Example:

```json
{"id": 1, "cmd": "ping"}
{"id": 1, "ok": true, "result": {"status": "online"}}
```

Core v0 commands:

- `ping`: check whether the API service is online.
- `state`: return paused or running state plus current file, line, and function.
- `where`: return stack frames.
- `locals`: return local variables from the current frame.
- `eval`: evaluate an expression in the current frame.
- `next`: run pdb-style next and pause again.
- `step`: run pdb-style step and pause again.
- `continue`: resume the target process.
- `quit`: terminate the debugger session.

## Internal Architecture

Main modules:

```text
apdb/__init__.py        public API: set_trace and version
apdb/debugger.py        session lifecycle and pdb/bdb integration
apdb/protocol.py        request and response JSON helpers
apdb/server.py          TCP server
apdb/cli.py             argparse CLI wrapper
tests/                  stdlib unittest tests
```

`apdb.set_trace()` creates a debugger session object around `pdb.Pdb` and `bdb`
behavior. The target process enters a paused state at the caller frame. A TCP
server thread accepts CLI/API requests while the main thread remains blocked at
the breakpoint. Release commands coordinate back to the main thread, run one
debugger action, then either pause again or resume the program.

## Errors

The API returns structured errors instead of exposing raw CLI tracebacks:

- Invalid JSON returns a structured protocol error.
- Unknown commands return a structured command error.
- CLI connection failures exit nonzero.
- A port already in use raises a clear exception from `set_trace()`.
- `eval` exceptions return structured error text.

## Testing

The v0 test suite should cover:

- protocol request and response helpers
- CLI argument handling
- TCP `ping` and `state` integration
- breakpoint blocking and release behavior through a subprocess

The implementation and tests should run with the Python standard library only.
