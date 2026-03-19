import os

BASE_DIR = "/home/user/win_workspace/storage/tiknib"
TARGET_SETS = ["test1", "test2"]


def cleanup_test_dir(test_dir):
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
    total_kept = 0
    total_removed = 0

    for test_name in TARGET_SETS:
        test_path = os.path.join(BASE_DIR, test_name)

        if not os.path.isdir(test_path):
            print(f"[SKIP] {test_path} does not exist or is not a directory.")
            continue

        print(f"\n=== Cleaning {test_path} ===")
        kept, removed = cleanup_test_dir(test_path)
        total_kept += kept
        total_removed += removed

        print(f"[SUMMARY] {test_name}: kept={kept}, removed={removed}")

    print(f"\n=== Done ===")
    print(f"Total kept: {total_kept}")
    print(f"Total removed: {total_removed}")


if __name__ == "__main__":
    main()

# EOF

