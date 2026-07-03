# apdb Agent Debugger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v0 `apdb` package with `apdb.set_trace(port=...)`, a no-auth NDJSON TCP API, and a zero-dependency `apdb_cli` command.

**Architecture:** The package uses a small TCP server thread to receive newline-delimited JSON requests while the target thread is paused in `set_trace()`. A session object owns frame state, structured command responses, and release coordination. The CLI uses `argparse`, `socket`, and `json` to send one command and print one JSON response.

**Tech Stack:** Python standard library only for runtime and tests: `argparse`, `bdb`, `inspect`, `json`, `socket`, `socketserver`, `threading`, `traceback`, `unittest`, `subprocess`.

---

### Task 1: Protocol Helpers

**Files:**
- Create: `apdb/protocol.py`
- Test: `tests/test_protocol.py`

- [ ] **Step 1: Write failing tests** for encoding responses, decoding newline JSON requests, invalid JSON, and missing command validation.
- [ ] **Step 2: Run** `python3 -m unittest tests.test_protocol -v` and verify the module is missing or tests fail.
- [ ] **Step 3: Implement** `ProtocolError`, `loads_request()`, `dumps_response()`, `ok_response()`, and `error_response()`.
- [ ] **Step 4: Re-run** `python3 -m unittest tests.test_protocol -v` and verify it passes.

### Task 2: CLI Client

**Files:**
- Create: `apdb/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests** for request construction, one-command TCP exchange, JSON stdout, and connection failure exit status.
- [ ] **Step 2: Run** `python3 -m unittest tests.test_cli -v` and verify failure.
- [ ] **Step 3: Implement** `build_parser()`, `send_command()`, and `main()`.
- [ ] **Step 4: Re-run** `python3 -m unittest tests.test_cli -v` and verify it passes.

### Task 3: Debugger Session and TCP Server

**Files:**
- Create: `apdb/debugger.py`
- Create: `apdb/server.py`
- Modify: `apdb/__init__.py`
- Test: `tests/test_integration.py`

- [ ] **Step 1: Write failing integration tests** for `ping`, `state`, `locals`, `eval`, and `continue` against a subprocess paused in `apdb.set_trace(port=...)`.
- [ ] **Step 2: Run** `python3 -m unittest tests.test_integration -v` and verify failure.
- [ ] **Step 3: Implement** `AgentPdbSession`, `APDBTCPServer`, request handling, and public `set_trace()`.
- [ ] **Step 4: Re-run** `python3 -m unittest tests.test_integration -v` and verify it passes.

### Task 4: Packaging and Documentation

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `LICENSE`
- Test: package metadata through stdlib commands

- [ ] **Step 1: Add packaging** with project name `apdb` and console script `apdb_cli = apdb.cli:main`.
- [ ] **Step 2: Add README** with Python API and CLI examples.
- [ ] **Step 3: Add BSD-2-Clause license text suitable for a fork-style package.**
- [ ] **Step 4: Run** `python3 -m unittest discover -v` and `python3 -m compileall apdb tests`.
