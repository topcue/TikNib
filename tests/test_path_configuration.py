import unittest

from config.path_variables import windows_to_wsl_path, wsl_to_windows_path


class PathConfigurationTests(unittest.TestCase):
    def test_wsl_to_windows_mapping_uses_explicit_prefixes(self):
        self.assertEqual(
            wsl_to_windows_path(
                "/wsl/workspace/data/sample.elf",
                "/wsl/workspace",
                "D:/research/workspace",
            ),
            "D:/research/workspace/data/sample.elf",
        )

    def test_windows_to_wsl_mapping_is_case_insensitive(self):
        self.assertEqual(
            windows_to_wsl_path(
                r"d:\Research\Workspace\data\sample.elf",
                "/wsl/workspace",
                "D:/research/workspace",
            ),
            "/wsl/workspace/data/sample.elf",
        )

    def test_unrelated_path_is_not_rewritten(self):
        self.assertEqual(
            wsl_to_windows_path(
                "/tmp/sample.elf", "/wsl/workspace", "D:/research/workspace"
            ),
            "/tmp/sample.elf",
        )


if __name__ == "__main__":
    unittest.main()
