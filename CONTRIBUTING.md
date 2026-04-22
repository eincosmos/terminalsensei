# Contributing to TerminalSensei

Thanks for contributing.

## Local development

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -e .
```

## Quick checks before pushing

```bash
python -m compileall terminalsensei
python -m terminalsensei.cli.main --help
```

## Smoke test

```bash
tmpdir=$(mktemp -d)
db="$tmpdir/sensei.db"
log="$tmpdir/.terminalsensei_log"
state="$tmpdir/state.json"
python - <<PY
from pathlib import Path
Path("$log").write_text("1713770000\t0\tcat notes.txt\n", encoding="utf-8")
PY
python -m terminalsensei.cli.main --db-path "$db" --log-path "$log" --state-path "$state" --daemon --once
python -m terminalsensei.cli.main --db-path "$db" book
rm -rf "$tmpdir"
```

## Pull requests

1. Create a branch from `main`.
2. Keep changes scoped and documented.
3. Update README when behavior or commands change.
4. Run the checks above before opening the PR.
