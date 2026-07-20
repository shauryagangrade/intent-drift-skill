#!/usr/bin/env bash
# Install / symlink the intent-drift skill into the active Claude Code skills dir.
set -euo pipefail

SKILL_NAME="intent-drift"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.claude/skills/${SKILL_NAME}"

echo "Installing ${SKILL_NAME} -> ${DEST}"

# Create the skills directory if needed
mkdir -p "$(dirname "${DEST}")"

# If the destination is not already this directory, (re)create the symlink
if [ "$(readlink -f "${DEST}" 2>/dev/null || true)" != "$(readlink -f "${SRC}")" ]; then
  rm -rf "${DEST}"
  ln -s "${SRC}" "${DEST}"
  echo "Symlinked."
else
  echo "Already linked."
fi

# Install Python dependencies (best-effort)
if command -v pip >/dev/null 2>&1; then
  pip install -r "${SRC}/requirements.txt" || echo "pip install failed; deps may already be present"
else
  echo "pip not found; skipping dependency install"
fi

echo "Done. Invoke with: /intent-drift --original-goal ... --current-plan ..."
