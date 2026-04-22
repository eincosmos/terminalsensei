"""Pattern library queries."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import List


@dataclass(frozen=True)
class PatternInfo:
    pattern_id: int
    pattern_string: str
    usage_count: int
    examples: List[str]


def top_patterns(connection: sqlite3.Connection, limit: int = 30, examples_per_pattern: int = 3) -> List[PatternInfo]:
    pattern_rows = connection.execute(
        """
        SELECT id, pattern_string, usage_count
        FROM patterns
        ORDER BY usage_count DESC, id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    data: List[PatternInfo] = []
    for row in pattern_rows:
        example_rows = connection.execute(
            """
            SELECT raw_command
            FROM examples
            WHERE pattern_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (row[0], examples_per_pattern),
        ).fetchall()
        data.append(
            PatternInfo(
                pattern_id=row[0],
                pattern_string=row[1],
                usage_count=row[2],
                examples=[example_row[0] for example_row in example_rows],
            )
        )
    return data
