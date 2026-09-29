"""Read-only checks for the WSL-to-Windows IDA execution environment."""

import os
import re
import subprocess

from config.path_variables import (
    IDA_PYTHON_DLL,
    WINDOWS_CMD_EXE,
    WINDOWS_REG_EXE,
    WIN_PREFIX,
    WSL_PREFIX,
    windows_to_wsl_path,
)


PYTHON_TARGET_RE = re.compile(
    rb"Python3TargetDLL\s+REG_SZ\s+([^\r\n]+)", re.IGNORECASE
)


def _same_windows_path(left, right):
    normalize = lambda value: value.replace("\\", "/").rstrip("/").lower()
    return normalize(left) == normalize(right)


def query_ida_python_target(reg_exe=WINDOWS_REG_EXE):
    """Return IDA's configured Python3 DLL without changing the registry."""
    try:
        result = subprocess.run(
            [
                reg_exe,
                "query",
                r"HKCU\Software\Hex-Rays\IDA",
                "/v",
                "Python3TargetDLL",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    match = PYTHON_TARGET_RE.search(result.stdout + result.stderr)
    if result.returncode != 0 or match is None:
        return None
    return match.group(1).decode("utf-8", errors="replace").strip()


def check_ida_environment(idapath, idc):
    """Return ``(errors, warnings, details)`` for the configured environment."""
    errors = []
    warnings = []
    details = {}

    if not idapath:
        errors.append("IDA install_path is not configured")
    else:
        details["ida_path"] = idapath
        # IDA 7.4 and newer use idat; older supported releases use idal.
        for bitness, executables in (
            ("32-bit", ("idat.exe", "idal.exe")),
            ("64-bit", ("idat64.exe", "idal64.exe")),
        ):
            paths = [os.path.join(idapath, name) for name in executables]
            if not any(os.path.isfile(path) for path in paths):
                errors.append(
                    "missing {} IDA executable (tried: {})".format(
                        bitness, ", ".join(paths)
                    )
                )

    if not WSL_PREFIX or not WIN_PREFIX:
        errors.append("paths.wsl_prefix and paths.windows_prefix must be configured")
    elif not os.path.isdir(WSL_PREFIX):
        errors.append("WSL-visible workspace does not exist: {}".format(WSL_PREFIX))
    else:
        details["path_mapping"] = "{} -> {}".format(WSL_PREFIX, WIN_PREFIX)

    if not idc:
        errors.append("IDA script_path is not configured")
    else:
        wsl_script = windows_to_wsl_path(idc)
        if not os.path.isabs(wsl_script):
            wsl_script = os.path.abspath(wsl_script)
        details["ida_script"] = idc
        if not os.path.isfile(wsl_script):
            errors.append(
                "IDA script is not visible through the configured mapping: {}"
                .format(idc)
            )

    if not os.path.isfile(WINDOWS_CMD_EXE):
        errors.append("missing Windows command launcher: {}".format(WINDOWS_CMD_EXE))
    else:
        try:
            interop = subprocess.run(
                [WINDOWS_CMD_EXE, "/c", "exit", "0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            interop = None
        if interop is None or interop.returncode != 0:
            errors.append("Windows executable interop is unavailable")

    if IDA_PYTHON_DLL:
        details["expected_python_dll"] = IDA_PYTHON_DLL
        dll_wsl_path = windows_to_wsl_path(IDA_PYTHON_DLL)
        if not os.path.isfile(dll_wsl_path):
            errors.append(
                "configured IDA Python DLL is not visible from WSL: {}"
                .format(IDA_PYTHON_DLL)
            )
        if not os.path.isfile(WINDOWS_REG_EXE):
            errors.append("missing Windows registry tool: {}".format(WINDOWS_REG_EXE))
        else:
            current_target = query_ida_python_target()
            details["current_python_dll"] = current_target or "<not found>"
            if current_target is None:
                errors.append("cannot read IDA Python3TargetDLL from the registry")
            elif not _same_windows_path(current_target, IDA_PYTHON_DLL):
                errors.append(
                    "IDA Python runtime mismatch: expected {!r}, found {!r}".format(
                        IDA_PYTHON_DLL, current_target
                    )
                )
    else:
        warnings.append(
            "ida.python_dll is not configured; the shared IDA Python runtime "
            "cannot be verified"
        )

    return errors, warnings, details
