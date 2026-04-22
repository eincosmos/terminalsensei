"""Command parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import List


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    flags: List[str]
    args: List[str]
    tokens: List[str]


def parse_command(raw_command: str) -> ParsedCommand | None:
    """Parse a raw shell command into command/flags/args."""
    cmd = (raw_command or "").strip()
    if not cmd:
        return None

    try:
        tokens = shlex.split(cmd, posix=True)
    except ValueError:
        tokens = cmd.split()

    if not tokens:
        return None

    name = tokens[0]
    flags: List[str] = []
    args: List[str] = []
    for token in tokens[1:]:
        if token.startswith("-") and token != "-":
            flags.append(token)
        else:
            args.append(token)

    return ParsedCommand(name=name, flags=flags, args=args, tokens=tokens)
