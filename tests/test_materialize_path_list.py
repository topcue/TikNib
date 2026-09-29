import os
import tempfile
import unittest

from script.materialize_path_list import materialize


class MaterializePathListTests(unittest.TestCase):
    def test_resolves_relative_files(self):
        with tempfile.TemporaryDirectory() as directory:
            package = os.path.join(directory, "package")
            os.mkdir(package)
            binary = os.path.join(package, "sample.elf")
            with open(binary, "wb"):
                pass
            manifest = os.path.join(directory, "manifest.txt")
            with open(manifest, "w") as manifest_file:
                manifest_file.write("package/sample.elf\n")

            paths, errors = materialize(manifest, directory)
            self.assertEqual(paths, [binary])
            self.assertEqual(errors, [])

    def test_rejects_absolute_and_parent_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = os.path.join(directory, "manifest.txt")
            with open(manifest, "w") as manifest_file:
                manifest_file.write(
                    "/tmp/sample.elf\n../sample.elf\nC:/data/sample.elf\n"
                )

            paths, errors = materialize(manifest, directory)
            self.assertEqual(paths, [])
            self.assertEqual(len(errors), 3)


if __name__ == "__main__":
    unittest.main()
