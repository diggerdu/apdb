import contextlib
import io
import json
import socket
import socketserver
import threading
import unittest

from apdb import cli


class OneShotHandler(socketserver.StreamRequestHandler):
    response = {"id": 1, "ok": True, "result": {"status": "online"}}
    seen_request = None

    def handle(self):
        line = self.rfile.readline()
        type(self).seen_request = json.loads(line.decode("utf-8"))
        self.wfile.write((json.dumps(type(self).response) + "\n").encode("utf-8"))


class CLITests(unittest.TestCase):
    def run_server(self):
        server = socketserver.TCPServer(("127.0.0.1", 0), OneShotHandler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        return server, thread

    def test_send_command_exchanges_one_ndjson_request(self):
        server, thread = self.run_server()
        host, port = server.server_address

        response = cli.send_command(host, port, {"id": 1, "cmd": "ping"}, timeout=1.0)
        thread.join(timeout=1.0)

        self.assertEqual(response, OneShotHandler.response)
        self.assertEqual(OneShotHandler.seen_request, {"id": 1, "cmd": "ping"})

    def test_main_prints_json_response(self):
        server, thread = self.run_server()
        host, port = server.server_address
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = cli.main(["ping", "--host", host, "--port", str(port)])
        thread.join(timeout=1.0)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), OneShotHandler.response)

    def test_main_returns_nonzero_when_connection_fails(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            host, port = sock.getsockname()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = cli.main(["ping", "--host", host, "--port", str(port)])

        self.assertEqual(exit_code, 2)
        self.assertIn("connection failed", stderr.getvalue())

    def test_eval_command_sends_expression(self):
        server, thread = self.run_server()
        host, port = server.server_address
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = cli.main(["eval", "x + 1", "--host", host, "--port", str(port)])
        thread.join(timeout=1.0)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            OneShotHandler.seen_request,
            {"id": 1, "cmd": "eval", "expr": "x + 1"},
        )


if __name__ == "__main__":
    unittest.main()
