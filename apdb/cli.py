import argparse
import json
import socket
import sys

from .protocol import dumps_response, loads_json_line
from .skill_installer import SkillInstallError, install_skills


DEFAULT_HOST = "127.0.0.1"
DEFAULT_TIMEOUT = 2.0


def build_parser():
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--host", default=DEFAULT_HOST)
    shared.add_argument("--port", type=int, required=True)
    shared.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    parser = argparse.ArgumentParser(prog="apdb_cli")
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    for name in ("ping", "state", "where", "locals", "next", "step", "continue", "quit"):
        subparsers.add_parser(name, parents=[shared])

    eval_parser = subparsers.add_parser("eval", parents=[shared])
    eval_parser.add_argument("expr")

    skills_parser = subparsers.add_parser("skills")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_cmd", required=True)
    install_parser = skills_subparsers.add_parser("install")
    install_parser.add_argument("--agent", choices=["codex", "claude-code", "all"], required=True)
    install_parser.add_argument("--scope", choices=["user", "global", "project"], required=True)
    install_parser.add_argument("--force", action="store_true")
    return parser


def make_request(args):
    request = {"id": 1, "cmd": args.cmd}
    if args.cmd == "eval":
        request["expr"] = args.expr
    return request


def send_command(host, port, request, timeout=DEFAULT_TIMEOUT):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(dumps_response(request))
        with sock.makefile("rb") as reader:
            return loads_json_line(reader.readline())


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "skills":
        return main_skills(args)

    try:
        response = send_command(args.host, args.port, make_request(args), args.timeout)
    except OSError as exc:
        print(f"connection failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(response, sort_keys=True))
    return 0 if response.get("ok") else 1


def main_skills(args):
    if args.skills_cmd != "install":
        response = {"ok": False, "error": {"code": "unknown_command", "message": args.skills_cmd}}
        print(json.dumps(response, sort_keys=True))
        return 1
    try:
        result = install_skills(agent=args.agent, scope=args.scope, force=args.force)
    except SkillInstallError as exc:
        response = {"ok": False, "error": {"code": exc.code, "message": exc.message}}
        print(json.dumps(response, sort_keys=True))
        return 1

    response = {"ok": True, **result}
    print(json.dumps(response, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
