"""Loading of the Letterboxd CSV exports into a local SQLite database."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: GPL-3.0-or-later

import csv
import sqlite3
from pathlib import Path

SCHEMA = """
DROP TABLE IF EXISTS viewing;
DROP TABLE IF EXISTS movie;

CREATE TABLE movie (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER,
    url TEXT,
    UNIQUE (title, year)
);

CREATE TABLE viewing (
    id INTEGER PRIMARY KEY,
    movie_id INTEGER NOT NULL REFERENCES movie (id),
    date TEXT NOT NULL,
    rewatch INTEGER NOT NULL DEFAULT 0,
    tags TEXT
);

CREATE INDEX viewing_movie ON viewing (movie_id);
CREATE INDEX viewing_date ON viewing (date);
"""


def resolve_datadir(path: Path) -> Path:
    """Return the real data directory.

    ``Datadir`` is a git symlink; on systems without symlink support it is
    checked out as a plain file containing the relative target path.
    """
    if path.is_file():
        target = path.read_text(encoding="utf-8").strip()
        path = path.parent / target
    if not path.is_dir():
        raise FileNotFoundError(f"Data directory not found: {path}")
    return path


def _parse_year(value: str) -> int | None:
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _movie_id(conn: sqlite3.Connection, title: str, year: int | None, url: str | None) -> int:
    row = conn.execute("SELECT id FROM movie WHERE title = ? AND year IS ?", (title, year)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO movie (title, year, url) VALUES (?, ?, ?)", (title, year, url))
    return cur.lastrowid


def build_database(datadir: Path, db_path: Path) -> None:
    """(Re)create the SQLite database from the CSV files in ``datadir``."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)

        for row in _read_csv(datadir / "watched.csv"):
            _movie_id(conn, row["Name"], _parse_year(row["Year"]), row.get("Letterboxd URI") or None)

        for row in _read_csv(datadir / "diary.csv"):
            movie_id = _movie_id(conn, row["Name"], _parse_year(row["Year"]), None)
            date = row.get("Watched Date") or row["Date"]
            conn.execute(
                "INSERT INTO viewing (movie_id, date, rewatch, tags) VALUES (?, ?, ?, ?)",
                (movie_id, date, 1 if row.get("Rewatch") == "Yes" else 0, row.get("Tags") or None),
            )

        conn.commit()
    finally:
        conn.close()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
