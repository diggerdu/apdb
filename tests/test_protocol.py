import json
import unittest

from apdb.protocol import (
    ProtocolError,
    dumps_response,
    error_response,
    loads_request,
    ok_response,
)


class ProtocolTests(unittest.TestCase):
    def test_loads_request_accepts_json_object_with_command(self):
        request = loads_request(b'{"id": 7, "cmd": "ping"}\n')

        self.assertEqual(request, {"id": 7, "cmd": "ping"})

    def test_loads_request_rejects_invalid_json(self):
        with self.assertRaises(ProtocolError) as context:
            loads_request(b"{not-json}\n")

        self.assertEqual(context.exception.code, "invalid_json")

    def test_loads_request_rejects_missing_command(self):
        with self.assertRaises(ProtocolError) as context:
            loads_request(b'{"id": 1}\n')

        self.assertEqual(context.exception.code, "missing_command")

    def test_dumps_response_writes_newline_delimited_json(self):
        payload = dumps_response({"id": 1, "ok": True, "result": {"status": "online"}})

        self.assertTrue(payload.endswith(b"\n"))
        self.assertEqual(
            json.loads(payload.decode("utf-8")),
            {"id": 1, "ok": True, "result": {"status": "online"}},
        )

    def test_ok_response_preserves_request_id(self):
        response = ok_response({"id": "abc", "cmd": "ping"}, {"status": "online"})

        self.assertEqual(
            response,
            {"id": "abc", "ok": True, "result": {"status": "online"}},
        )

    def test_error_response_preserves_request_id(self):
        response = error_response({"id": 3}, "unknown_command", "unknown command: nope")

        self.assertEqual(
            response,
            {
                "id": 3,
                "ok": False,
                "error": {"code": "unknown_command", "message": "unknown command: nope"},
            },
        )


if __name__ == "__main__":
    unittest.main()
