import argparse
import os
import pickle
import sys


REQUIRED_FUNCTION_FIELDS = {
    "name",
    "bin_path",
    "strings",
    "consts",
    "bb_data",
}


def validate_pickle(path):
    try:
        with open(path, "rb") as pickle_file:
            functions = pickle.load(pickle_file)
    except Exception as error:
        return ["cannot load pickle: {}".format(error)]

    if not isinstance(functions, list) or not functions:
        return ["pickle must contain a non-empty function list"]

    errors = []
    for index, function in enumerate(functions):
        if not isinstance(function, dict):
            errors.append("function {} is not a dictionary".format(index))
            continue

        missing = REQUIRED_FUNCTION_FIELDS - set(function)
        if missing:
            errors.append(
                "function {} is missing fields: {}".format(
                    index, ", ".join(sorted(missing))
                )
            )
            continue

        if not isinstance(function["bb_data"], list) or not all(
            isinstance(block, dict) for block in function["bb_data"]
        ):
            errors.append("function {} has malformed basic-block data".format(index))
            continue
        if not isinstance(function["strings"], list):
            errors.append("function {} has malformed strings".format(index))
            continue
        if not isinstance(function["consts"], list):
            errors.append("function {} has malformed constants".format(index))
            continue

        malformed_block = next(
            (
                block
                for block in function["bb_data"]
                if not isinstance(block.get("strings", []), list)
                or not isinstance(block.get("consts", []), list)
            ),
            None,
        )
        if malformed_block is not None:
            errors.append(
                "function {} has malformed basic-block strings or constants".format(
                    index
                )
            )
            continue

        bb_strings = [
            value
            for block in function["bb_data"]
            for value in block.get("strings", [])
        ]
        bb_consts = [
            value
            for block in function["bb_data"]
            for value in block.get("consts", [])
        ]
        if function["strings"] != bb_strings:
            errors.append("function {} has inconsistent strings".format(index))
        if function["consts"] != bb_consts:
            errors.append("function {} has inconsistent constants".format(index))
        if any(
            not isinstance(value[1], str)
            for value in function["strings"]
            if isinstance(value, (list, tuple)) and len(value) > 1
        ):
            errors.append("function {} contains non-text strings".format(index))

        if len(errors) >= 20:
            errors.append("validation stopped after 20 errors")
            break

    return errors


def validate_binary(binary_path, require_log=True):
    errors = []
    required = [
        binary_path,
        binary_path + ".done",
        binary_path + ".pickle",
    ]
    if require_log:
        required.append(binary_path + ".output")
    for path in required:
        if not os.path.isfile(path):
            errors.append("missing {}".format(path))

    if not any(
        os.path.isfile(binary_path + suffix) for suffix in (".idb", ".i64")
    ):
        errors.append("missing IDA database (.idb or .i64)")

    pickle_path = binary_path + ".pickle"
    if os.path.isfile(pickle_path):
        errors.extend(validate_pickle(pickle_path))
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate raw IDA outputs and write a retry input list."
    )
    parser.add_argument("--input_list", required=True)
    parser.add_argument("--failed_list")
    parser.add_argument(
        "--allow-missing-log",
        action="store_true",
        help="do not require the .output log produced by do_idascript.py --log",
    )
    args = parser.parse_args()

    with open(args.input_list, "r") as input_file:
        binaries = [line.strip() for line in input_file if line.strip()]

    failed = []
    for binary_path in binaries:
        errors = validate_binary(
            binary_path, require_log=not args.allow_missing_log
        )
        if errors:
            failed.append(binary_path)
            print("[FAIL] {}".format(binary_path))
            for error in errors:
                print("  - {}".format(error))
    if args.failed_list:
        with open(args.failed_list, "w") as failed_file:
            if failed:
                failed_file.write("\n".join(failed) + "\n")

    print(
        "validated={} passed={} failed={}".format(
            len(binaries), len(binaries) - len(failed), len(failed)
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
