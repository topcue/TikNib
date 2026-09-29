import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.path_variables import WSL_PREFIX


BASE_DIR = os.environ.get("TIKNIB_TEST_DATASET_ROOT")
if not BASE_DIR and WSL_PREFIX:
    BASE_DIR = os.path.join(WSL_PREFIX, "storage", "tiknib")
TARGET_SETS = ["test1", "test2"]


def cleanup_test_dir(test_dir):
    elf_count = sum(
        name.endswith(".elf")
        for _, _, files in os.walk(test_dir)
        for name in files
    )
    if elf_count == 0:
        raise ValueError("refusing to clean a directory with no .elf inputs")

    removed = 0
    kept = 0

    for root, dirs, files in os.walk(test_dir):
        for name in files:
            path = os.path.join(root, name)

            if name.endswith(".elf"):
                kept += 1
                print(f"[KEEP]   {path}")
                continue

            try:
                os.remove(path)
                removed += 1
                print(f"[REMOVE] {path}")
            except Exception as e:
                print(f"[ERROR]  {path}: {e}")

    return kept, removed


def main():
    parser = argparse.ArgumentParser(
        description="Remove generated sidecars from the small TikNib test sets."
    )
    parser.add_argument("test_set", nargs="?", choices=TARGET_SETS)
    parser.add_argument(
        "--dataset-dir",
        help="exact test-set directory; requires the matching test_set argument",
    )
    args = parser.parse_args()

    if args.dataset_dir and not args.test_set:
        parser.error("--dataset-dir requires test_set")
    if args.dataset_dir:
        expected_name = args.test_set
        actual_name = os.path.basename(os.path.abspath(args.dataset_dir))
        if actual_name != expected_name:
            parser.error(
                "--dataset-dir basename must match test_set ({!r})".format(
                    expected_name
                )
            )
        targets = [(args.test_set, os.path.abspath(args.dataset_dir))]
    else:
        if not BASE_DIR or not os.path.isabs(BASE_DIR):
            parser.error(
                "configure paths.wsl_prefix, TIKNIB_TEST_DATASET_ROOT, or "
                "--dataset-dir"
            )
        target_sets = [args.test_set] if args.test_set else TARGET_SETS
        targets = [(name, os.path.join(BASE_DIR, name)) for name in target_sets]

    total_kept = 0
    total_removed = 0

    for test_name, test_path in targets:
        if not os.path.isdir(test_path):
            print(f"[SKIP] {test_path} does not exist or is not a directory.")
            continue

        print(f"\n=== Cleaning {test_path} ===")
        try:
            kept, removed = cleanup_test_dir(test_path)
        except ValueError as error:
            print(f"[ERROR] {test_path}: {error}")
            sys.exit(1)
        total_kept += kept
        total_removed += removed

        print(f"[SUMMARY] {test_name}: kept={kept}, removed={removed}")

    print(f"\n=== Done ===")
    print(f"Total kept: {total_kept}")
    print(f"Total removed: {total_removed}")


if __name__ == "__main__":
    main()

# EOF
