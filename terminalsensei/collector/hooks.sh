# TerminalSensei passive collector hooks.
# Source this file from .bashrc/.zshrc to append command history entries to
# ~/.terminalsensei_log without wrapping command execution.

: "${TERMINALSENSEI_LOG:=$HOME/.terminalsensei_log}"

terminalsensei_collect_bash() {
  local exit_code="$?"
  local ts cmd
  ts="$(date +%s)"
  cmd="$(history 1 | sed 's/^[[:space:]]*[0-9]\+[[:space:]]*//')"
  [ -z "$cmd" ] && return 0
  command printf '%s\t%s\t%s\n' "$ts" "$exit_code" "$cmd" >> "$TERMINALSENSEI_LOG" 2>/dev/null
}

terminalsensei_install_bash_hook() {
  if [ -n "${PROMPT_COMMAND:-}" ]; then
    PROMPT_COMMAND="terminalsensei_collect_bash; $PROMPT_COMMAND"
  else
    PROMPT_COMMAND="terminalsensei_collect_bash"
  fi
}

typeset -g __terminalsensei_zsh_last_cmd=""

terminalsensei_collect_zsh_preexec() {
  __terminalsensei_zsh_last_cmd="$1"
}

terminalsensei_collect_zsh_precmd() {
  local exit_code="$?"
  local ts
  ts="$(date +%s)"
  [ -z "$__terminalsensei_zsh_last_cmd" ] && return 0
  command printf '%s\t%s\t%s\n' "$ts" "$exit_code" "$__terminalsensei_zsh_last_cmd" >> "$TERMINALSENSEI_LOG" 2>/dev/null
}

terminalsensei_install_zsh_hook() {
  autoload -Uz add-zsh-hook
  add-zsh-hook preexec terminalsensei_collect_zsh_preexec
  add-zsh-hook precmd terminalsensei_collect_zsh_precmd
}
