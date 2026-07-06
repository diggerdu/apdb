import pathlib
import tomllib
import unittest

import apdb


class PackageMetadataTests(unittest.TestCase):
    def test_readme_uses_user_facing_language(self):
        readme = pathlib.Path("README.md").read_text(encoding="utf-8")

        self.assertNotIn("v0", readme)
        self.assertNotIn("internal", readme.lower())
        self.assertNotIn("convention", readme.lower())

    def test_project_urls_point_to_github(self):
        metadata = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(
            metadata["project"]["urls"],
            {
                "Homepage": "https://github.com/diggerdu/apdb",
                "Repository": "https://github.com/diggerdu/apdb",
                "Issues": "https://github.com/diggerdu/apdb/issues",
            },
        )

    def test_package_version_matches_project_metadata(self):
        metadata = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(apdb.__version__, metadata["project"]["version"])


if __name__ == "__main__":
    unittest.main()
