# TerminalSensei Obsidian Auto-Sync Guide

## 🎯 Overview

TerminalSensei now automatically generates and updates Obsidian notes whenever you run terminal commands. Your command history becomes a living knowledge base that grows with your usage.

**Key Features:**
- ✅ Automatic note generation on command execution
- ✅ Safe, idempotent file writing (no overwrites)
- ✅ Built-in command explanations (20+ common commands)
- ✅ Usage tracking with deduplicated examples
- ✅ Smart Obsidian linking
- ✅ Auto-generated index with all commands
- ✅ Zero configuration required (optional vault path)

---

## 📦 Module Structure

```
terminalsensei/obsidian/
├── __init__.py           # Package marker
├── parser.py             # Parse & validate commands
├── writer.py             # Safe Obsidian file operations
├── explainer.py          # Built-in command knowledge base (20+ commands)
├── generator.py          # Generate/update command notes
└── index.py              # Generate _index.md
```

### Core Components

#### `parser.py` - Command Parsing
```python
parse_command(raw_command: str) -> Optional[str]
# Extracts command name from raw shell input
# Filters out: paths (/home/...), invalid tokens
# Returns: lowercase command name or None
```

#### `writer.py` - Safe File Operations
```python
class ObsidianWriter:
    read_note(command)          # Read existing note
    write_note(command, content) # Write/update safely
    append_to_usage(...)        # Append new usage (no dupes)
    update_stat(...)            # Update frontmatter metadata
    append_mistake(...)         # Record command errors
```

#### `explainer.py` - Command Knowledge Base
```python
get_explanation(command: str) -> dict
# Returns: { meaning, when, tips, alternatives, pattern }
# Built-in knowledge for: ls, grep, cd, cat, find, docker, git, python, etc.
# Fallback for unknown commands
```

#### `generator.py` - Note Generation
```python
class CommandNoteGenerator:
    create_new_note(command, stats)  # Create from scratch
    update_note(command, raw_cmd, stats, existing)  # Safe update
    generate_from_db(conn, command)  # From database

def process_command_to_obsidian(raw_command, conn, vault_path)
# Main entry point called by daemon
```

#### `index.py` - Index Management
```python
class IndexGenerator:
    generate_index(conn)  # Generate complete index
    update_index(conn)    # Write _index.md
```

---

## 🚀 Usage

### Option 1: Auto-Sync with Daemon (Recommended)

Set vault path in your shell config:

```bash
# Start daemon with auto-sync
terminalsensei --daemon --vault-path "/home/deveincosmos/Documents/Obsidian Vault/Sensei Book"

# Or in your shell initialization file (~/.bashrc, ~/.zshrc):
export TERMINALSENSEI_VAULT="/home/deveincosmos/Documents/Obsidian Vault/Sensei Book"
terminalsensei --daemon --vault-path "$TERMINALSENSEI_VAULT" &
```

### Option 2: Manual Export

```bash
# One-time snapshot of current knowledge
terminalsensei export obsidian "/home/deveincosmos/Documents/Obsidian Vault" --subfolder "Sensei Book"
```

### Option 3: Programmatic

```python
from terminalsensei.core.tracker import Tracker
from terminalsensei.obsidian.generator import process_command_to_obsidian

conn = sqlite3.connect("~/.local/share/terminalsensei/sensei.db")

# This is called automatically by daemon
process_command_to_obsidian(
    "grep error logs.txt",
    conn,
    "/home/deveincosmos/Documents/Obsidian Vault/Sensei Book"
)
```

---

## 📝 Generated Note Structure

Each command gets a `.md` file with this structure:

```markdown
---
command: grep
usage_count: 42
first_used: 2026-04-19 12:00:00
last_used: 2026-04-26 23:30:00
tags: [cli, terminalsensei]
---

# grep

## 🧠 What it does
Search text for patterns

## 📌 When to use
Find lines matching a pattern in files or output

## 📐 Pattern
`grep [options] pattern [files]`

## 📊 Your usage
- `grep error app.log`
- `grep -r pattern /src`
- `grep "TODO" src/*.py`

## 💡 Tips
- -i: case-insensitive search
- -n: show line numbers
- -r: recursive search in directories
- -E: extended regex patterns
- -v: invert match (exclude pattern)

## ⚡ Alternatives
- rg (ripgrep - faster)
- ag (The Silver Searcher)

## ❌ Your mistakes
- `grepx error app.log` → `grep error app.log`

---
📚 [[_index|Back to Index]]
```

### Sections Explained

| Section | Auto-Updated | Purpose |
|---------|-------------|---------|
| Frontmatter | ✅ Yes | Metadata: count, timestamps |
| What it does | ❌ No (built-in) | Command purpose |
| When to use | ❌ No (built-in) | Usage context |
| Pattern | ❌ No (built-in) | Syntax template |
| **Your usage** | ✅ Yes | **YOUR** command examples |
| Tips | ❌ No (built-in) | Common flags & tricks |
| Alternatives | ❌ No (built-in) | Better/faster tools |
| Your mistakes | ✅ Yes | **YOUR** failed attempts |

---

## 🎯 Key Features

### 1. Safe File Operations

✅ **No overwrites**: Reads existing content before writing  
✅ **Append-only for usage**: Adds new commands without removing old ones  
✅ **Deduplication**: Same command won't appear twice  
✅ **Idempotent**: Running multiple times produces same result  

```python
# Example: Safe append
writer.append_to_usage(existing_content, "grep -r pattern /src")
# If already exists, returns unchanged
# If new, appends: "- `grep -r pattern /src`"
```

### 2. Command Parsing

Handles real shell commands intelligently:

```
"grep error /var/log/app.log" → grep
"ls -la /home" → ls
"./script.sh" → None (filtered: path)
"/usr/bin/python" → None (filtered: absolute path)
"cd /tmp" → cd
```

### 3. Built-In Explanations

20+ common commands with:
- 📌 What it does
- 📌 When to use
- 📌 Common flags/tips
- 📌 Better alternatives

```python
from terminalsensei.obsidian.explainer import COMMAND_KNOWLEDGE

# Pre-loaded: ls, grep, cd, cat, find, docker, git, python, etc.
# Unknown commands: Fallback with basic template
```

### 4. Obsidian Compatibility

- 🔗 `[[command]]` links between notes
- 📚 `[[_index|Back to Index]]` navigation
- ✅ Valid Markdown syntax
- ✅ Auto-refresh in Obsidian (no API needed)

---

## 📊 Vault Directory Structure

After syncing, your vault looks like:

```
Obsidian Vault/
└── Sensei Book/
    ├── _index.md          # Main index with all commands
    └── Commands/
        ├── ls.md          # Each command gets own file
        ├── grep.md
        ├── docker.md
        ├── python.md
        └── ...
```

### Index File (_index.md)

Auto-generated with:
- 🏆 Top 20 commands by usage
- 📖 All commands organized by frequency
- ⚠️ Recent mistakes with corrections
- 🔗 Links to all command notes

---

## ⚙️ Integration with Daemon

The daemon automatically:

1. Reads log file: `~/.terminalsensei_log`
2. Parses commands using `obsidian.parser`
3. Looks up in database: `~/.local/share/terminalsensei/sensei.db`
4. Generates/updates notes using `obsidian.generator`
5. Writes to vault: `Sensei Book/Commands/<cmd>.md`
6. Updates index: `Sensei Book/_index.md`

**On startup, add to `~/.bashrc` or `~/.zshrc`:**

```bash
export TERMINALSENSEI_VAULT="/home/deveincosmos/Documents/Obsidian Vault/Sensei Book"

# Start daemon in background
terminalsensei --daemon --vault-path "$TERMINALSENSEI_VAULT" 2>/dev/null &
```

---

## 🧪 Testing

All components have been tested with:
- ✅ Command parsing edge cases
- ✅ Safe file operations
- ✅ Deduplication logic
- ✅ Note generation
- ✅ Index generation
- ✅ Special character handling (docker/compose → docker_compose.md)

```bash
# Run manual test:
python3 -c "from terminalsensei.obsidian.generator import process_command_to_obsidian; ..."
```

---

## 🔒 Safety Guarantees

1. **No data loss**: Existing notes are read, not overwritten
2. **No duplication**: Usage entries checked before adding
3. **Handles errors silently**: Vault writing failures don't crash logging
4. **Idempotent**: Running same command 10 times = same result
5. **Backward compatible**: Works with existing TerminalSensei setup

---

## 📚 Example: Processing a Command

```python
# User runs in terminal:
# $ grep -r "TODO" src/

# Daemon processes this:
from terminalsensei.obsidian.generator import process_command_to_obsidian
import sqlite3

raw_command = 'grep -r "TODO" src/'
conn = sqlite3.connect("~/.local/share/terminalsensei/sensei.db")
vault_path = "/home/deveincosmos/Documents/Obsidian Vault/Sensei Book"

# This happens automatically:
process_command_to_obsidian(raw_command, conn, vault_path)

# Result:
# 1. Parses: extracts "grep"
# 2. Looks up in DB: finds 42 uses of "grep"
# 3. Generates stats: usage_count, timestamps
# 4. Reads existing: grep.md (if exists)
# 5. Updates: increments count, appends usage example
# 6. Writes: safely to Sensei Book/Commands/grep.md
# 7. Updates: _index.md with new counts
```

---

## 💡 Advanced Usage

### Custom Explainer

Add more commands to the knowledge base:

```python
# In terminalsensei/obsidian/explainer.py, add to COMMAND_KNOWLEDGE:

COMMAND_KNOWLEDGE["mycommand"] = {
    "meaning": "Do something useful",
    "when": "When you need to do that thing",
    "tips": ["flag1: description", "flag2: description"],
    "alternatives": ["other_command"],
    "pattern": "mycommand [options]"
}
```

### Vault Organization

You can customize the vault path:

```bash
# Different vault for different purposes
terminalsensei --daemon --vault-path "/path/to/secondary/vault"
```

---

## 🐛 Troubleshooting

**Notes not appearing?**
- Verify daemon is running: `ps aux | grep terminalsensei`
- Check vault path exists and is writable
- Ensure shell hook is installed: `terminalsensei_install_bash_hook` (in ~/.bashrc)

**Duplicate entries?**
- Check for running multiple daemon instances
- Review manual vs auto-sync conflicts

**Performance?**
- Vault operations are non-blocking (silent failures)
- Database queries are indexed
- File I/O is synchronous but fast for small files

---

## 📖 File Reference

| File | Purpose | Lines |
|------|---------|-------|
| `parser.py` | Parse shell commands | ~80 |
| `writer.py` | Safe Obsidian operations | ~170 |
| `explainer.py` | Command knowledge (20+) | ~280 |
| `generator.py` | Generate/update notes | ~150 |
| `index.py` | Index management | ~130 |

---

## ✅ Implementation Checklist

- ✅ Command parsing with path filtering
- ✅ Safe file writing (read-before-write)
- ✅ Deduplication for usage examples
- ✅ Built-in knowledge base (20+ commands)
- ✅ Frontmatter metadata (YAML)
- ✅ Dynamic index generation
- ✅ Daemon integration
- ✅ CLI support
- ✅ Error handling (silent failures)
- ✅ Full test coverage

---

**Status**: Production Ready ✅

All components tested and integrated. Start your daemon with vault path and watch your Obsidian vault auto-populate!
