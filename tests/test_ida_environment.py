import os
import tempfile
import unittest
from unittest import mock

from tiknib import ida_environment


class IdaEnvironmentTests(unittest.TestCase):
    def test_accepts_legacy_executable_names(self):
        with tempfile.TemporaryDirectory() as directory:
            ida_dir = os.path.join(directory, "IDA")
            os.mkdir(ida_dir)
            for name in ("idal.exe", "idal64.exe"):
                with open(os.path.join(ida_dir, name), "wb"):
                    pass

            script_path = os.path.join(directory, "fetch.py")
            python_dll = os.path.join(directory, "python.dll")
            cmd_exe = os.path.join(directory, "cmd.exe")
            reg_exe = os.path.join(directory, "reg.exe")
            for path in (script_path, python_dll, cmd_exe, reg_exe):
                with open(path, "wb"):
                    pass

            completed = mock.Mock(returncode=0)
            with mock.patch.object(ida_environment, "WSL_PREFIX", directory), \
                mock.patch.object(ida_environment, "WIN_PREFIX", "C:/workspace"), \
                mock.patch.object(
                    ida_environment, "IDA_PYTHON_DLL", python_dll
                ), mock.patch.object(
                    ida_environment, "WINDOWS_CMD_EXE", cmd_exe
                ), mock.patch.object(
                    ida_environment, "WINDOWS_REG_EXE", reg_exe
                ), mock.patch.object(
                    ida_environment, "query_ida_python_target", return_value=python_dll
                ), mock.patch.object(
                    ida_environment.subprocess, "run", return_value=completed
                ):
                errors, warnings, _ = ida_environment.check_ida_environment(
                    ida_dir, script_path
                )

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_registry_query_failure_returns_none(self):
        with mock.patch.object(
            ida_environment.subprocess, "run", side_effect=OSError("no interop")
        ):
            self.assertIsNone(ida_environment.query_ida_python_target("reg.exe"))


if __name__ == "__main__":
    unittest.main()
