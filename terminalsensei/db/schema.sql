CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    first_used INTEGER NOT NULL,
    last_used INTEGER NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_string TEXT NOT NULL UNIQUE,
    usage_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    raw_command TEXT NOT NULL,
    FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mistakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wrong_command TEXT NOT NULL,
    corrected_command TEXT,
    timestamp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_command TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    exit_code INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_mistakes_timestamp ON mistakes(timestamp);
CREATE INDEX IF NOT EXISTS idx_examples_pattern_id ON examples(pattern_id);
