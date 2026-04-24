# TerminalSensei

TerminalSensei is a **separate, non-intrusive terminal intelligence system** that passively observes CLI usage and turns it into structured learning.

It never wraps commands, never injects output into execution flow, and runs analysis in a separate daemon process.

## Features

- Passive shell collector for Bash and Zsh
- Independent daemon processor (`terminalsensei --daemon`)
- SQLite knowledge base:
  - commands
  - patterns
  - examples
  - mistakes
  - raw logs
- Pattern normalization (`grep error app.log` -> `grep <arg> <file>`)
- Mistake tracking (including command-not-found typo suggestions)
- Improvement suggestions via `sensei tips`

## Install

```bash
python -m pip install .
```

This provides two equivalent commands:

- `sensei`
- `terminalsensei`

For editable development install:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -e .
```

## Shell Hook Setup (Passive Collector)

Collector file:

```bash
python -c 'import importlib.resources as r; print(r.files("terminalsensei.collector").joinpath("hooks.sh"))'
```

### Bash (`~/.bashrc`)

```bash
source /path/to/site-packages/terminalsensei/collector/hooks.sh
terminalsensei_install_bash_hook
```

### Zsh (`~/.zshrc`)

```zsh
source /path/to/site-packages/terminalsensei/collector/hooks.sh
terminalsensei_install_zsh_hook
```

Optional env override:

```bash
export TERMINALSENSEI_LOG="$HOME/.terminalsensei_log"
```

Collector writes tab-separated records:

```text
<unix_timestamp>\t<exit_code>\t<raw_command>
```

## Run the Daemon

```bash
terminalsensei --daemon
```

Process once and exit (useful for testing):

```bash
terminalsensei --daemon --once

# custom state file (optional)
terminalsensei --daemon --state-path /tmp/terminalsensei-state.json
```

## CLI Usage

```bash
sensei stats      # command usage stats
sensei book       # full CLI knowledge book (numbered entries)
sensei patterns   # normalized syntax patterns + examples
sensei tips       # behavior-based improvement suggestions
sensei delete 3   # delete command by numbered book index (or command name)
sensei clear      # clear all tracked book data
```

## Database Location

Default database path:

```text
~/.local/share/terminalsensei/sensei.db
```

Default daemon state path:

```text
~/.local/state/terminalsensei/daemon_state.json
```

## Architecture

```text
terminalsensei/
├── collector/        # shell integration
├── daemon/           # background processor
├── core/
│   ├── parser.py
│   ├── normalizer.py
│   ├── tracker.py
├── book/
│   ├── commands.py
│   ├── patterns.py
│   ├── mistakes.py
├── engine/
│   ├── suggester.py
│   ├── explainer.py
├── cli/
│   └── main.py
├── db/
│   └── schema.sql
```

## Notes

- TerminalSensei is intentionally silent during shell execution.
- Suggestions are only shown when the user explicitly runs `sensei tips`.
- No network dependency is required for core functionality.

## GitHub-ready repository layout

```text
.
├── .github/workflows/ci.yml
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
└── terminalsensei/
```
