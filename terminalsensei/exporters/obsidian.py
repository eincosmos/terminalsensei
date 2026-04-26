"""Obsidian vault exporter for TerminalSensei."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from terminalsensei.book.commands import most_used_commands, recent_usage_examples
from terminalsensei.book.mistakes import recent_mistakes
from terminalsensei.book.patterns import top_patterns


def _sanitize_filename(name: str) -> str:
    """Convert command name to a valid Obsidian filename."""
    # Replace problematic characters with underscores
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', name)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    return sanitized if sanitized else 'command'


def _format_timestamp(ts: int) -> str:
    """Format Unix timestamp to readable date."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _escape_special_chars(text: str) -> str:
    """Escape special markdown characters for Obsidian."""
    # Escape pipes and brackets that might interfere with links
    return text.replace('|', '\\|')


class ObsidianExporter:
    """Exports TerminalSensei knowledge base to Obsidian vault format."""

    def __init__(self, vault_path: str, subfolder: str = "TerminalSensei"):
        """
        Initialize the exporter.

        Args:
            vault_path: Path to the Obsidian vault root
            subfolder: Subfolder within the vault to store sensei data (default: TerminalSensei)
        """
        self.vault_path = Path(vault_path)
        self.subfolder = subfolder
        self.root_dir = self.vault_path / subfolder
        self.commands_dir = self.root_dir / "Commands"
        self.patterns_dir = self.root_dir / "Patterns"

    def prepare_directories(self) -> None:
        """Create necessary directory structure in the vault."""
        self.commands_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def _create_command_note(self, command_name: str, conn: sqlite3.Connection) -> str:
        """Generate markdown content for a single command."""
        # Get command stats
        row = conn.execute(
            "SELECT usage_count, first_used, last_used, description FROM commands WHERE name = ?",
            (command_name,),
        ).fetchone()

        if not row:
            return f"# {command_name}\n\nNo data available."

        usage_count, first_used, last_used, description = row

        # Build the note
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f"command: {command_name}")
        lines.append(f"usage_count: {usage_count}")
        lines.append(f"first_used: {_format_timestamp(first_used)}")
        lines.append(f"last_used: {_format_timestamp(last_used)}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {command_name}")
        lines.append("")

        # Description
        lines.append("## 🧠 Meaning")
        if description:
            lines.append(description)
        else:
            lines.append("*Description not yet available. Use this command more to build context.*")
        lines.append("")

        # Usage Stats
        lines.append("## 📊 Statistics")
        lines.append(f"- **Used**: {usage_count} times")
        lines.append(f"- **First used**: {_format_timestamp(first_used)}")
        lines.append(f"- **Last used**: {_format_timestamp(last_used)}")
        lines.append("")

        # Recent Examples
        examples = recent_usage_examples(conn, command_name, limit=5)
        if examples:
            lines.append("## 📌 Your Recent Usage")
            for example in examples:
                # Escape the command for display
                safe_cmd = _escape_special_chars(example.raw_command)
                lines.append(f"- `{safe_cmd}`")
            lines.append("")

        # Related patterns
        patterns = top_patterns(conn, limit=5, examples_per_pattern=2)
        related_patterns = [p for p in patterns if command_name in p.pattern_string]
        if related_patterns:
            lines.append("## 🔗 Related Patterns")
            for pattern in related_patterns:
                lines.append(f"- `{_escape_special_chars(pattern.pattern_string)}` ({pattern.usage_count} uses)")
            lines.append("")

        # Link back to index
        lines.append("---")
        lines.append(f"📚 [[_index|Back to Index]]")
        lines.append("")

        return "\n".join(lines)

    def _create_index_note(self, conn: sqlite3.Connection) -> str:
        """Generate the main index note with all commands."""
        commands = most_used_commands(conn, limit=10_000)

        lines = []
        lines.append("# TerminalSensei CLI Book")
        lines.append("")
        lines.append("## 📚 Your Command Reference")
        lines.append("")
        lines.append(f"*Synced on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")

        if not commands:
            lines.append("No commands tracked yet. Start using your terminal and run `sensei export obsidian <vault>`.")
            return "\n".join(lines)

        lines.append(f"**Total Commands**: {len(commands)}")
        lines.append("")

        # Top commands
        lines.append("## 🏆 Top Commands")
        lines.append("")
        for i, cmd in enumerate(commands[:20], 1):
            safe_name = _sanitize_filename(cmd.name)
            lines.append(f"{i}. [[{safe_name}|{cmd.name}]] — {cmd.usage_count} uses")
        lines.append("")

        # All commands (grouped by frequency)
        lines.append("## 📖 All Commands")
        lines.append("")

        # High frequency (>50 uses)
        high_freq = [c for c in commands if c.usage_count > 50]
        if high_freq:
            lines.append("### Frequently Used (>50 uses)")
            for cmd in high_freq:
                safe_name = _sanitize_filename(cmd.name)
                lines.append(f"- [[{safe_name}|{cmd.name}]] ({cmd.usage_count})")
            lines.append("")

        # Medium frequency (10-50 uses)
        med_freq = [c for c in commands if 10 <= c.usage_count <= 50]
        if med_freq:
            lines.append("### Medium Frequency (10-50 uses)")
            for cmd in med_freq:
                safe_name = _sanitize_filename(cmd.name)
                lines.append(f"- [[{safe_name}|{cmd.name}]] ({cmd.usage_count})")
            lines.append("")

        # Low frequency (<10 uses)
        low_freq = [c for c in commands if c.usage_count < 10]
        if low_freq:
            lines.append("### Occasional (1-9 uses)")
            for cmd in low_freq:
                safe_name = _sanitize_filename(cmd.name)
                lines.append(f"- [[{safe_name}|{cmd.name}]] ({cmd.usage_count})")
            lines.append("")

        # Recent mistakes section
        mistakes = recent_mistakes(conn, limit=5)
        if mistakes:
            lines.append("## ⚠️ Recent Mistakes")
            lines.append("")
            for mistake in mistakes:
                lines.append(
                    f"- `{_escape_special_chars(mistake.wrong_command)}` ❌"
                )
                if mistake.corrected_command:
                    lines.append(f"  → try `{_escape_special_chars(mistake.corrected_command)}` ✅")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated by TerminalSensei*")
        lines.append("")

        return "\n".join(lines)

    def _create_patterns_note(self, conn: sqlite3.Connection) -> str:
        """Generate a note with all pattern highlights."""
        patterns = top_patterns(conn, limit=50, examples_per_pattern=3)

        lines = []
        lines.append("# Command Patterns")
        lines.append("")
        lines.append("## 🔍 Normalized Syntax Patterns")
        lines.append("")
        lines.append("These are the most common patterns in your command usage.")
        lines.append("")

        if not patterns:
            lines.append("No patterns tracked yet.")
            return "\n".join(lines)

        for i, pattern in enumerate(patterns, 1):
            lines.append(f"### {i}. `{_escape_special_chars(pattern.pattern_string)}`")
            lines.append(f"**Used**: {pattern.usage_count} times")
            lines.append("")
            if pattern.examples:
                lines.append("**Examples:**")
                for example in pattern.examples:
                    lines.append(f"- `{_escape_special_chars(example)}`")
                lines.append("")

        lines.append("---")
        lines.append(f"[[_index|Back to Index]]")
        lines.append("")

        return "\n".join(lines)

    def export(self, conn: sqlite3.Connection) -> int:
        """
        Export the entire knowledge base to Obsidian vault.

        Args:
            conn: SQLite connection to the knowledge database

        Returns:
            0 on success, 1 on failure
        """
        try:
            self.prepare_directories()

            # Export commands
            commands = most_used_commands(conn, limit=10_000)
            print(f"📝 Exporting {len(commands)} commands...")

            for command in commands:
                safe_name = _sanitize_filename(command.name)
                content = self._create_command_note(command.name, conn)
                file_path = self.commands_dir / f"{safe_name}.md"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Export index
            print("📚 Creating index...")
            index_content = self._create_index_note(conn)
            index_path = self.root_dir / "_index.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)

            # Export patterns
            print("🔗 Creating patterns reference...")
            patterns_content = self._create_patterns_note(conn)
            patterns_path = self.patterns_dir / "_patterns.md"
            with open(patterns_path, "w", encoding="utf-8") as f:
                f.write(patterns_content)

            print(f"✅ Export complete! Vault stored at: {self.root_dir}")
            print(f"📖 Start with: {index_path}")

            return 0

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return 1
