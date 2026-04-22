"""Suggestion engine based on usage behavior."""

from __future__ import annotations

import sqlite3
from typing import List

from terminalsensei.core.parser import parse_command


def _tip_cat_pipe_grep(raw_command: str) -> str | None:
    if "| grep " not in raw_command or not raw_command.strip().startswith("cat "):
        return None
    left, _, right = raw_command.partition("|")
    left_parsed = parse_command(left.strip())
    right_parsed = parse_command(right.strip())
    if not left_parsed or not right_parsed:
        return None
    if left_parsed.name != "cat" or right_parsed.name != "grep":
        return None
    if len(left_parsed.args) != 1:
        return None
    if right_parsed.args:
        pattern = " ".join(right_parsed.args)
        return f'Use `grep {pattern} {left_parsed.args[0]}` instead of `cat ... | grep ...`.'
    return None


def _tip_grep_flags(raw_command: str) -> str | None:
    parsed = parse_command(raw_command)
    if not parsed or parsed.name != "grep":
        return None
    flags = set(parsed.flags)
    missing = []
    if "-n" not in flags:
        missing.append("-n")
    if "-i" not in flags:
        missing.append("-i")
    if not missing:
        return None
    return f"Consider `grep {' '.join(missing)} ...` for line numbers and case-insensitive search."


def generate_tips(connection: sqlite3.Connection, limit: int = 30) -> List[str]:
    rows = connection.execute(
        """
        SELECT raw_command
        FROM logs
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    tips: List[str] = []
    seen = set()
    for row in rows:
        cmd = row[0]
        for tip_fn in (_tip_cat_pipe_grep, _tip_grep_flags):
            tip = tip_fn(cmd)
            if tip and tip not in seen:
                tips.append(tip)
                seen.add(tip)

    grep_usage = connection.execute(
        "SELECT usage_count FROM commands WHERE name = 'grep'"
    ).fetchone()
    rg_usage = connection.execute(
        "SELECT usage_count FROM commands WHERE name = 'rg'"
    ).fetchone()
    grep_count = int(grep_usage[0]) if grep_usage else 0
    rg_count = int(rg_usage[0]) if rg_usage else 0
    if grep_count >= 10 and rg_count == 0:
        tips.append("You use `grep` frequently; try `rg` (ripgrep) for faster recursive search.")

    return tips
