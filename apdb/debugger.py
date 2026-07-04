import bdb
import ctypes
import linecache
import sys
import threading

from .protocol import error_response, ok_response
from .server import APDBTCPServer


RELEASE_COMMANDS = {"continue", "next", "step", "quit"}
HISTORY_TEXT_LIMIT = 200


class APDBError(RuntimeError):
    pass


class AgentPdbSession:
    def __init__(self, host, port, header=None):
        self.host = host
        self.port = port
        self.header = header
        self._condition = threading.Condition()
        self._release_event = threading.Event()
        self._server = None
        self._server_thread = None
        self._current_frame = None
        self._current_action = None
        self._done = False
        self._paused = False
        self._trace_mode = None
        self._next_frame = None
        self._skip_line = None
        self._history = []
        self._history_seq = 0
        self._history_lock = threading.Lock()

    def start(self):
        try:
            self._server = APDBTCPServer((self.host, self.port), self)
        except OSError as exc:
            raise APDBError(f"could not start apdb server on {self.host}:{self.port}: {exc}") from exc

        self._server_thread = threading.Thread(
            target=self._server.serve_forever,
            name=f"apdb:{self.host}:{self.port}",
            daemon=True,
        )
        self._server_thread.start()

    def close(self):
        self._done = True
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def pause(self, frame):
        with self._condition:
            self._current_frame = frame
            self._current_action = None
            self._paused = True
            self._release_event.clear()
            self._condition.notify_all()

        self._release_event.wait()

        with self._condition:
            self._paused = False
            return self._current_action

    def handle_request(self, request):
        cmd = request["cmd"]
        try:
            response = self._handle_request(request, cmd)
        except Exception as exc:
            response = error_response(request, "command_error", f"{type(exc).__name__}: {exc}")
        self._record_history(request, response)
        return response

    def _handle_request(self, request, cmd):
        if cmd == "ping":
            return ok_response(request, {"status": "online"})
        if cmd == "state":
            return ok_response(request, self._state())
        if cmd == "where":
            return ok_response(request, {"frames": self._stack()})
        if cmd == "locals":
            return ok_response(request, self._locals())
        if cmd == "history":
            return ok_response(request, {"entries": self._history_snapshot()})
        if cmd == "eval":
            return ok_response(request, self._eval(request.get("expr", "")))
        if cmd == "exec":
            return ok_response(request, self._exec(request.get("code", "")))
        if cmd in RELEASE_COMMANDS:
            return self._release(request, cmd)
        return error_response(request, "unknown_command", f"unknown command: {cmd}")

    def trace_dispatch(self, frame, event, arg):
        if self._done:
            return None
        if self._should_pause_for_trace(frame, event):
            action = self.pause(frame)
            return self._after_action(action, frame)
        return self.trace_dispatch

    def _release(self, request, action):
        with self._condition:
            self._current_action = action
            self._release_event.set()
        status = {
            "continue": "continuing",
            "next": "next",
            "step": "step",
            "quit": "quitting",
        }[action]
        return ok_response(request, {"status": status})

    def _history_snapshot(self):
        with self._history_lock:
            return [dict(entry) for entry in self._history]

    def _record_history(self, request, response):
        entry = {
            "seq": None,
            "id": request.get("id"),
            "cmd": request.get("cmd"),
            "ok": bool(response.get("ok")),
        }
        if request.get("cmd") == "eval":
            entry["expr"] = summarize_text(request.get("expr", ""))
        if request.get("cmd") == "exec":
            entry["code"] = summarize_text(request.get("code", ""))
        if not entry["ok"]:
            entry["error"] = response.get("error", {}).get("code")

        with self._history_lock:
            self._history_seq += 1
            entry["seq"] = self._history_seq
            self._history.append(entry)

    def _state(self):
        frame = self._current_frame
        result = {"status": "paused" if self._paused else "running"}
        if frame is not None:
            result.update(self._frame_info(frame, index=0))
        return result

    def _stack(self):
        frames = []
        frame = self._current_frame
        index = 0
        while frame is not None:
            frames.append(self._frame_info(frame, index=index))
            frame = frame.f_back
            index += 1
        return frames

    def _locals(self):
        frame = self._require_frame()
        return {name: safe_repr(value) for name, value in sorted(frame.f_locals.items())}

    def _eval(self, expr):
        if not expr:
            raise ValueError("eval command requires expr")
        frame = self._require_frame()
        value = eval(expr, frame.f_globals, frame.f_locals)
        return {"repr": safe_repr(value), "type": type(value).__name__}

    def _exec(self, code):
        if not code:
            raise ValueError("exec command requires code")
        frame = self._require_frame()
        exec(code, frame.f_globals, frame.f_locals)
        sync_frame_locals(frame)
        return {"status": "executed"}

    def _require_frame(self):
        if self._current_frame is None:
            raise RuntimeError("debugger is not paused at a frame")
        return self._current_frame

    def _frame_info(self, frame, index):
        filename = frame.f_code.co_filename
        line = linecache.getline(filename, frame.f_lineno).strip()
        return {
            "index": index,
            "file": filename,
            "line": frame.f_lineno,
            "function": frame.f_code.co_name,
            "code": line,
        }

    def _should_pause_for_trace(self, frame, event):
        if event != "line":
            return False
        if self._skip_line == (frame, frame.f_lineno):
            self._skip_line = None
            return False
        if self._trace_mode == "step":
            return True
        if self._trace_mode == "next":
            return frame is self._next_frame
        return False

    def _after_action(self, action, frame):
        if action == "continue":
            self.close()
            sys.settrace(None)
            return None
        if action == "quit":
            self.close()
            sys.settrace(None)
            raise bdb.BdbQuit()
        if action in {"next", "step"}:
            self._trace_mode = action
            self._next_frame = frame
            self._skip_line = (frame, frame.f_lineno)
            frame.f_trace = self.trace_dispatch
            sys.settrace(self.trace_dispatch)
            return self.trace_dispatch
        self.close()
        sys.settrace(None)
        return None


def safe_repr(value):
    try:
        return repr(value)
    except Exception:
        return f"<unrepresentable {type(value).__name__}>"


def summarize_text(value, limit=HISTORY_TEXT_LIMIT):
    if not isinstance(value, str):
        value = str(value)
    if len(value) <= limit:
        return value
    return value[:limit] + "...<truncated>"


def sync_frame_locals(frame):
    try:
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(1))
    except AttributeError:
        pass


def set_trace(host="127.0.0.1", port=None, header=None):
    if port is None:
        raise TypeError("apdb.set_trace() missing required keyword argument: 'port'")

    frame = sys._getframe().f_back
    session = AgentPdbSession(host=host, port=port, header=header)
    session.start()
    action = session.pause(frame)
    return session._after_action(action, frame)
