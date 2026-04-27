"""TerminalSensei command-line interface."""

from __future__ import annotations

import argparse
from datetime import datetime
import sqlite3
import sys
from typing import Iterable

from terminalsensei.book.commands import most_used_commands, recent_usage_examples
from terminalsensei.book.mistakes import recent_mistakes
from terminalsensei.book.patterns import top_patterns
from terminalsensei.core.tracker import Tracker, default_db_path
from terminalsensei.daemon.runner import default_log_path, default_state_path, run_daemon
from terminalsensei.engine.explainer import refresh_missing_descriptions
from terminalsensei.engine.suggester import generate_tips
from terminalsensei.exporters.obsidian import ObsidianExporter
from terminalsensei.obsidian.generator import resolve_book_path


def _format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _open_conn(db_path: str) -> sqlite3.Connection:
    tracker = Tracker(db_path=db_path)
    conn = tracker.connection
    return conn


def _print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def _better_ways_for_command(command_name: str) -> list[str]:
    suggestions = {
        "cat": [
            "less <file> (for large files)",
            "bat <file> (colored output)",
        ],
        "grep": [
            "rg <pattern> <path> (faster recursive search)",
            "grep -n -i <pattern> <file> (line numbers + case-insensitive)",
        ],
        "find": [
            "fd <pattern> <path> (simpler and faster than find for common lookups)",
        ],
        "du": [
            "du -h --max-depth=1 <dir> (human-readable quick summaries)",
        ],
    }
    return suggestions.get(command_name, [])


def cmd_stats(db_path: str) -> int:
    conn = _open_conn(db_path)
    total_logs = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    total_cmds = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    print(f"Logs processed: {total_logs}")
    print(f"Unique commands: {total_cmds}")
    print("")
    print("Top commands:")
    for entry in most_used_commands(conn, limit=15):
        print(f"- {entry.name:<18} {entry.usage_count:>5} uses")
    return 0


def cmd_patterns(db_path: str) -> int:
    conn = _open_conn(db_path)
    patterns = top_patterns(conn, limit=30, examples_per_pattern=3)
    if not patterns:
        print("No patterns found yet. Start the daemon and run more commands.")
        return 0
    for p in patterns:
        print(f"{p.pattern_string}  [{p.usage_count}]")
        for example in p.examples:
            print(f"  - {example}")
        print("")
    return 0


def cmd_tips(db_path: str) -> int:
    conn = _open_conn(db_path)
    tips = generate_tips(conn, limit=50)
    if not tips:
        print("No tips yet. Keep using your terminal to generate learning signals.")
        return 0
    _print_lines(f"- {tip}" for tip in tips)
    return 0


def cmd_book(db_path: str) -> int:
    conn = _open_conn(db_path)
    refresh_missing_descriptions(conn, limit=200)
    top = most_used_commands(conn, limit=10_000)
    if not top:
        print("No commands in your CLI book yet.")
        return 0

    for index, command in enumerate(top):
        print(f"📘 [{index + 1}] Command: {command.name}")
        print("")
        print("🧠 Meaning:")
        print(command.description or "No description available.")
        print("")
        print("📌 Your usage:")
        examples = recent_usage_examples(conn, command.name, limit=3)
        if not examples:
            print(f"- {command.name}")
        else:
            for item in examples:
                print(f"- {item.raw_command}")

        print("")
        print("💡 Better ways:")
        better = _better_ways_for_command(command.name)
        if better:
            for tip in better:
                print(f"- {tip}")
        else:
            print("- Keep using this command; Sensei will add optimization tips as patterns grow.")

        if index < len(top) - 1:
            print("")
            print("─" * 48)
            print("")

    mistakes = recent_mistakes(conn, limit=5)
    if mistakes:
        print("")
        print("⚠️ Recent mistakes:")
        for m in mistakes:
            suffix = f" -> try `{m.corrected_command}`" if m.corrected_command else ""
            print(f"- {_format_ts(m.timestamp)}: `{m.wrong_command}`{suffix}")

    patterns = top_patterns(conn, limit=5, examples_per_pattern=1)
    if patterns:
        print("")
        print("📚 Pattern highlights:")
        for p in patterns:
            print(f"- {p.pattern_string} ({p.usage_count} uses)")
    return 0


def _resolve_book_command_name(connection: sqlite3.Connection, target: str) -> str | None:
    token = target.strip()
    if not token:
        return None

    if token.isdigit():
        index = int(token)
        if index <= 0:
            return None
        rows = connection.execute(
            """
            SELECT name
            FROM commands
            ORDER BY usage_count DESC, last_used DESC
            LIMIT 1 OFFSET ?
            """,
            (index - 1,),
        ).fetchall()
        return rows[0][0] if rows else None
    return token


def cmd_delete(db_path: str, target: str) -> int:
    conn = _open_conn(db_path)
    command_name = _resolve_book_command_name(conn, target)
    if not command_name:
        print(f"Could not resolve command target: {target}")
        return 1

    existing = conn.execute("SELECT 1 FROM commands WHERE name = ?", (command_name,)).fetchone()
    if not existing:
        print(f"Command not found in your book: {command_name}")
        return 1

    conn.execute(
        """
        DELETE FROM examples
        WHERE pattern_id IN (
            SELECT id FROM patterns
            WHERE pattern_string = ? OR pattern_string LIKE ?
        )
        """,
        (command_name, f"{command_name} %"),
    )
    conn.execute(
        "DELETE FROM patterns WHERE pattern_string = ? OR pattern_string LIKE ?",
        (command_name, f"{command_name} %"),
    )
    conn.execute(
        """
        DELETE FROM logs
        WHERE raw_command = ? OR raw_command LIKE ?
        """,
        (command_name, f"{command_name} %"),
    )
    conn.execute(
        """
        DELETE FROM mistakes
        WHERE wrong_command = ? OR wrong_command LIKE ?
           OR corrected_command = ? OR corrected_command LIKE ?
        """,
        (command_name, f"{command_name} %", command_name, f"{command_name} %"),
    )
    conn.execute("DELETE FROM commands WHERE name = ?", (command_name,))
    conn.commit()
    print(f"Deleted command from book: {command_name}")
    return 0


def cmd_clear(db_path: str, vault_path: str | None = None) -> int:
    from pathlib import Path
    
    conn = _open_conn(db_path)
    conn.execute("DELETE FROM examples")
    conn.execute("DELETE FROM patterns")
    conn.execute("DELETE FROM mistakes")
    conn.execute("DELETE FROM logs")
    conn.execute("DELETE FROM commands")
    conn.execute(
        """
        DELETE FROM sqlite_sequence
        WHERE name IN ('examples', 'patterns', 'mistakes', 'logs', 'commands')
        """
    )
    conn.commit()
    
    # Also clear Obsidian vault if configured
    if vault_path:
        book_path = Path(resolve_book_path(vault_path))
        commands_dir = book_path / "Commands"
        if commands_dir.exists():
            for md_file in commands_dir.glob("*.md"):
                md_file.unlink()
        # Also clear index file
        index_file = book_path / "_index.md"
        if index_file.exists():
            index_file.unlink()
    
    print("Cleared all book data.")
    if vault_path:
        print(f"Cleared Obsidian vault: {resolve_book_path(vault_path)}")
    return 0


def cmd_export(db_path: str, target: str, vault_path: str, subfolder: str = "TerminalSensei") -> int:
    conn = _open_conn(db_path)
    
    if target == "obsidian":
        exporter = ObsidianExporter(vault_path, subfolder=subfolder)
        return exporter.export(conn)
    else:
        print(f"Unknown export target: {target}")
        print("Available targets: obsidian")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sensei", description="TerminalSensei CLI mentor.")
    parser.add_argument("--db-path", default=default_db_path(), help="Path to SQLite database.")
    parser.add_argument("--log-path", default=default_log_path(), help="Path to collector log file.")
    parser.add_argument("--state-path", default=default_state_path(), help="Path to daemon state file.")
    parser.add_argument("--daemon", action="store_true", help="Run background daemon.")
    parser.add_argument("--once", action="store_true", help="For daemon mode: process currently available entries then exit.")
    parser.add_argument("--interval", type=float, default=2.0, help="Daemon polling interval in seconds.")
    parser.add_argument("--vault-path", default=None, help="Path to Obsidian vault for auto-sync (optional).")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("stats", help="Show command usage stats.")
    subparsers.add_parser("book", help="Show full CLI knowledge book.")
    subparsers.add_parser("patterns", help="Show normalized command patterns.")
    subparsers.add_parser("tips", help="Show improvement suggestions.")
    subparsers.add_parser("clear", help="Clear all tracked book data.")
    delete_parser = subparsers.add_parser("delete", help="Delete a command from book by index or name.")
    delete_parser.add_argument("target", help="Book index (from `sensei book`) or command name.")
    export_parser = subparsers.add_parser("export", help="Export knowledge base to external format.")
    export_parser.add_argument("target", choices=["obsidian"], help="Export target format (obsidian).")
    export_parser.add_argument("vault_path", help="Path to Obsidian vault root directory.")
    export_parser.add_argument("--subfolder", default="TerminalSensei", help="Subfolder within vault (default: TerminalSensei).")
    daemon_parser = subparsers.add_parser("daemon", help="Run processing daemon.")
    daemon_parser.add_argument("--vault-path", default=None, help="Path to Obsidian vault for auto-sync (optional).")
    return parser


def main(argv: list[str] | None = None) -> int:
    import os
    
    parser = build_parser()
    args = parser.parse_args(argv)

    # Get vault path from: --vault-path flag > SENSEI_VAULT_PATH env var > daemon subcommand option
    vault_path = getattr(args, 'vault_path', None) or os.environ.get('SENSEI_VAULT_PATH')

    if args.daemon or args.command == "daemon":
        run_daemon(
            db_path=args.db_path,
            log_path=args.log_path,
            state_path=args.state_path,
            vault_path=vault_path,
            interval=args.interval,
            once=args.once,
        )
        return 0

    if args.command == "stats":
        return cmd_stats(args.db_path)
    if args.command == "book":
        return cmd_book(args.db_path)
    if args.command == "patterns":
        return cmd_patterns(args.db_path)
    if args.command == "tips":
        return cmd_tips(args.db_path)
    if args.command == "clear":
        return cmd_clear(args.db_path, vault_path)
    if args.command == "delete":
        return cmd_delete(args.db_path, args.target)
    if args.command == "export":
        return cmd_export(args.db_path, args.target, args.vault_path, args.subfolder)

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
