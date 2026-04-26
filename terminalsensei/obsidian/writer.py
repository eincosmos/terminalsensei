"""Safe command-aware file writing for Obsidian vaults."""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import Optional


def sanitize_filename(command: str) -> str:
    """Convert command name to safe filename for Obsidian."""
    # Replace problematic characters
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', command)
    sanitized = sanitized.strip('. ')
    return sanitized or 'command'


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp to readable format."""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


class ObsidianWriter:
    """Manages safe reading and writing of Obsidian vault files."""

    def __init__(self, vault_path: str | Path, folder: str = "Commands"):
        """
        Initialize writer.

        Args:
            vault_path: Obsidian vault root directory (should be the Sensei Book folder)
            folder: Subfolder within vault (default: Commands)
        """
        self.vault_path = Path(vault_path)
        self.folder_path = self.vault_path / folder
        self.index_path = self.vault_path / "_index.md"

    def ensure_directory(self) -> None:
        """Create directory structure if needed."""
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def get_note_path(self, command: str) -> Path:
        """Get the full path for a command note."""
        safe_name = sanitize_filename(command)
        return self.folder_path / f"{safe_name}.md"

    def read_note(self, command: str) -> Optional[str]:
        """Read existing note, return None if doesn't exist."""
        note_path = self.get_note_path(command)
        if note_path.exists():
            return note_path.read_text(encoding="utf-8")
        return None

    def write_note(self, command: str, content: str) -> None:
        """Write note to disk. Safe and idempotent."""
        self.ensure_directory()
        note_path = self.get_note_path(command)
        note_path.write_text(content, encoding="utf-8")

    def get_frontmatter(self, command: str, stats: dict) -> str:
        """Generate YAML frontmatter."""
        return f"""---
command: {command}
usage_count: {stats.get('usage_count', 1)}
first_used: {stats.get('first_used', '')}
last_used: {stats.get('last_used', '')}
tags: [cli, terminalsensei]
---
"""

    def parse_frontmatter(self, content: str) -> dict:
        """Extract metadata from frontmatter."""
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {}

        data = {}
        for line in match.group(1).split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data

    def extract_section(self, content: str, section: str) -> Optional[str]:
        """Extract specific section from note."""
        pattern = rf'^## {re.escape(section)}.*?(?=^## |\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(0)
        return None

    def append_to_usage(self, content: str, raw_command: str) -> str:
        """Append command to usage section without duplicates."""
        # Parse sections
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        frontmatter_end = frontmatter_match.end() if frontmatter_match else 0

        # Find "Your usage" section
        usage_match = re.search(
            r'^(## 📊 Your usage.*?)(?=^##|\Z)',
            content[frontmatter_end:],
            re.MULTILINE | re.DOTALL
        )

        if not usage_match:
            # Create section if missing
            return content + f"\n## 📊 Your usage\n- `{raw_command}`\n"

        usage_section = usage_match.group(1)
        # Check if already exists
        if f"`{raw_command}`" in usage_section:
            return content  # Already exists

        # Append new entry while preserving blank line before next section
        # The usage section ends with a blank line before next ##
        # We need to insert the new entry before that blank line
        usage_lines = usage_section.rstrip('\n').split('\n')
        usage_lines.append(f"- `{raw_command}`")
        new_usage = '\n'.join(usage_lines) + '\n'
        
        return (
            content[:frontmatter_end + usage_match.start(1)]
            + new_usage
            + content[frontmatter_end + usage_match.end(1):]
        )

    def update_stat(self, content: str, key: str, value: str) -> str:
        """Update a frontmatter value."""
        pattern = rf'^{key}: .*$'
        return re.sub(pattern, f'{key}: {value}', content, flags=re.MULTILINE)

    def append_mistake(self, content: str, mistake: str, correction: Optional[str] = None) -> str:
        """Append to mistakes section without duplicates."""
        mistakes_match = re.search(
            r'^## ❌ Your mistakes.*?(?=^## |\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )

        entry = f"- `{mistake}`"
        if correction:
            entry += f" → `{correction}`"

        if not mistakes_match:
            # Create section
            return content.rstrip() + f"\n\n## ❌ Your mistakes\n{entry}\n"

        mistakes_section = mistakes_match.group(0)
        if entry in mistakes_section:
            return content  # Already exists

        # Append
        new_mistakes = mistakes_section.rstrip() + f"\n{entry}"
        return content.replace(mistakes_section, new_mistakes)
