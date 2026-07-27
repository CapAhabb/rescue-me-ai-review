from pathlib import Path
import sqlite3


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "database" / "migrations"


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def migrate(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    applied = {
        row["version"]
        for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
    }
    for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = migration.name
        if version in applied:
            continue
        connection.executescript(migration.read_text())
        connection.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
    connection.commit()
