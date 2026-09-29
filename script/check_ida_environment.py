#!/usr/bin/env python3
"""Validate local IDA configuration without modifying IDA or the registry."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.path_variables import IDA_FETCH_FUNCDATA, IDA_PATH
from tiknib.ida_environment import check_ida_environment


def main():
    errors, warnings, details = check_ida_environment(
        IDA_PATH, IDA_FETCH_FUNCDATA
    )
    for name, value in sorted(details.items()):
        print("{}={}".format(name, value))
    for warning in warnings:
        print("[WARN] {}".format(warning))
    for error in errors:
        print("[FAIL] {}".format(error))
    if errors:
        return 1
    print("[OK] IDA configuration and Windows interop are consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
