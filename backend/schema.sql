CREATE TABLE IF NOT EXISTS specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id INTEGER NOT NULL REFERENCES specs(id),
    line_number INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    statement TEXT NOT NULL,
    section TEXT,
    uppercase_keywords TEXT NOT NULL DEFAULT '[]',
    lowercase_keywords TEXT NOT NULL DEFAULT '[]',
    UNIQUE(spec_id, line_number)
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id INTEGER NOT NULL REFERENCES specs(id),
    line_number INTEGER NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    suggested_rewrite TEXT NOT NULL,
    check_id TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rewrites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id INTEGER NOT NULL REFERENCES specs(id),
    line_number INTEGER NOT NULL,
    rewritten_text TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(spec_id, line_number)
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    total_cases INTEGER NOT NULL,
    true_positives INTEGER NOT NULL,
    false_positives INTEGER NOT NULL,
    false_negatives INTEGER NOT NULL,
    true_positive_ratio REAL NOT NULL,
    detection_coverage_ratio REAL NOT NULL,
    per_case_json TEXT NOT NULL
);
