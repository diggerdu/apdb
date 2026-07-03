import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

from apdb.cli import send_command


def unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_ping(port, timeout=5.0):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            return send_command("127.0.0.1", port, {"id": 1, "cmd": "ping"}, timeout=0.2)
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    raise AssertionError(f"apdb service did not become ready: {last_error}")


class IntegrationTests(unittest.TestCase):
    def start_debuggee(self, source):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        script = os.path.join(tempdir.name, "debuggee.py")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(source)

        env = os.environ.copy()
        repo_root = os.path.dirname(os.path.dirname(__file__))
        env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
        process = subprocess.Popen(
            [sys.executable, script],
            cwd=tempdir.name,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(self.cleanup_process, process)
        return process

    def cleanup_process(self, process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    def test_set_trace_serves_state_locals_eval_and_continue(self):
        port = unused_port()
        source = textwrap.dedent(
            f"""
            import apdb

            def main():
                answer = 41
                print("before", flush=True)
                apdb.set_trace(port={port})
                print("after", answer + 1, flush=True)

            main()
            """
        )
        process = self.start_debuggee(source)

        self.assertEqual(process.stdout.readline().strip(), "before")
        self.assertEqual(wait_for_ping(port)["result"], {"status": "online"})

        state = send_command("127.0.0.1", port, {"id": 2, "cmd": "state"}, timeout=1.0)
        self.assertTrue(state["ok"])
        self.assertEqual(state["result"]["status"], "paused")
        self.assertEqual(state["result"]["function"], "main")
        self.assertEqual(os.path.basename(state["result"]["file"]), "debuggee.py")

        locals_response = send_command(
            "127.0.0.1", port, {"id": 3, "cmd": "locals"}, timeout=1.0
        )
        self.assertEqual(locals_response["result"]["answer"], "41")

        eval_response = send_command(
            "127.0.0.1", port, {"id": 4, "cmd": "eval", "expr": "answer + 1"}, timeout=1.0
        )
        self.assertEqual(eval_response["result"]["repr"], "42")

        continue_response = send_command(
            "127.0.0.1", port, {"id": 5, "cmd": "continue"}, timeout=1.0
        )
        self.assertTrue(continue_response["ok"])
        self.assertEqual(continue_response["result"]["status"], "continuing")

        self.assertEqual(process.stdout.readline().strip(), "after 42")
        self.assertEqual(process.wait(timeout=2), 0)

    def test_unknown_command_returns_structured_error(self):
        port = unused_port()
        source = textwrap.dedent(
            f"""
            import apdb
            print("before", flush=True)
            apdb.set_trace(port={port})
            print("after", flush=True)
            """
        )
        process = self.start_debuggee(source)

        self.assertEqual(process.stdout.readline().strip(), "before")
        wait_for_ping(port)
        response = send_command("127.0.0.1", port, {"id": 9, "cmd": "bad"}, timeout=1.0)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "unknown_command")
        send_command("127.0.0.1", port, {"id": 10, "cmd": "continue"}, timeout=1.0)
        self.assertEqual(process.wait(timeout=2), 0)

    def test_next_releases_to_next_line_and_pauses_again(self):
        port = unused_port()
        source = textwrap.dedent(
            f"""
            import apdb

            def main():
                value = 1
                print("before", flush=True)
                apdb.set_trace(port={port})
                value = value + 1
                print("middle", value, flush=True)
                print("after", flush=True)

            main()
            """
        )
        process = self.start_debuggee(source)

        self.assertEqual(process.stdout.readline().strip(), "before")
        wait_for_ping(port)
        next_response = send_command(
            "127.0.0.1", port, {"id": 11, "cmd": "next"}, timeout=1.0
        )
        self.assertTrue(next_response["ok"])

        state = send_command("127.0.0.1", port, {"id": 12, "cmd": "state"}, timeout=2.0)
        self.assertEqual(state["result"]["status"], "paused")
        self.assertIn("value = value + 1", state["result"]["code"])

        send_command("127.0.0.1", port, {"id": 13, "cmd": "continue"}, timeout=1.0)
        self.assertEqual(process.stdout.readline().strip(), "middle 2")
        self.assertEqual(process.stdout.readline().strip(), "after")
        self.assertEqual(process.wait(timeout=2), 0)

    def test_step_enters_called_function_and_pauses_again(self):
        port = unused_port()
        source = textwrap.dedent(
            f"""
            import apdb

            def helper():
                marker = "inside"
                return marker

            def main():
                print("before", flush=True)
                apdb.set_trace(port={port})
                result = helper()
                print("after", result, flush=True)

            main()
            """
        )
        process = self.start_debuggee(source)

        self.assertEqual(process.stdout.readline().strip(), "before")
        wait_for_ping(port)
        step_response = send_command(
            "127.0.0.1", port, {"id": 14, "cmd": "step"}, timeout=1.0
        )
        self.assertTrue(step_response["ok"])

        state = send_command("127.0.0.1", port, {"id": 15, "cmd": "state"}, timeout=2.0)
        self.assertEqual(state["result"]["status"], "paused")
        self.assertIn("result = helper()", state["result"]["code"])

        step_into_response = send_command(
            "127.0.0.1", port, {"id": 16, "cmd": "step"}, timeout=1.0
        )
        self.assertTrue(step_into_response["ok"])
        state = send_command("127.0.0.1", port, {"id": 17, "cmd": "state"}, timeout=2.0)
        self.assertEqual(state["result"]["function"], "helper")

        send_command("127.0.0.1", port, {"id": 18, "cmd": "continue"}, timeout=1.0)
        self.assertEqual(process.stdout.readline().strip(), "after inside")
        self.assertEqual(process.wait(timeout=2), 0)


if __name__ == "__main__":
    unittest.main()
