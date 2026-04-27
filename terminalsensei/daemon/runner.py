"""Background daemon that processes appended shell logs."""

from __future__ import annotations

import json
import fcntl
from pathlib import Path
import time
from typing import List

from terminalsensei.core.tracker import LogRecord, Tracker


def default_log_path() -> str:
    return str(Path.home() / ".terminalsensei_log")


def default_state_path() -> str:
    path = Path.home() / ".local" / "state" / "terminalsensei" / "daemon_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def load_offset(state_path: str) -> int:
    p = Path(state_path)
    if not p.exists():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return int(data.get("offset", 0))


def save_offset(state_path: str, offset: int) -> None:
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"offset": offset}), encoding="utf-8")


def acquire_daemon_lock(state_path: str):
    """Ensure only one daemon instance is processing the same state/log stream."""
    lock_path = Path(state_path).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_handle.close()
        return None
    lock_handle.write(str(Path.cwd()))
    lock_handle.flush()
    return lock_handle


def parse_log_line(line: str) -> LogRecord | None:
    parts = line.rstrip("\n").split("\t", 2)
    if len(parts) != 3:
        return None
    try:
        timestamp = int(parts[0])
        exit_code = int(parts[1])
    except ValueError:
        return None
    raw_command = parts[2].strip()
    if not raw_command:
        return None
    return LogRecord(raw_command=raw_command, timestamp=timestamp, exit_code=exit_code)


def read_new_records(log_path: str, offset: int) -> tuple[List[LogRecord], int]:
    p = Path(log_path)
    if not p.exists():
        return ([], offset)

    records: List[LogRecord] = []
    with p.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        for line in handle:
            record = parse_log_line(line)
            if record is not None:
                records.append(record)
        new_offset = handle.tell()
    return (records, new_offset)


def run_daemon(
    db_path: str | None = None,
    log_path: str | None = None,
    state_path: str | None = None,
    vault_path: str | None = None,
    interval: float = 2.0,
    once: bool = False,
) -> int:
    effective_log_path = log_path or default_log_path()
    effective_state_path = state_path or default_state_path()
    lock_handle = acquire_daemon_lock(effective_state_path)
    if lock_handle is None:
        print(f"Daemon already running for state file: {effective_state_path}")
        return 0

    offset = load_offset(effective_state_path)
    tracker = Tracker(db_path=db_path, vault_path=vault_path)

    try:
        while True:
            if Path(effective_log_path).exists():
                file_size = Path(effective_log_path).stat().st_size
                if file_size < offset:
                    offset = 0
                    save_offset(effective_state_path, offset)

            records, new_offset = read_new_records(effective_log_path, offset)
            if records:
                tracker.process_many(records)
                offset = new_offset
                save_offset(effective_state_path, offset)

            if once:
                return len(records)
            time.sleep(interval)
    finally:
        tracker.close()
        lock_handle.close()
