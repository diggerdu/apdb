import pathlib
import tomllib
import unittest


class PackageMetadataTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
