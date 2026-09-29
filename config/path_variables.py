"""Machine-local configuration for the TikNib reproduction environment.

Tracked code reads ``config/local.ini`` (ignored by Git) and then applies
environment-variable overrides. This keeps workstation paths out of the
repository while preserving the historical constants imported by helpers.
"""

import configparser
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "local.ini"
CONFIG_PATH = Path(os.environ.get("TIKNIB_CONFIG", str(DEFAULT_CONFIG_PATH)))

_config = configparser.ConfigParser()
if CONFIG_PATH.is_file():
    _config.read(str(CONFIG_PATH))


def _get(section, option, environment, default=""):
    if environment in os.environ:
        return os.environ[environment]
    return _config.get(section, option, fallback=default).strip()


def _get_int(section, option, environment, default):
    value = _get(section, option, environment, str(default))
    try:
        return int(value)
    except ValueError:
        raise ValueError("{} must be an integer, got {!r}".format(environment, value))


# Compatibility names used throughout the original TikNib helpers.
IDA_PATH = _get("ida", "install_path", "TIKNIB_IDA_PATH")
IDA_FETCH_FUNCDATA = _get("ida", "script_path", "TIKNIB_IDA_SCRIPT")
IDA_PYTHON_DLL = _get("ida", "python_dll", "TIKNIB_IDA_PYTHON_DLL")
IDA_POOL_SIZE = _get_int("ida", "pool_size", "TIKNIB_IDA_POOL_SIZE", 1)
if IDA_POOL_SIZE < 1:
    raise ValueError("TIKNIB_IDA_POOL_SIZE must be at least 1")

WSL_PREFIX = _get("paths", "wsl_prefix", "TIKNIB_WSL_PREFIX")
WIN_PREFIX = _get("paths", "windows_prefix", "TIKNIB_WINDOWS_PREFIX")
BINKIT_DATASET = _get("paths", "dataset_root", "TIKNIB_DATASET_ROOT")

WINDOWS_CMD_EXE = _get(
    "windows", "cmd_exe", "TIKNIB_WINDOWS_CMD", "/mnt/c/Windows/System32/cmd.exe"
)
WINDOWS_REG_EXE = _get(
    "windows", "reg_exe", "TIKNIB_WINDOWS_REG", "/mnt/c/Windows/System32/reg.exe"
)


def _normalized_prefix(value):
    return value.replace("\\", "/").rstrip("/")


def wsl_to_windows_path(path, wsl_prefix=None, win_prefix=None):
    """Translate a configured WSL-visible path into its Windows spelling."""
    value = str(path).replace("\\", "/")
    wsl_prefix = _normalized_prefix(
        WSL_PREFIX if wsl_prefix is None else wsl_prefix
    )
    win_prefix = _normalized_prefix(WIN_PREFIX if win_prefix is None else win_prefix)
    if wsl_prefix and win_prefix and (
        value == wsl_prefix or value.startswith(wsl_prefix + "/")
    ):
        return win_prefix + value[len(wsl_prefix) :]
    return value


def windows_to_wsl_path(path, wsl_prefix=None, win_prefix=None):
    """Translate a configured Windows path into its WSL-visible spelling."""
    value = str(path).replace("\\", "/")
    win_prefix = _normalized_prefix(WIN_PREFIX if win_prefix is None else win_prefix)
    wsl_prefix = _normalized_prefix(
        WSL_PREFIX if wsl_prefix is None else wsl_prefix
    )
    if win_prefix and wsl_prefix and (
        value.lower() == win_prefix.lower()
        or value.lower().startswith(win_prefix.lower() + "/")
    ):
        return wsl_prefix + value[len(win_prefix) :]
    return value
