"""Command explainer utilities."""

from __future__ import annotations

import sqlite3
import shutil
import subprocess


def _run_output(command: list[str]) -> str:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def _run_stderr_output(command: list[str]) -> str:
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return out


def _pick_help_description(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith("usage:"):
            continue
        if lower in {"options:", "commands:", "examples:"}:
            continue
        if stripped.startswith("-"):
            continue
        return stripped
    return ""


def _pick_tldr_description(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return ""
    for candidate in lines[1:4]:
        lower = candidate.lower()
        if lower.startswith("more information"):
            continue
        if candidate.startswith("-"):
            continue
        return candidate
    return ""


def get_command_definition(command_name: str) -> str:
    """Best-effort offline command description."""
    if not command_name:
        return "No description available."

    if shutil.which("tldr"):
        out = _run_output(["tldr", command_name, "--color", "never"])
        if out:
            picked = _pick_tldr_description(out)
            if picked:
                return picked

    if shutil.which("whatis"):
        out = _run_output(["whatis", command_name])
        if out:
            return out.splitlines()[0]

    if shutil.which("man"):
        out = _run_output(["man", "-f", command_name])
        if out:
            return out.splitlines()[0]

    out = _run_stderr_output([command_name, "--help"])
    if out:
        picked = _pick_help_description(out)
        if picked:
            return picked

    out = _run_stderr_output([command_name, "-h"])
    if out:
        picked = _pick_help_description(out)
        if picked:
            return picked

    out = _run_output(["bash", "-lc", f"help {command_name}"])
    if out:
        picked = _pick_help_description(out)
        if picked:
            return picked

    return "No description available."


def refresh_missing_descriptions(connection: sqlite3.Connection, limit: int = 100) -> int:
    rows = connection.execute(
        """
        SELECT id, name
        FROM commands
        WHERE description IS NULL OR description = '' OR description = 'No description available.'
        ORDER BY last_used DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    updated = 0
    for row in rows:
        command_id, command_name = row
        description = get_command_definition(command_name)
        if description and description != "No description available.":
            connection.execute(
                "UPDATE commands SET description = ? WHERE id = ?",
                (description, command_id),
            )
            updated += 1

    if updated:
        connection.commit()
    return updated
