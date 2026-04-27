# TerminalSensei Implementation Deep Dive (Interview Guide)

This document explains **how TerminalSensei was built**, **why each design choice was made**, and **what production issues were discovered and fixed**.

Use this as your detailed interview reference.

---

## 1. Problem Statement

Most terminal learners repeat commands but do not build a structured memory of:

1. What they run frequently
2. Where they make mistakes
3. Which patterns they should improve

TerminalSensei solves this by passively capturing command behavior and converting it into a searchable learning system (CLI views + Obsidian knowledge notes).

---

## 2. Core Design Principles

1. **Non-intrusive**: never wrap/modify command execution.
2. **Passive collection**: only record terminal events after command completion.
3. **Separation of concerns**: shell hook logs; daemon processes; CLI reads/exports.
4. **Offline-first**: SQLite + local files, no required network dependency.
5. **Idempotent writes**: repeated updates should not duplicate note content.

---

## 3. Architecture in Plain English

### Data path

1. User runs command in shell.
2. Hook appends `<timestamp>\t<exit_code>\t<raw_command>` to log file.
3. Daemon tails that log using an offset file.
4. Daemon parses command and updates SQLite tables (`commands`, `patterns`, `examples`, `mistakes`, `logs`).
5. If Obsidian path is configured, daemon updates:
   - `Sensei Book/Commands/<command>.md`
   - `Sensei Book/_index.md`

### Main modules and responsibilities

- `terminalsensei/collector/hooks.sh`: Bash/Zsh collection hooks
- `terminalsensei/daemon/runner.py`: background polling + offset state
- `terminalsensei/core/tracker.py`: DB ingestion + normalization + mistake recording
- `terminalsensei/obsidian/generator.py`: command note create/update
- `terminalsensei/obsidian/index.py`: `_index.md` generation
- `terminalsensei/cli/main.py`: command entrypoint (`sensei ...`)
- `scripts/setup.sh`: one-command bootstrap for beginners

---

## 4. Important Terms (Interview Vocabulary)

- **Shell hook**: function attached to shell lifecycle (`PROMPT_COMMAND` in Bash, `preexec/precmd` in Zsh).
- **Daemon**: long-running background process that continuously processes new logs.
- **Offset**: byte position in log file used to resume incremental reading.
- **WAL mode**: SQLite Write-Ahead Logging for improved concurrent safety/performance.
- **Idempotent update**: running update multiple times produces same final output.
- **Normalization**: converting command invocations into comparable patterns (`grep error app.log` -> `grep <arg> <file>`).
- **Vault-relative link**: Obsidian link path relative to vault root, not current note folder.

---

## 5. Build Plan (How it was implemented)

### Phase A: Passive collection

Implemented shell-level append-only logging:

- Bash hook reads latest history line and `$?`.
- Zsh hook captures command in `preexec`, writes in `precmd`.
- Output format is tab-separated, append-only, low overhead.

Why: avoids touching user command behavior and keeps failure surface small.

### Phase B: Streaming processor (daemon)

Implemented `run_daemon(...)` to:

1. Load previous offset from JSON state.
2. Read only newly appended log lines.
3. Parse each line into a `LogRecord`.
4. Update DB transactionally through `Tracker`.
5. Save new offset.

Why: scalable incremental processing without rereading full log.

### Phase C: Knowledge modeling in SQLite

Tracked multiple perspectives:

- Command usage counts and timestamps
- Pattern abstraction
- Raw examples
- Mistakes with optional corrections

Why: enables both analytics (`sensei stats/patterns/tips`) and educational recall.

### Phase D: Obsidian output

Implemented note generation and index generation:

- One note per command
- Frontmatter metadata + usage/mistakes sections
- Index with ranked and alphabetical views

Why: user gets a personal knowledge graph outside terminal.

### Phase E: Beginner onboarding

Added `scripts/setup.sh` so user can run one command:

1. Create `.venv`
2. Install package in editable mode
3. Configure shell hook snippet
4. Configure `SENSEI_VAULT_PATH`
5. Start daemon automatically

Why: remove manual setup complexity for first-time users.

---

## 6. Real Problems Faced and How They Were Solved

### Problem 1: Clicking command in `_index.md` opened blank note

**Symptoms**
- Command note had content in one place.
- Clicking index link opened empty file.

**Root causes**
1. Filename normalization mismatch (case differences could split targets).
2. Link path ambiguity in Obsidian (vault-root path vs folder-relative expectation).
3. Old empty notes existed in vault root `Commands/` and were being resolved first.

**Fixes**
1. Normalized command note filenames to lowercase in `obsidian/writer.py`.
2. Updated link generation to vault-relative explicit form:
   - `[[Sensei Book/Commands/<name>|<label>]]`
3. Ensured auto-sync resolves to `.../Sensei Book` by default.

### Problem 2: Behavior reverted after `sensei clear` / new commands

**Symptoms**
- Links seemed fixed, then reverted to old `[[Commands/...]]`.

**Root cause**
- Multiple daemon processes were running simultaneously.
- One process still wrote old index format, overwriting new one.

**Fixes**
1. Killed duplicate daemons.
2. Added single-instance daemon lock in `daemon/runner.py` using file lock (`fcntl`).
3. Restarted one clean daemon instance with consistent vault path.

### Problem 3: Setup too hard for beginners

**Symptoms**
- User needed manual venv + install + hooks + daemon command.

**Fix**
- Upgraded `scripts/setup.sh` to perform full bootstrap automatically.

---

## 7. Why Specific Technical Decisions Were Chosen

### Why daemon instead of synchronous shell write?

- Shell UX must stay fast and silent.
- Parsing + DB + file writes are safer in an isolated worker.
- Failures in indexing should not block user command execution.

### Why SQLite?

- Zero-ops local database.
- Good enough for command history workloads.
- Easy query model for stats/patterns/mistake insights.

### Why markdown vault output?

- Human-readable and durable.
- Easy linking and search in Obsidian.
- User owns local data; no SaaS lock-in.

### Why one-command setup script?

- Adoption friction drops dramatically.
- Reduces onboarding mistakes (wrong interpreter, missing hooks, daemon not running).

---

## 8. End-to-End Runtime Sequence (Detailed)

1. Shell starts and loads hook snippet from `.bashrc`/`.zshrc`.
2. User runs `grep error app.log`.
3. Hook appends line to `~/.terminalsensei_log`.
4. Daemon wakes up, reads bytes from last offset.
5. `parse_log_line()` converts row into typed record.
6. `Tracker.process_record()`:
   - Inserts into `logs`
   - Parses command token
   - Upserts command usage + timestamps
   - Normalizes pattern and updates `patterns`
   - Inserts example
   - If failed exit code, records mistake and suggestion path
7. If vault configured:
   - Resolve target folder (`Sensei Book`)
   - Update/create command note
   - Regenerate `_index.md` with vault-relative links
8. Save offset and sleep until next poll interval.

---

## 9. Reliability and Safety Controls

1. **Append-only collection log** reduces mutation risk.
2. **Offset checkpoints** prevent double-processing after restarts.
3. **Daemon lock file** avoids concurrent writers on same stream.
4. **Per-command idempotent note updates** reduce duplication.
5. **Graceful parsing fallbacks** skip malformed lines safely.
6. **Explicit vault path resolution** prevents folder ambiguity.

---

## 10. Interview Talking Points (How to explain confidently)

### 30-second summary

"I built a passive terminal intelligence system. A shell hook logs commands, a daemon incrementally processes those logs into SQLite knowledge, and an Obsidian layer converts that into command notes and an index. I solved real production issues like path-link ambiguity, duplicate daemon writers, and onboarding complexity by adding deterministic vault-relative links, single-instance daemon locking, and a one-command bootstrap script."

### 2-minute technical explanation

"The hook is intentionally minimal and non-blocking. The daemon owns compute-heavy work: parsing, normalization, metrics, and export. I used offsets and WAL SQLite for efficiency and resilience. For Obsidian, I generate structured markdown with frontmatter and stable links. During debugging, I traced a blank-note issue to link/path mismatch and competing daemon processes. I hardened the system with normalized filenames, explicit `Sensei Book/Commands/...` links, vault-path resolver logic, and an OS-level lock to prevent concurrent daemons."

### If asked "What was hardest?"

"The hardest part was not feature coding but making behavior deterministic in real user environments: conflicting paths, stale processes, and shell startup variance. The fix was to make every ambiguous input explicit and to enforce single-writer semantics."

---

## 11. Practical Operations Cheatsheet

### Start daemon manually

```bash
SENSEI_VAULT_PATH="/path/to/Obsidian Vault" \
python -m terminalsensei.cli.main --daemon
```

### One-command setup for new user

```bash
bash scripts/setup.sh "/path/to/Obsidian Vault"
```

### Common checks

```bash
python -m compileall terminalsensei
python -m terminalsensei.cli.main --help
```

---

## 12. Future Improvements You Can Mention

1. Systemd/user-service generation for daemon lifecycle management.
2. Smarter conflict cleanup for stale root-level `Commands/*.md` files.
3. Optional telemetry-free diagnostics command (`sensei doctor`) for setup health.
4. Incremental index update strategy to reduce full-file rewrites for very large books.

---

## 13. Final Narrative (Interview-ready)

You can position this project as:

"A production-minded developer tooling system where I handled both feature implementation and reliability hardening. I designed asynchronous architecture, data modeling, and UX documentation, then debugged real-world race/path issues and solved them with deterministic linking, environment bootstrap automation, and process-level locking."
