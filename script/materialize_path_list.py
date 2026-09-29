#!/usr/bin/env python3
"""Resolve a portable relative-path manifest against a local root."""

import argparse
import os
import re
import sys


WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def materialize(manifest, root, kind="file"):
    root = os.path.abspath(root)
    real_root = os.path.realpath(root)
    resolved = []
    errors = []

    with open(manifest, "r") as manifest_file:
        entries = [line.strip() for line in manifest_file if line.strip()]

    for line_number, entry in enumerate(entries, 1):
        normalized = entry.replace("\\", "/")
        if (
            os.path.isabs(normalized)
            or WINDOWS_ABSOLUTE_PATH.match(normalized)
            or normalized == ".."
            or normalized.startswith("../")
        ):
            errors.append(
                "line {} must be a relative path: {}".format(line_number, entry)
            )
            continue

        path = os.path.abspath(os.path.join(root, normalized))
        if os.path.commonpath((real_root, os.path.realpath(path))) != real_root:
            errors.append("line {} escapes the root: {}".format(line_number, entry))
            continue
        exists = {
            "file": os.path.isfile,
            "directory": os.path.isdir,
            "any": os.path.exists,
        }[kind](path)
        if not exists:
            errors.append(
                "line {} does not resolve to a {}: {}".format(
                    line_number, kind, path
                )
            )
            continue
        resolved.append(path)

    if not entries:
        errors.append("manifest is empty")
    return resolved, errors


def main():
    parser = argparse.ArgumentParser(
        description="Resolve a tracked relative manifest into a local path list."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--kind", choices=("file", "directory", "any"), default="file"
    )
    args = parser.parse_args()

    paths, errors = materialize(args.manifest, args.root, args.kind)
    if errors:
        for error in errors:
            print("[FAIL] {}".format(error), file=sys.stderr)
        return 1

    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w") as output_file:
        output_file.write("\n".join(paths) + "\n")
    print("materialized={} output={}".format(len(paths), args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
