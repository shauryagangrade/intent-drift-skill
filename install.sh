#!/usr/bin/env bash
# Install / symlink the intent-drift skill into the active Claude Code skills dir.
set -euo pipefail

SKILL_NAME="intent-drift"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.claude/skills/${SKILL_NAME}"

echo "Installing ${SKILL_NAME} -> ${DEST}"

# Create the skills directory if needed
mkdir -p "$(dirname "${DEST}")"

# Portable realpath: `readlink -f` is a GNU coreutils extension that the BSD
# readlink on macOS does not support, so fall back to python3 or pwd -P.
realpath_portable() {
  local path="$1"
  if readlink -f "$path" >/dev/null 2>&1; then
    readlink -f "$path"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$path"
  else
    (cd "$path" && pwd -P) || return 1
  fi
}

# Only ever replace the destination when it is a symlink pointing elsewhere.
# A real directory is left untouched so user data is never deleted.
if [ -L "${DEST}" ]; then
  if [ "$(realpath_portable "${DEST}")" = "$(realpath_portable "${SRC}")" ]; then
    echo "Already linked."
  else
    rm "${DEST}"
    ln -s "${SRC}" "${DEST}"
    echo "Symlinked."
  fi
elif [ -e "${DEST}" ]; then
  echo "WARNING: ${DEST} exists and is not a symlink; leaving it in place."
  echo "Remove it manually, then re-run this script to symlink."
else
  ln -s "${SRC}" "${DEST}"
  echo "Symlinked."
fi

# Install Python dependencies (best-effort)
if command -v pip >/dev/null 2>&1; then
  pip install -r "${SRC}/requirements.txt" || echo "pip install failed; deps may already be present"

  # Install intent-drift if not already installed
  if ! pip show intent-drift >/dev/null 2>&1; then
    pip install "intent-drift>=0.1.0"
  else
    echo "intent-drift already installed"
  fi
else
  echo "pip not found; skipping dependency install"
fi

echo "Done. Invoke with: /intent-drift --original-goal ... --current-plan ..."
