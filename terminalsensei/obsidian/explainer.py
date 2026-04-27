"""Built-in knowledge base for command explanations."""

from __future__ import annotations

from typing import TypedDict


class CommandInfo(TypedDict):
    """Structure for command information."""

    meaning: str
    when: str
    tips: list[str]
    alternatives: list[str]
    pattern: str


# Built-in knowledge base of common commands
COMMAND_KNOWLEDGE: dict[str, CommandInfo] = {
    "ls": {
        "meaning": "List directory contents",
        "when": "View files and folders in current or specified directory",
        "tips": [
            "-l: long format with permissions and sizes",
            "-a: show hidden files (starting with .)",
            "-h: human-readable file sizes",
            "-S: sort by file size",
        ],
        "alternatives": ["exa (faster, colored)", "tree (hierarchical view)"],
        "pattern": "ls [options] [path]",
    },
    "grep": {
        "meaning": "Search text for patterns",
        "when": "Find lines matching a pattern in files or output",
        "tips": [
            "-i: case-insensitive search",
            "-n: show line numbers",
            "-r: recursive search in directories",
            "-E: extended regex patterns",
            "-v: invert match (exclude pattern)",
        ],
        "alternatives": ["rg (ripgrep - faster)", "ag (The Silver Searcher)"],
        "pattern": "grep [options] pattern [files]",
    },
    "cd": {
        "meaning": "Change directory",
        "when": "Navigate between directories in the filesystem",
        "tips": [
            "cd .. : go to parent directory",
            "cd ~ : go to home",
            "cd - : go to previous directory",
            "cd /path : absolute path",
        ],
        "alternatives": ["pushd/popd for directory stack management"],
        "pattern": "cd [directory]",
    },
    "cat": {
        "meaning": "Concatenate and display file contents",
        "when": "Read file contents or combine multiple files",
        "tips": [
            "cat > file: create/overwrite file (Ctrl+D to end)",
            "cat >> file: append to file",
            "-n: show line numbers",
        ],
        "alternatives": ["less (paginated)", "bat (colored output)", "head/tail (partial)"],
        "pattern": "cat [files]",
    },
    "find": {
        "meaning": "Search for files in directory tree",
        "when": "Locate files by name, type, size, date, or other criteria",
        "tips": [
            "-name: search by filename",
            "-type f: files only (d for directories)",
            "-mtime: modified time",
            "-exec: run command on results",
        ],
        "alternatives": ["fd (simpler syntax)", "locate (faster, indexed)"],
        "pattern": "find [path] [options] [expression]",
    },
    "chmod": {
        "meaning": "Change file permissions",
        "when": "Modify read/write/execute permissions on files or directories",
        "tips": [
            "755: rwxr-xr-x (typical for executables)",
            "644: rw-r--r-- (typical for files)",
            "-R: recursive (all files in directory)",
            "+x: add execute permission",
        ],
        "alternatives": ["chown (change owner)", "umask (set defaults)"],
        "pattern": "chmod [mode] [files]",
    },
    "sudo": {
        "meaning": "Execute command as superuser",
        "when": "Run commands that require root/admin privileges",
        "tips": [
            "sudo !!: repeat last command with sudo",
            "sudo -i: interactive root shell",
            "-u user: run as specific user",
        ],
        "alternatives": ["su (switch user)", "doas (simpler)"],
        "pattern": "sudo [command]",
    },
    "docker": {
        "meaning": "Container management and orchestration",
        "when": "Build, run, and manage containerized applications",
        "tips": [
            "docker run: create and start container",
            "docker ps: list running containers",
            "docker logs: view container output",
            "docker build -t name .: build from Dockerfile",
        ],
        "alternatives": ["podman (rootless)", "containerd"],
        "pattern": "docker [command] [options]",
    },
    "git": {
        "meaning": "Version control system",
        "when": "Track changes, collaborate, and manage code history",
        "tips": [
            "git add .: stage all changes",
            "git commit -m 'msg': commit changes",
            "git push: upload to remote",
            "git pull: fetch and merge",
            "git log: view history",
        ],
        "alternatives": ["mercurial (hg)", "fossil"],
        "pattern": "git [subcommand] [options]",
    },
    "python": {
        "meaning": "Python interpreter and runtime",
        "when": "Run Python scripts or start interactive shell",
        "tips": [
            "-m module: run module as script",
            "-c 'code': execute code directly",
            "-i: interactive mode after script",
            "pip: package manager (use python -m pip)",
        ],
        "alternatives": ["python3 (explicit version)", "pypy (faster)"],
        "pattern": "python [options] [script]",
    },
    "echo": {
        "meaning": "Print text to standard output",
        "when": "Display messages, variables, or text output",
        "tips": [
            "-n: don't print newline",
            "-e: interpret escape sequences (\\n, \\t)",
            "$VAR: expand variables",
        ],
        "alternatives": ["printf (more control)"],
        "pattern": "echo [options] [text]",
    },
    "cp": {
        "meaning": "Copy files or directories",
        "when": "Duplicate files or entire directory trees",
        "tips": [
            "-r: recursive (copy directories)",
            "-i: interactive (ask before overwrite)",
            "-v: verbose (show what's copied)",
        ],
        "alternatives": ["rsync (better for backups)", "scp (remote copy)"],
        "pattern": "cp [options] source destination",
    },
    "mv": {
        "meaning": "Move or rename files",
        "when": "Relocate files to new location or rename them",
        "tips": [
            "-i: interactive (ask before overwrite)",
            "-v: verbose",
            "Works across filesystems",
        ],
        "alternatives": ["rename (batch rename)"],
        "pattern": "mv [options] source destination",
    },
    "rm": {
        "meaning": "Remove files or directories",
        "when": "Delete files (WARNING: no recovery)",
        "tips": [
            "-r: recursive (delete directories)",
            "-f: force (no prompts)",
            "-i: interactive (ask each file)",
            "Use with caution! No trash/recycle bin",
        ],
        "alternatives": ["trash (safe delete)", "rm -i (safer)"],
        "pattern": "rm [options] [files]",
    },
    "curl": {
        "meaning": "Transfer data using URLs",
        "when": "Download files, test APIs, or transfer data",
        "tips": [
            "-O: save with original filename",
            "-o file: save to specific name",
            "-X POST: use POST method",
            "-H 'Header': add custom headers",
            "-d data: send data",
        ],
        "alternatives": ["wget (simpler)", "httpie (human-friendly)"],
        "pattern": "curl [options] [URL]",
    },
    "tar": {
        "meaning": "Archive files and directories",
        "when": "Create or extract compressed backups",
        "tips": [
            "-c: create archive",
            "-x: extract archive",
            "-v: verbose",
            "-z: gzip compression",
            "-j: bzip2 compression",
        ],
        "alternatives": ["zip (cross-platform)", "7z (better compression)"],
        "pattern": "tar [options] [files]",
    },
    "less": {
        "meaning": "Pager for viewing large text files",
        "when": "Read files page-by-page with search capability",
        "tips": [
            "space: next page",
            "b: previous page",
            "/: search forward",
            "?: search backward",
            "q: quit",
        ],
        "alternatives": ["more (simpler)", "bat (with syntax highlighting)"],
        "pattern": "less [file]",
    },
    "make": {
        "meaning": "Build automation tool",
        "when": "Compile code, run build tasks defined in Makefile",
        "tips": [
            "make: run default target",
            "make target: run specific target",
            "-B: force rebuild",
            "-n: dry-run (show commands)",
        ],
        "alternatives": ["cmake", "meson", "build tools specific to language"],
        "pattern": "make [options] [target]",
    },
    "man": {
        "meaning": "Manual pages for commands",
        "when": "Read documentation for command-line tools",
        "tips": [
            "man command: show manual",
            "man -k keyword: search by keyword",
            "man 3 function: C library function",
        ],
        "alternatives": ["--help flag", "info", "tldr"],
        "pattern": "man [section] [command]",
    },
    "file": {
        "meaning": "Determine file type and encoding",
        "when": "Identify what type of file something is without relying on extension",
        "tips": [
            "-i: show MIME type",
            "-b: brief mode (no filename prefix)",
            "-L: follow symbolic links",
            "-z: examine compressed files",
            "-r: don't stop at first match",
        ],
        "alternatives": ["stat (show file metadata)", "head (view contents)", "file-info scripts"],
        "pattern": "file [options] filename",
    },
}


def get_explanation(command: str) -> dict:
    """
    Get explanation for a command.

    Args:
        command: Command name (lowercase)

    Returns:
        Dict with: meaning, when, tips, alternatives, pattern
        Returns minimal dict if command not in knowledge base.
    """
    normalized = command.lower().strip()

    if normalized in COMMAND_KNOWLEDGE:
        return COMMAND_KNOWLEDGE[normalized]

    # Fallback for unknown commands
    return {
        "meaning": f"Command: {command}",
        "when": "Use terminal to explore this command's capabilities",
        "tips": [f"Run `{command} --help` for more information"],
        "alternatives": [],
        "pattern": f"{command} [options] [arguments]",
    }
