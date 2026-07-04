import pathlib
import re
import unittest


class APDBSkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_examples_are_valid(self):
        path = pathlib.Path("skills/apdb/SKILL.md")
        text = path.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: apdb", text)
        self.assertRegex(text, r"description: Use when .+apdb_cli")
        self.assertIn("apdb.set_trace(port=8888)", text)
        self.assertIn("apdb_cli ping --port 8888", text)
        self.assertIn("apdb_cli exec-file snippet.py --port 8888", text)
        self.assertIn("--output result.json", text)
        self.assertNotIn("44" + "44", text)

    def test_skill_only_documents_shipped_commands(self):
        text = pathlib.Path("skills/apdb/SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("Install This Skill", text)
        self.assertNotIn("skills install", text)

    def test_skill_description_stays_under_limit(self):
        text = pathlib.Path("skills/apdb/SKILL.md").read_text(encoding="utf-8")
        description = re.search(r"^description: (.+)$", text, re.MULTILINE).group(1)

        self.assertLessEqual(len(description), 1024)

    def test_packaged_skill_copy_matches_repo_skill(self):
        repo_skill = pathlib.Path("skills/apdb/SKILL.md").read_text(encoding="utf-8")
        packaged_skill = pathlib.Path("apdb/bundled_skill/apdb/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(packaged_skill, repo_skill)


if __name__ == "__main__":
    unittest.main()
