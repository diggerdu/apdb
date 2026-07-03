import os
import pathlib
import subprocess
import tempfile
import unittest

from apdb import skill_installer


class SkillInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = pathlib.Path(self.tempdir.name)
        self.home = self.root / "home"
        self.codex_home = self.root / "codex-home"
        self.project = self.root / "project"
        self.home.mkdir()
        self.codex_home.mkdir()
        self.project.mkdir()

    def test_user_destinations(self):
        destinations = skill_installer.resolve_destinations(
            agent="all",
            scope="user",
            home=self.home,
            codex_home=self.codex_home,
            cwd=self.project,
        )

        self.assertEqual(
            destinations,
            [
                skill_installer.InstallDestination(
                    agent="codex", path=self.codex_home / "skills" / "apdb"
                ),
                skill_installer.InstallDestination(
                    agent="claude-code", path=self.home / ".claude" / "skills" / "apdb"
                ),
            ],
        )

    def test_global_scope_aliases_user(self):
        user = skill_installer.resolve_destinations(
            agent="codex",
            scope="user",
            home=self.home,
            codex_home=self.codex_home,
            cwd=self.project,
        )
        global_scope = skill_installer.resolve_destinations(
            agent="codex",
            scope="global",
            home=self.home,
            codex_home=self.codex_home,
            cwd=self.project,
        )

        self.assertEqual(global_scope, user)

    def test_project_destinations_use_current_directory_without_git(self):
        destinations = skill_installer.resolve_destinations(
            agent="all",
            scope="project",
            home=self.home,
            codex_home=self.codex_home,
            cwd=self.project,
        )

        self.assertEqual(
            destinations,
            [
                skill_installer.InstallDestination(
                    agent="codex", path=self.project / ".codex" / "skills" / "apdb"
                ),
                skill_installer.InstallDestination(
                    agent="claude-code", path=self.project / ".claude" / "skills" / "apdb"
                ),
            ],
        )

    def test_project_destinations_use_git_root_when_available(self):
        nested = self.project / "nested"
        nested.mkdir()
        subprocess.run(
            ["git", "init", "-q"],
            cwd=self.project,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        destinations = skill_installer.resolve_destinations(
            agent="codex",
            scope="project",
            home=self.home,
            codex_home=self.codex_home,
            cwd=nested,
        )

        self.assertEqual(
            destinations,
            [
                skill_installer.InstallDestination(
                    agent="codex", path=self.project.resolve() / ".codex" / "skills" / "apdb"
                ),
            ],
        )

    def test_install_copies_skill(self):
        destination = self.root / "install" / "apdb"

        result = skill_installer.install_to_destination(destination)

        self.assertEqual(result["status"], "installed")
        self.assertTrue((destination / "SKILL.md").exists())

    def test_install_existing_destination_fails_without_force(self):
        destination = self.root / "install" / "apdb"
        destination.mkdir(parents=True)

        with self.assertRaises(skill_installer.SkillInstallError) as context:
            skill_installer.install_to_destination(destination, force=False)

        self.assertEqual(context.exception.code, "destination_exists")

    def test_install_force_overwrites_existing_destination(self):
        destination = self.root / "install" / "apdb"
        destination.mkdir(parents=True)
        stale = destination / "stale.txt"
        stale.write_text("old", encoding="utf-8")

        result = skill_installer.install_to_destination(destination, force=True)

        self.assertEqual(result["status"], "installed")
        self.assertFalse(stale.exists())
        self.assertTrue((destination / "SKILL.md").exists())

    def test_install_skills_returns_json_ready_results(self):
        result = skill_installer.install_skills(
            agent="codex",
            scope="project",
            force=False,
            home=self.home,
            codex_home=self.codex_home,
            cwd=self.project,
        )

        self.assertEqual(result["status"], "installed")
        self.assertEqual(result["installed"][0]["agent"], "codex")
        self.assertTrue(os.path.isabs(result["installed"][0]["path"]))


if __name__ == "__main__":
    unittest.main()
