import ast
import os
import unittest
from unittest import mock

from config.path_variables import IDA_POOL_SIZE
from tiknib.utils import decode_string_literal, parse_fname, parse_source_path
from tiknib.idascript import IDAScript, resolve_ida_executable
from script.handle_pickle import process_recursive


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class IDAScriptTests(unittest.TestCase):
    def test_default_pool_size_comes_from_configuration(self):
        self.assertEqual(IDAScript().pool_size, IDA_POOL_SIZE)

    def test_legacy_ida_executable_is_supported(self):
        with mock.patch("tiknib.idascript.os.path.exists") as exists:
            exists.side_effect = lambda path: path.endswith("idal64.exe")
            self.assertTrue(
                resolve_ida_executable("C:/IDA", is_64_bit=True).endswith(
                    "idal64.exe"
                )
            )


class SourcePathTests(unittest.TestCase):
    def test_official_binkit_source_path(self):
        path = "/build/coreutils-8.32_gcc-8.2.0_x86_64_O0_normal/src/test.c"
        self.assertEqual(parse_source_path(path), os.path.normpath("src/test.c"))

    def test_binforge_source_path_without_option_suffix(self):
        path = "/build/coreutils_gcc-13.3.0_x86_64_O0/src/lbracket.c"
        self.assertEqual(parse_source_path(path), os.path.normpath("src/lbracket.c"))

    def test_windows_source_path(self):
        path = r"C:\build\coreutils_gcc-13.3.0_x86_64_O0\lib\hash.c"
        self.assertEqual(parse_source_path(path), os.path.normpath("lib/hash.c"))

    def test_unrecognized_source_path(self):
        self.assertEqual(parse_source_path("/usr/include/stdio.h"), "")

    def test_binary_filename_parser_is_unchanged(self):
        parsed = parse_fname("coreutils_gcc-13.3.0_x86_64_Ofast_b2sum.elf")
        self.assertEqual(
            parsed,
            ("coreutils", "gcc-13.3.0", "x86_64", "Ofast", "b2sum.elf"),
        )


class StringLiteralTests(unittest.TestCase):
    def test_ida_bytes_are_decoded(self):
        self.assertEqual(decode_string_literal(b"hello\xff"), "hello\u00ff")

    def test_existing_text_is_preserved(self):
        value = "already text"
        self.assertIs(decode_string_literal(value), value)

    def test_path_normalization_does_not_corrupt_escaped_strings(self):
        values = [r"\\n", r"\\r", r"\\\\", "format\\value"]
        found, normalized = process_recursive(values[:], replace_flag=True)
        self.assertEqual(found, [])
        self.assertEqual(normalized, values)

    def test_path_normalization_still_rewrites_windows_paths(self):
        value = r"D:\research\workspace\storage\binary.elf"
        with mock.patch(
            "script.handle_pickle.WIN_PREFIX", "D:/research/workspace"
        ), mock.patch(
            "script.handle_pickle.WSL_PREFIX", "/wsl/workspace"
        ):
            found, normalized = process_recursive(value, replace_flag=True)
        self.assertEqual(found, [value])
        self.assertEqual(
            normalized, "/wsl/workspace/storage/binary.elf"
        )


class BasicBlockAggregationTests(unittest.TestCase):
    def _assert_aggregation_is_inside_basic_block_loop(self, relative_path):
        path = os.path.join(ROOT_DIR, relative_path)
        with open(path, "r") as source_file:
            tree = ast.parse(source_file.read(), filename=path)

        loops = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.For)
            and isinstance(node.target, ast.Name)
            and node.target.id == "bb"
        ]
        self.assertTrue(loops, "basic-block loop was not found")

        aggregated = set()
        for loop in loops:
            for node in ast.walk(loop):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                owner = node.func.value
                if (
                    node.func.attr == "extend"
                    and isinstance(owner, ast.Name)
                    and owner.id in {"func_strings", "func_consts"}
                ):
                    aggregated.add(owner.id)
        self.assertEqual(aggregated, {"func_strings", "func_consts"})

    def test_ida_75_aggregates_each_basic_block(self):
        self._assert_aggregation_is_inside_basic_block_loop(
            "tiknib/ida/fetch_funcdata_v7.5.py"
        )

    def test_legacy_ida_aggregates_each_basic_block(self):
        self._assert_aggregation_is_inside_basic_block_loop(
            "tiknib/ida/fetch_funcdata.py"
        )


if __name__ == "__main__":
    unittest.main()
