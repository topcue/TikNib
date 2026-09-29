import os
import pickle
import tempfile
import unittest

from script.validate_ida_outputs import validate_binary, validate_pickle


def valid_function():
    string = [0x10, "hello", 0, 0x20]
    return {
        "name": "main",
        "bin_path": "/tmp/sample.elf",
        "strings": [string],
        "consts": [7],
        "bb_data": [{"strings": [string], "consts": [7]}],
    }


class ValidateIDAOutputsTests(unittest.TestCase):
    def test_valid_pickle(self):
        with tempfile.NamedTemporaryFile() as pickle_file:
            pickle.dump([valid_function()], pickle_file)
            pickle_file.flush()
            self.assertEqual(validate_pickle(pickle_file.name), [])

    def test_detects_basic_block_aggregation_mismatch(self):
        function = valid_function()
        function["consts"] = []
        with tempfile.NamedTemporaryFile() as pickle_file:
            pickle.dump([function], pickle_file)
            pickle_file.flush()
            self.assertIn(
                "function 0 has inconsistent constants",
                validate_pickle(pickle_file.name),
            )

    def test_detects_missing_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = os.path.join(directory, "sample.elf")
            with open(binary, "wb") as binary_file:
                binary_file.write(b"ELF")
            errors = validate_binary(binary)
            self.assertTrue(any(".done" in error for error in errors))
            self.assertTrue(any(".pickle" in error for error in errors))
            self.assertTrue(any("IDA database" in error for error in errors))

    def test_output_log_can_be_made_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = os.path.join(directory, "sample.elf")
            for suffix in ("", ".done", ".idb"):
                with open(binary + suffix, "wb"):
                    pass
            with open(binary + ".pickle", "wb") as pickle_file:
                pickle.dump([valid_function()], pickle_file)

            self.assertTrue(
                any(
                    ".output" in error
                    for error in validate_binary(binary)
                )
            )
            self.assertEqual(validate_binary(binary, require_log=False), [])

    def test_malformed_basic_blocks_are_reported(self):
        function = valid_function()
        function["bb_data"] = None
        with tempfile.NamedTemporaryFile() as pickle_file:
            pickle.dump([function], pickle_file)
            pickle_file.flush()
            self.assertIn(
                "function 0 has malformed basic-block data",
                validate_pickle(pickle_file.name),
            )

    def test_malformed_basic_block_values_are_reported(self):
        function = valid_function()
        function["bb_data"][0]["strings"] = None
        with tempfile.NamedTemporaryFile() as pickle_file:
            pickle.dump([function], pickle_file)
            pickle_file.flush()
            self.assertIn(
                "function 0 has malformed basic-block strings or constants",
                validate_pickle(pickle_file.name),
            )


if __name__ == "__main__":
    unittest.main()
