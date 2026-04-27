#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/setup.sh \"/path/to/Obsidian Vault\""
  exit 1
fi

VAULT_PATH="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$VAULT_PATH" ]; then
  echo "Error: vault path does not exist: $VAULT_PATH"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: python not found (set PYTHON_BIN to override)"
  exit 1
fi

VENV_DIR="$REPO_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
  "$VENV_PYTHON" -m ensurepip --upgrade
fi

"$VENV_PYTHON" -m pip install -e "$REPO_ROOT" >/dev/null

if [ -n "${ZSH_VERSION:-}" ]; then
  SHELL_RC="$HOME/.zshrc"
else
  SHELL_RC="$HOME/.bashrc"
fi

mkdir -p "$HOME/.local/state/terminalsensei"

HOOKS_PATH="$("$VENV_PYTHON" - <<'PY'
import importlib.resources as r
print(r.files("terminalsensei.collector").joinpath("hooks.sh"))
PY
)"

START_SCRIPT="$HOME/.local/state/terminalsensei/start-daemon.sh"
cat > "$START_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export SENSEI_VAULT_PATH="$VAULT_PATH"
exec "$VENV_PYTHON" -m terminalsensei.cli.main --daemon
EOF
chmod +x "$START_SCRIPT"

SNIPPET_BEGIN="# >>> TerminalSensei auto-setup >>>"
SNIPPET_END="# <<< TerminalSensei auto-setup <<<"

if grep -Fq "$SNIPPET_BEGIN" "$SHELL_RC" 2>/dev/null; then
  TMP_FILE="$(mktemp)"
  awk -v b="$SNIPPET_BEGIN" -v e="$SNIPPET_END" '
    $0==b {skip=1; next}
    $0==e {skip=0; next}
    !skip {print}
  ' "$SHELL_RC" > "$TMP_FILE"
  mv "$TMP_FILE" "$SHELL_RC"
fi

cat >> "$SHELL_RC" <<EOF
$SNIPPET_BEGIN
export SENSEI_VAULT_PATH="$VAULT_PATH"
source "$HOOKS_PATH"
terminalsensei_install_bash_hook 2>/dev/null || true
terminalsensei_install_zsh_hook 2>/dev/null || true
if ! pgrep -f "terminalsensei.cli.main --daemon" >/dev/null 2>&1; then
  nohup "$START_SCRIPT" >/dev/null 2>&1 &
fi
$SNIPPET_END
EOF

if ! pgrep -f "terminalsensei.cli.main --daemon" >/dev/null 2>&1; then
  nohup "$START_SCRIPT" >/dev/null 2>&1 &
fi

echo "Done."
echo "Vault: $VAULT_PATH"
echo "Virtualenv: $VENV_DIR"
echo "RC file updated: $SHELL_RC"
echo "Open a new shell to activate hooks immediately."
