"""SQLite tracking and ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
import sqlite3
from typing import Iterable

from terminalsensei.book.mistakes import get_known_commands, suggest_correction
from terminalsensei.core.normalizer import normalize_pattern
from terminalsensei.core.parser import parse_command
from terminalsensei.engine.explainer import get_command_definition
from terminalsensei.obsidian.generator import process_command_to_obsidian


@dataclass(frozen=True)
class LogRecord:
    raw_command: str
    timestamp: int
    exit_code: int


def default_db_path() -> str:
    from pathlib import Path

    path = Path.home() / ".local" / "share" / "terminalsensei" / "sensei.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


class Tracker:
    def __init__(self, db_path: str | None = None, vault_path: str | None = None):
        self.db_path = db_path or default_db_path()
        self.vault_path = vault_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.ensure_schema()

    def ensure_schema(self) -> None:
        schema = resources.files("terminalsensei.db").joinpath("schema.sql").read_text(encoding="utf-8")
        self.connection.executescript(schema)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def process_many(self, records: Iterable[LogRecord]) -> int:
        count = 0
        for record in records:
            self.process_record(record)
            count += 1
        self.connection.commit()
        return count

    def process_record(self, record: LogRecord) -> None:
        raw_command = record.raw_command.strip()
        if not raw_command:
            return

        self.connection.execute(
            """
            INSERT INTO logs(raw_command, timestamp, exit_code)
            VALUES(?, ?, ?)
            """,
            (raw_command, record.timestamp, record.exit_code),
        )

        parsed = parse_command(raw_command)
        if not parsed:
            return

        existing = self.connection.execute(
            "SELECT usage_count, description FROM commands WHERE name = ?",
            (parsed.name,),
        ).fetchone()
        if existing:
            self.connection.execute(
                """
                UPDATE commands
                SET usage_count = usage_count + 1, last_used = ?
                WHERE name = ?
                """,
                (record.timestamp, parsed.name),
            )
        else:
            self.connection.execute(
                """
                INSERT INTO commands(name, usage_count, first_used, last_used, description)
                VALUES(?, 1, ?, ?, ?)
                """,
                (
                    parsed.name,
                    record.timestamp,
                    record.timestamp,
                    get_command_definition(parsed.name),
                ),
            )

        pattern = normalize_pattern(parsed.name, parsed.flags, parsed.args)
        pattern_row = self.connection.execute(
            "SELECT id FROM patterns WHERE pattern_string = ?",
            (pattern,),
        ).fetchone()

        if pattern_row:
            pattern_id = pattern_row[0]
            self.connection.execute(
                "UPDATE patterns SET usage_count = usage_count + 1 WHERE id = ?",
                (pattern_id,),
            )
        else:
            cur = self.connection.execute(
                "INSERT INTO patterns(pattern_string, usage_count) VALUES(?, 1)",
                (pattern,),
            )
            pattern_id = int(cur.lastrowid)

        self.connection.execute(
            """
            INSERT INTO examples(pattern_id, raw_command)
            VALUES(?, ?)
            """,
            (pattern_id, raw_command),
        )

        if record.exit_code != 0:
            correction: str | None = None
            if record.exit_code == 127:
                wrong_name = parsed.name
                candidates = [candidate for candidate in get_known_commands(self.connection) if candidate != wrong_name]
                correction = suggest_correction(raw_command, candidates)
            self.connection.execute(
                """
                INSERT INTO mistakes(wrong_command, corrected_command, timestamp)
                VALUES(?, ?, ?)
                """,
                (raw_command, correction, record.timestamp),
            )

        # Update Obsidian vault if configured
        if self.vault_path:
            try:
                process_command_to_obsidian(raw_command, self.connection, self.vault_path)
            except Exception:
                # Silently fail - don't interrupt logging if vault writing fails
                pass
