#!/bin/bash
set -euo pipefail

TEST_SET="${1:-test1}"
LOCK_DIR="/tmp/tiknib_test.lock"
INPUT_MANIFEST="example/${TEST_SET}/list.txt"
INPUT_LIST="data/${TEST_SET}/list.txt"
SOURCE_LIST="example/${TEST_SET}/sources.txt"
DATASET_DIR="${TIKNIB_TEST_DATASET_DIR:-}"
CTAGS_DIR="data/${TEST_SET}"
CMD_EXE=""
FAILED_DIR="data/${TEST_SET}/failures"

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

if [ -z "${DATASET_DIR}" ]; then
  WSL_PREFIX="$(${PYTHON_BIN} -c 'from config.path_variables import WSL_PREFIX; print(WSL_PREFIX)')"
  DATASET_DIR="${WSL_PREFIX}/storage/tiknib/${TEST_SET}"
fi

CMD_EXE="$(${PYTHON_BIN} -c 'from config.path_variables import WINDOWS_CMD_EXE; print(WINDOWS_CMD_EXE)')"

if [ ! -f "${INPUT_MANIFEST}" ]; then
  echo "Missing input manifest: ${INPUT_MANIFEST}" >&2
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

mkdir -p "${FAILED_DIR}"

"${PYTHON_BIN}" script/materialize_path_list.py \
  --manifest "${INPUT_MANIFEST}" \
  --root "${DATASET_DIR}" \
  --output "${INPUT_LIST}"

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

"${PYTHON_BIN}" script/cleanup_tiknib_test.py \
  "${TEST_SET}" \
  --dataset-dir "${DATASET_DIR}"

"${PYTHON_BIN}" helper/do_idascript.py \
  --preflight \
  --log \
  --failed_list "${FAILED_DIR}/ida.txt" \
  --input_list "${INPUT_LIST}"

"${PYTHON_BIN}" script/validate_ida_outputs.py \
  --input_list "${INPUT_LIST}" \
  --failed_list "${FAILED_DIR}/ida_validation.txt"

"${PYTHON_BIN}" script/handle_pickle.py --yes "${DATASET_DIR}"

"${PYTHON_BIN}" script/validate_tiknib_stage.py \
  --input_list "${INPUT_LIST}" \
  --stage normalized \
  --failed_list "${FAILED_DIR}/normalized.txt"

"${PYTHON_BIN}" helper/extract_lineno.py \
  --input_list "${INPUT_LIST}" \
  --failed_list "${FAILED_DIR}/lineno_extraction.txt" \
  --threshold 1000

"${PYTHON_BIN}" script/validate_tiknib_stage.py \
  --input_list "${INPUT_LIST}" \
  --stage lineno \
  --failed_list "${FAILED_DIR}/lineno_validation.txt"

"${PYTHON_BIN}" helper/filter_functions.py \
  --input_list "${INPUT_LIST}" \
  --threshold 1

"${PYTHON_BIN}" script/validate_tiknib_stage.py \
  --input_list "${INPUT_LIST}" \
  --stage filtered \
  --failed_list "${FAILED_DIR}/filtered.txt"

"${PYTHON_BIN}" helper/extract_functype.py \
    --input_list "${INPUT_LIST}" \
    --source_list "${SOURCE_LIST}" \
    --ctags_dir "${CTAGS_DIR}" \
    --threshold 1

"${PYTHON_BIN}" script/validate_tiknib_stage.py \
  --input_list "${INPUT_LIST}" \
  --stage typed \
  --failed_list "${FAILED_DIR}/typed.txt"

"${PYTHON_BIN}" helper/extract_features.py \
    --input_list "${INPUT_LIST}" \
    --threshold 1

"${PYTHON_BIN}" script/validate_tiknib_stage.py \
  --input_list "${INPUT_LIST}" \
  --stage feature \
  --failed_list "${FAILED_DIR}/feature.txt"
