"""Generate and update Obsidian command notes."""

from __future__ import annotations

import sqlite3
from typing import Optional

from terminalsensei.obsidian.writer import ObsidianWriter, format_timestamp
from terminalsensei.obsidian.explainer import get_explanation
from terminalsensei.obsidian.parser import parse_command, normalize_command
from terminalsensei.obsidian.index import IndexGenerator


class CommandNoteGenerator:
    """Generates and maintains Obsidian notes for CLI commands."""

    def __init__(self, writer: ObsidianWriter):
        """
        Initialize generator.

        Args:
            writer: ObsidianWriter instance
        """
        self.writer = writer

    def create_new_note(self, command: str, stats: dict) -> str:
        """
        Create a new command note from scratch.

        Args:
            command: Command name
            stats: Dict with usage_count, first_used, last_used

        Returns:
            Complete markdown content
        """
        info = get_explanation(command)

        # Build note
        lines = []

        # Frontmatter
        frontmatter = self.writer.get_frontmatter(command, stats).rstrip("\n")
        lines.append(frontmatter)
        lines.append("")

        # Title
        lines.append(f"# {command}")
        lines.append("")

        # Description
        lines.append("## 🧠 What it does")
        lines.append(info["meaning"])
        lines.append("")

        # When to use
        lines.append("## 📌 When to use")
        lines.append(info["when"])
        lines.append("")

        # Pattern
        lines.append("## 📐 Pattern")
        lines.append(f"`{info['pattern']}`")
        lines.append("")

        # Usage
        lines.append("## 📊 Your usage")
        lines.append("- *No examples yet. Run the command to populate this.*")
        lines.append("")

        # Tips
        if info.get("tips"):
            lines.append("## 💡 Tips")
            for tip in info["tips"]:
                lines.append(f"- {tip}")
            lines.append("")

        # Alternatives
        if info.get("alternatives"):
            lines.append("## ⚡ Alternatives")
            for alt in info["alternatives"]:
                lines.append(f"- {alt}")
            lines.append("")

        # Mistakes (empty initially)
        lines.append("## ❌ Your mistakes")
        lines.append("- *None recorded yet.*")
        lines.append("")

        # Navigation
        lines.append("---")
        lines.append("📚 [[_index|Back to Index]]")

        return "\n".join(lines)

    def update_note(
        self,
        command: str,
        raw_command: str,
        stats: dict,
        existing_content: Optional[str] = None,
    ) -> str:
        """
        Update existing note with new usage and stats.

        Args:
            command: Command name
            raw_command: Full raw command executed
            stats: Dict with updated usage_count, first_used, last_used
            existing_content: Existing note content (if any)

        Returns:
            Updated markdown content
        """
        if not existing_content:
            content = self.create_new_note(command, stats)
            # Append the raw command even on first creation
            if raw_command != command:
                content = self.writer.append_to_usage(content, raw_command)
            return content

        # Update frontmatter
        content = self.writer.update_stat(
            existing_content, "usage_count", str(stats["usage_count"])
        )
        content = self.writer.update_stat(
            content, "last_used", stats["last_used"]
        )

        # Append usage if it's a new one
        if raw_command != command:  # Only if it's not just the command name
            content = self.writer.append_to_usage(content, raw_command)

        return content

    def generate_from_db(
        self,
        conn: sqlite3.Connection,
        command: str,
    ) -> str:
        """
        Generate note from database stats.

        Args:
            conn: SQLite connection
            command: Command name

        Returns:
            Markdown content
        """
        row = conn.execute(
            "SELECT usage_count, first_used, last_used FROM commands WHERE name = ?",
            (command,),
        ).fetchone()

        if not row:
            return ""

        usage_count, first_used, last_used = row
        stats = {
            "usage_count": usage_count,
            "first_used": format_timestamp(first_used),
            "last_used": format_timestamp(last_used),
        }

        existing = self.writer.read_note(command)
        return self.update_note(command, command, stats, existing)


def process_command_to_obsidian(
    raw_command: str,
    conn: sqlite3.Connection,
    vault_path: str,
) -> bool:
    """
    Process a command and update Obsidian vault.

    This is the main entry point for command processing.

    Args:
        raw_command: Full command from shell
        conn: SQLite database connection
        vault_path: Path to Obsidian vault

    Returns:
        True if note was created/updated, False otherwise

    Example:
        >>> process_command_to_obsidian("grep error logs.txt", db_conn, "/path/to/vault")
        True
    """
    from pathlib import Path
    
    # Parse command
    command = parse_command(raw_command)
    if not command:
        return False

    # Get stats from database
    row = conn.execute(
        "SELECT usage_count, first_used, last_used FROM commands WHERE name = ?",
        (command,),
    ).fetchone()

    if not row:
        return False  # Not in database yet

    usage_count, first_used, last_used = row

    # Initialize writer and generator
    writer = ObsidianWriter(vault_path)
    generator = CommandNoteGenerator(writer)

    # Generate/update note
    stats = {
        "usage_count": usage_count,
        "first_used": format_timestamp(first_used),
        "last_used": format_timestamp(last_used),
    }

    existing_content = writer.read_note(command)
    new_content = generator.update_note(command, raw_command, stats, existing_content)

    # Write to vault
    writer.write_note(command, new_content)

    # Update index file
    index_path = Path(vault_path) / "_index.md"
    index_gen = IndexGenerator(index_path)
    index_gen.update_index(conn)

    return True
