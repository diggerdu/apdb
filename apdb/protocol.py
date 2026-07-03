import json


class ProtocolError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def loads_request(line):
    request = loads_json_line(line)
    if not isinstance(request, dict):
        raise ProtocolError("invalid_request", "request must be a JSON object")
    if not request.get("cmd"):
        raise ProtocolError("missing_command", "request must include cmd")
    if not isinstance(request["cmd"], str):
        raise ProtocolError("invalid_command", "cmd must be a string")
    return request


def loads_json_line(line):
    try:
        payload = json.loads(line.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ProtocolError("invalid_encoding", str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError("invalid_json", str(exc)) from exc
    return payload


def dumps_response(response):
    return (json.dumps(response, sort_keys=True) + "\n").encode("utf-8")


def ok_response(request, result):
    return {"id": request.get("id"), "ok": True, "result": result}


def error_response(request, code, message):
    return {
        "id": request.get("id"),
        "ok": False,
        "error": {"code": code, "message": message},
    }
