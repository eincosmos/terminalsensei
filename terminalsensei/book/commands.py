"""Command knowledge-book views."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import List


@dataclass(frozen=True)
class CommandStats:
    name: str
    usage_count: int
    first_used: int
    last_used: int
    description: str | None


@dataclass(frozen=True)
class CommandUsageExample:
    raw_command: str


def most_used_commands(connection: sqlite3.Connection, limit: int = 20) -> List[CommandStats]:
    rows = connection.execute(
        """
        SELECT name, usage_count, first_used, last_used, description
        FROM commands
        ORDER BY usage_count DESC, last_used DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        CommandStats(
            name=row[0],
            usage_count=row[1],
            first_used=row[2],
            last_used=row[3],
            description=row[4],
        )
        for row in rows
    ]


def recent_usage_examples(connection: sqlite3.Connection, command_name: str, limit: int = 5) -> List[CommandUsageExample]:
    rows = connection.execute(
        """
        SELECT raw_command
        FROM logs
        WHERE raw_command = ? OR raw_command LIKE ? OR raw_command LIKE ?
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (command_name, f"{command_name} %", f"%| {command_name} %", limit),
    ).fetchall()
    return [CommandUsageExample(raw_command=row[0]) for row in rows]


def newest_commands(connection: sqlite3.Connection, limit: int = 20) -> List[CommandStats]:
    rows = connection.execute(
        """
        SELECT name, usage_count, first_used, last_used, description
        FROM commands
        ORDER BY first_used DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        CommandStats(
            name=row[0],
            usage_count=row[1],
            first_used=row[2],
            last_used=row[3],
            description=row[4],
        )
        for row in rows
    ]
