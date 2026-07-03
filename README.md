# apdb

`apdb` is an agent-friendly Python debugger inspired by `remote-pdb`.
It keeps the Python call site close to `pdb`, but exposes debugger control over
a newline-delimited JSON TCP API instead of a human interactive shell.

The runtime and CLI use only the Python standard library.

## Python API

```python
import apdb

answer = 41
apdb.set_trace(port=4444)
print(answer + 1)
```

`set_trace()` blocks the target process whether or not a client is connected.
The process resumes only after the TCP API receives a release command such as
`continue`, `next`, `step`, or `quit`.

By default, `apdb` binds to `127.0.0.1` and uses no authentication:

```python
apdb.set_trace(port=4444, host="127.0.0.1")
```

## CLI

The package installs `apdb_cli`:

```bash
apdb_cli ping --port 4444
apdb_cli state --port 4444
apdb_cli where --port 4444
apdb_cli locals --port 4444
apdb_cli eval 'answer + 1' --port 4444
apdb_cli next --port 4444
apdb_cli step --port 4444
apdb_cli continue --port 4444
```

The CLI prints one JSON response to stdout and exits nonzero for connection
failures or API errors.

## TCP API

The TCP API speaks newline-delimited JSON. Each request and response is one JSON
object followed by `\n`.

Request:

```json
{"id": 1, "cmd": "state"}
```

Response:

```json
{"id": 1, "ok": true, "result": {"status": "paused"}}
```

Supported v0 commands:

- `ping`
- `state`
- `where`
- `locals`
- `eval`
- `next`
- `step`
- `continue`
- `quit`

## Security

`apdb` has no authentication in v0. Debugger access can inspect and evaluate
code inside the target process. Bind to `127.0.0.1` unless you explicitly want
to expose that control surface.
