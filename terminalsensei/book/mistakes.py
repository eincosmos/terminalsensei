"""Mistake detection and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import difflib
import os
from pathlib import Path
import sqlite3
from typing import Iterable, List


@dataclass(frozen=True)
class MistakeRecord:
    wrong_command: str
    corrected_command: str | None
    timestamp: int


def get_known_commands(connection: sqlite3.Connection) -> List[str]:
    rows = connection.execute("SELECT name FROM commands").fetchall()
    known = {row[0] for row in rows if row[0]}
    for path in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(path)
        if not p.is_dir():
            continue
        try:
            for child in p.iterdir():
                if child.is_file() and os.access(child, os.X_OK):
                    known.add(child.name)
        except OSError:
            continue
    return sorted(known)


def suggest_correction(wrong_command: str, candidates: Iterable[str]) -> str | None:
    if not wrong_command:
        return None
    name = wrong_command.strip().split()[0]
    if not name:
        return None
    suggestion = difflib.get_close_matches(name, list(candidates), n=1, cutoff=0.6)
    if not suggestion:
        return None
    if len(wrong_command.strip().split()) == 1:
        return suggestion[0]
    suffix = " ".join(wrong_command.strip().split()[1:])
    return f"{suggestion[0]} {suffix}".strip()


def recent_mistakes(connection: sqlite3.Connection, limit: int = 20) -> List[MistakeRecord]:
    rows = connection.execute(
        """
        SELECT wrong_command, corrected_command, timestamp
        FROM mistakes
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        MistakeRecord(
            wrong_command=row[0],
            corrected_command=row[1],
            timestamp=row[2],
        )
        for row in rows
    ]
