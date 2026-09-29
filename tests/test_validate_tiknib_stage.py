import os
import pickle
import tempfile
import unittest

from script.validate_tiknib_stage import validate


def function_record():
    return {
        "name": "main",
        "seg_name": ".text",
        "src_path": "/source/example/main.c",
        "src_file": "main.c",
        "src_line": 10,
        "abstract_args_type": ["int"],
        "abstract_ret_type": "int",
        "feature": {"cfg_size": 1},
    }


class ValidateTikNibStageTests(unittest.TestCase):
    def write_stage(self, directory, suffix, functions):
        binary = os.path.join(directory, "sample.elf")
        with open(binary + suffix, "wb") as pickle_file:
            pickle.dump(functions, pickle_file)
        return binary

    def test_feature_stage_accepts_complete_record(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = self.write_stage(
                directory, ".feature.pickle", [function_record()]
            )
            self.assertEqual(validate(binary, "feature"), ([], 1))

    def test_normalized_stage_rejects_embedded_windows_path(self):
        with tempfile.TemporaryDirectory() as directory:
            record = function_record()
            record["src_path"] = r"C:\source\example\main.c"
            binary = self.write_stage(directory, ".pickle", [record])
            errors, count = validate(binary, "normalized")
            self.assertEqual(count, 1)
            self.assertIn("function 0 retains a Windows path", errors)

    def test_typed_stage_requires_abstract_types(self):
        with tempfile.TemporaryDirectory() as directory:
            record = function_record()
            del record["abstract_ret_type"]
            binary = self.write_stage(directory, ".filtered.pickle", [record])
            errors, count = validate(binary, "typed")
            self.assertEqual(count, 1)
            self.assertIn("function 0 lacks abstract_ret_type", errors)


if __name__ == "__main__":
    unittest.main()
