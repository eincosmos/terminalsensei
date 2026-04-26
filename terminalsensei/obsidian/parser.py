"""Safe command parsing and validation."""

from __future__ import annotations

import re
from typing import Optional


def is_path(token: str) -> bool:
    """Check if token looks like a path."""
    # Absolute paths: /home/... or relative: ./...
    if token.startswith('/') or token.startswith('./') or token.startswith('../'):
        return True
    # Windows paths
    if re.match(r'^[A-Z]:', token):
        return True
    return False


def is_valid_command(token: str) -> bool:
    """Check if token is a valid command name."""
    if not token or len(token) == 0:
        return False

    # Command names should be alphanumeric + some special chars
    if not re.match(r'^[a-zA-Z0-9\-_.]+$', token):
        return False

    return True


def parse_command(raw_command: str) -> Optional[str]:
    """
    Extract command name from raw command.

    Args:
        raw_command: Full command string

    Returns:
        Command name (lowercase) or None if invalid

    Examples:
        "ls -la /home" -> "ls"
        "grep error file.txt" -> "grep"
        "/home/user/script.sh" -> None (path)
        "cd /" -> "cd"
    """
    if not raw_command or not isinstance(raw_command, str):
        return None

    # Split by whitespace, handle pipes
    tokens = raw_command.split()
    if not tokens:
        return None

    first_token = tokens[0]

    # Filter out paths
    if is_path(first_token):
        return None

    # Try to extract command name
    # Handle cases like "command|another" or "command&&another"
    command = re.split(r'[|&;]', first_token)[0].strip()

    if not is_valid_command(command):
        return None

    return command.lower()


def normalize_command(command: str) -> str:
    """
    Normalize command name.

    Args:
        command: Command name

    Returns:
        Normalized (lowercase, trimmed)
    """
    return command.lower().strip()
