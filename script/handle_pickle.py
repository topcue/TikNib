import pickle
import os
import re
import sys

# --- Configuration ---

WSL_PREFIX = "/home/user/win_workspace"
WIN_PREFIX = "C:/Users/user/workspace"


def win_to_wsl_path(p):
    """
    Standardize backslashes and replace Windows prefix with WSL prefix.
    """
    p_norm = p.replace("\\", "/")
    if p_norm == WIN_PREFIX or p_norm.startswith(WIN_PREFIX + "/"):
        return WSL_PREFIX + p_norm[len(WIN_PREFIX):]
    return p_norm


def process_recursive(data, replace_flag=False):
    """
    Recursively search and optionally replace Windows paths.
    """
    found_paths = []

    if isinstance(data, dict):
        for k, v in data.items():
            res, updated_v = process_recursive(v, replace_flag)
            found_paths.extend(res)
            if replace_flag:
                data[k] = updated_v

    elif isinstance(data, list):
        for i in range(len(data)):
            res, updated_item = process_recursive(data[i], replace_flag)
            found_paths.extend(res)
            if replace_flag:
                data[i] = updated_item

    elif isinstance(data, str):
        if re.match(r"^[a-zA-Z]:\\", data) or "\\" in data:
            found_paths.append(data)
            if replace_flag:
                return found_paths, win_to_wsl_path(data)

    return found_paths, data


def get_immediate_subdirs(base_path):
    entries = [os.path.join(base_path, name) for name in os.listdir(base_path)]
    subdirs = [p for p in entries if os.path.isdir(p)]
    nondirs = [p for p in entries if not os.path.isdir(p)]
    return sorted(subdirs), sorted(nondirs)


def collect_elf_basenames(project_dir):
    """
    Return a set of basenames for files ending with '.elf'.

    Example:
      foo.elf -> basename 'foo'
    """
    basenames = set()

    for name in os.listdir(project_dir):
        full_path = os.path.join(project_dir, name)
        if not os.path.isfile(full_path):
            continue

        if name.endswith(".elf"):
            basenames.add(name[:-4])  # strip ".elf"

    return basenames


def validate_project_dir(project_dir):
    """
    Validate one project directory.

    Conditions:
    - Must contain at least one '.elf' file
    - For every basename found from '.elf', the following must exist:
      - <basename>.elf
      - <basename>.elf.done
      - <basename>.elf.pickle
    - Extra files like <basename>.elf.i64 are allowed
    """
    errors = []

    basenames = collect_elf_basenames(project_dir)
    if not basenames:
        errors.append(f"No '.elf' files found in: {project_dir}")
        return False, errors

    for base in sorted(basenames):
        required_files = [
            os.path.join(project_dir, f"{base}.elf"),
            os.path.join(project_dir, f"{base}.elf.done"),
            os.path.join(project_dir, f"{base}.elf.pickle"),
        ]

        missing = [p for p in required_files if not os.path.isfile(p)]
        if missing:
            errors.append(
                f"Missing required variations for basename '{base}' in {project_dir}:"
            )
            for m in missing:
                errors.append(f"  - {m}")

    return len(errors) == 0, errors


def validate_base_path(base_path):
    """
    Validate BASE_PATH.

    Conditions:
    - Path must exist
    - Must be a directory
    - Must contain one or more subdirectories
    - Must not contain non-directory entries directly under BASE_PATH
    - Each subdirectory must pass project-dir validation
    """
    errors = []

    if not os.path.exists(base_path):
        errors.append(f"Path does not exist: {base_path}")
        return False, errors

    if not os.path.isdir(base_path):
        errors.append(f"Path is not a directory: {base_path}")
        return False, errors

    subdirs, nondirs = get_immediate_subdirs(base_path)

    if not subdirs:
        errors.append(
            f"BASE_PATH must contain at least one subdirectory: {base_path}"
        )

    if nondirs:
        errors.append(
            "BASE_PATH must contain only subdirectories directly under it. "
            "Found non-directory entries:"
        )
        for p in nondirs:
            errors.append(f"  - {p}")

    for subdir in subdirs:
        ok, sub_errors = validate_project_dir(subdir)
        if not ok:
            errors.append(f"[Invalid project dir] {subdir}")
            errors.extend(sub_errors)

    return len(errors) == 0, errors


def get_abs_paths(target_dir):
    abs_paths = []
    target_dir = os.path.abspath(target_dir)

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".elf.pickle"):
                abs_paths.append(os.path.join(root, file))

    abs_paths.sort()
    return abs_paths


def load_pickle_file(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle_file(path, data):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def scan_paths(target_paths):
    """
    Search mode only. Do not modify files.
    Returns:
      - files_with_matches: list of file paths that contain Windows paths
      - total_matches: total number of matched strings
    """
    files_with_matches = []
    total_matches = 0

    for target_path in target_paths:
        print(f"\n[Target] {target_path}")

        try:
            data = load_pickle_file(target_path)
        except Exception as e:
            print(f"Failed to load {target_path}: {e}")
            continue

        found, _ = process_recursive(data, replace_flag=False)

        if found:
            unique_found = sorted(set(found))
            total_matches += len(found)
            files_with_matches.append(target_path)

            print(f"Found {len(found)} Windows paths ({len(unique_found)} unique).")
            for p in unique_found:
                print(f"  - Detected: {p}")
                print(f"    -> Would be: {win_to_wsl_path(p)}")
        else:
            print("No Windows paths detected.")

    return files_with_matches, total_matches


def replace_paths(target_paths):
    """
    Replace mode. Actually modify and save files.
    """
    updated_files = 0

    for target_path in target_paths:
        print(f"\n[Replace Target] {target_path}")

        try:
            data = load_pickle_file(target_path)
        except Exception as e:
            print(f"Failed to load {target_path}: {e}")
            continue

        found, updated_data = process_recursive(data, replace_flag=True)

        if found:
            try:
                save_pickle_file(target_path, updated_data)
                updated_files += 1
                print(f"Successfully updated and saved: {target_path}")
            except Exception as e:
                print(f"Failed to save {target_path}: {e}")
        else:
            print("No Windows paths detected. Skipped.")

    return updated_files


def ask_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer with 'y' or 'n'.")


def main():
    args = sys.argv[1:]
    auto_yes = False

    if "--yes" in args:
        auto_yes = True
        args.remove("--yes")

    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} [--yes] <BASE_PATH>")
        sys.exit(1)

    base_path = os.path.abspath(os.path.expanduser(args[0]))

    print(f"\n[Validate] BASE_PATH = {base_path}")
    ok, errors = validate_base_path(base_path)
    if not ok:
        print("Validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("Validation passed.")

    target_paths = get_abs_paths(base_path)
    if not target_paths:
        print("No '.elf.pickle' files found under the given BASE_PATH.")
        sys.exit(1)

    print(f"\nFound {len(target_paths)} '.elf.pickle' files.")

    print("\n=== Search mode (no modification) ===")
    files_with_matches, total_matches = scan_paths(target_paths)

    if not files_with_matches:
        print("\nNo Windows-style paths were found in any pickle file.")
        sys.exit(0)

    print(
        f"\nSummary: {len(files_with_matches)} files contain Windows paths, "
        f"{total_matches} total matches."
    )

    if auto_yes:
        do_replace = True
        print("\nAuto-confirm enabled: replacing detected Windows paths.")
    else:
        do_replace = ask_yes_no("\nDo you want to replace and save them? [y/n]: ")
    if not do_replace:
        print("Replacement cancelled.")
        sys.exit(0)

    print("\n=== Replace mode (modification enabled) ===")
    updated_files = replace_paths(files_with_matches)
    print(f"\nDone. Updated {updated_files} file(s).")


if __name__ == "__main__":
    main()
