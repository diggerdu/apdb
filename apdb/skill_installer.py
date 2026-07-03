import dataclasses
import os
import pathlib
import shutil
import subprocess


SUPPORTED_AGENTS = ("codex", "claude-code")
SUPPORTED_SCOPES = ("user", "global", "project")
SKILL_NAME = "apdb"


class SkillInstallError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclasses.dataclass(frozen=True)
class InstallDestination:
    agent: str
    path: pathlib.Path


def resolve_destinations(agent, scope, home=None, codex_home=None, cwd=None):
    normalized_scope = normalize_scope(scope)
    agents = normalize_agents(agent)
    home_path = pathlib.Path(home if home is not None else pathlib.Path.home()).expanduser()
    codex_home_path = pathlib.Path(
        codex_home if codex_home is not None else os.environ.get("CODEX_HOME", home_path / ".codex")
    ).expanduser()
    cwd_path = pathlib.Path(cwd if cwd is not None else pathlib.Path.cwd()).resolve()
    project_root = find_project_root(cwd_path)

    destinations = []
    for agent_name in agents:
        if agent_name == "codex":
            base = codex_home_path if normalized_scope == "user" else project_root / ".codex"
        elif agent_name == "claude-code":
            base = home_path / ".claude" if normalized_scope == "user" else project_root / ".claude"
        else:
            raise SkillInstallError("unsupported_agent", f"unsupported agent: {agent_name}")
        destinations.append(InstallDestination(agent=agent_name, path=base / "skills" / SKILL_NAME))
    return destinations


def install_skills(agent, scope, force=False, home=None, codex_home=None, cwd=None):
    installed = []
    for destination in resolve_destinations(
        agent=agent, scope=scope, home=home, codex_home=codex_home, cwd=cwd
    ):
        result = install_to_destination(destination.path, force=force)
        installed.append({"agent": destination.agent, "path": str(destination.path), **result})
    return {"status": "installed", "installed": installed}


def install_to_destination(destination, force=False):
    destination = pathlib.Path(destination)
    source = bundled_skill_path()
    if destination.exists():
        if not force:
            raise SkillInstallError(
                "destination_exists",
                f"skill already exists at {destination}; pass --force to overwrite",
            )
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    return {"status": "installed"}


def bundled_skill_path():
    path = pathlib.Path(__file__).parent / "bundled_skill" / SKILL_NAME
    if not (path / "SKILL.md").exists():
        raise SkillInstallError("missing_bundled_skill", f"bundled skill not found at {path}")
    return path


def normalize_scope(scope):
    if scope not in SUPPORTED_SCOPES:
        raise SkillInstallError("unsupported_scope", f"unsupported scope: {scope}")
    return "user" if scope == "global" else scope


def normalize_agents(agent):
    if agent == "all":
        return list(SUPPORTED_AGENTS)
    if agent not in SUPPORTED_AGENTS:
        raise SkillInstallError("unsupported_agent", f"unsupported agent: {agent}")
    return [agent]


def find_project_root(cwd):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return cwd
    return pathlib.Path(result.stdout.strip()).resolve()
