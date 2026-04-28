#!/bin/bash
set -euo pipefail

TEST_SET="${1:-test1}"
LOCK_DIR="/tmp/tiknib_test.lock"
INPUT_LIST="example/${TEST_SET}/list.txt"
SOURCE_LIST="example/${TEST_SET}/sources.txt"
DATASET_DIR="/home/user/win_workspace/storage/tiknib/${TEST_SET}"
CTAGS_DIR="data/${TEST_SET}"
CMD_EXE="/mnt/c/Windows/System32/cmd.exe"

case "${TEST_SET}" in
  test1|test2)
    ;;
  *)
    echo "Usage: bash script/test.sh [test1|test2]" >&2
    exit 1
    ;;
esac

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  echo "Another TikNib test run is already in progress." >&2
  exit 1
fi
trap 'rmdir "${LOCK_DIR}"' EXIT

if [ -x "venv/bin/python" ]; then
  PYTHON_BIN="venv/bin/python"
else
  PYTHON_BIN="python"
fi

if [ ! -f "${INPUT_LIST}" ]; then
  echo "Missing input list: ${INPUT_LIST}" >&2
  exit 1
fi

if [ ! -f "${SOURCE_LIST}" ]; then
  echo "Missing source list: ${SOURCE_LIST}" >&2
  exit 1
fi

if [ ! -d "${DATASET_DIR}" ]; then
  echo "Missing dataset directory: ${DATASET_DIR}" >&2
  exit 1
fi

if [ -z "${WSL_INTEROP:-}" ]; then
  echo "WSL_INTEROP is not set. Run this from a Windows-launched WSL session." >&2
  exit 1
fi

if [ ! -x "${CMD_EXE}" ]; then
  echo "Missing Windows command launcher: ${CMD_EXE}" >&2
  exit 1
fi

if ! "${CMD_EXE}" /c exit 0 >/dev/null 2>&1; then
  echo "Windows executable interop is not available in this WSL session." >&2
  echo "Open a Windows-launched WSL terminal and run the script there." >&2
  exit 1
fi

"${PYTHON_BIN}" script/cleanup_tiknib_test.py "${TEST_SET}"

"${PYTHON_BIN}" helper/do_idascript.py \
  --idapath "/home/user/win_workspace/IDA" \
  --idc "tiknib/ida/fetch_funcdata_v7.5.py" \
  --input_list "${INPUT_LIST}"

"${PYTHON_BIN}" script/handle_pickle.py --yes "${DATASET_DIR}"

"${PYTHON_BIN}" helper/extract_lineno.py \
  --input_list "${INPUT_LIST}" \
  --threshold 1000

"${PYTHON_BIN}" helper/filter_functions.py \
  --input_list "${INPUT_LIST}" \
  --threshold 1

"${PYTHON_BIN}" helper/extract_functype.py \
    --input_list "${INPUT_LIST}" \
    --source_list "${SOURCE_LIST}" \
    --ctags_dir "${CTAGS_DIR}" \
    --threshold 1

"${PYTHON_BIN}" helper/extract_features.py \
    --input_list "${INPUT_LIST}" \
    --threshold 1
