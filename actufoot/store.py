import sqlite3
from pathlib import Path


def init_db(path: str = "data/seen.db") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS seen (article_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()


def is_seen(conn: sqlite3.Connection, article_id: str) -> bool:
    cur = conn.execute("SELECT 1 FROM seen WHERE article_id = ?", (article_id,))
    return cur.fetchone() is not None


def mark_seen(conn: sqlite3.Connection, article_id: str) -> None:
    conn.execute("INSERT OR IGNORE INTO seen (article_id) VALUES (?)", (article_id,))
    conn.commit()


def seed_seen(conn: sqlite3.Connection, article_ids: list[str]) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO seen (article_id) VALUES (?)",
        [(i,) for i in article_ids],
    )
    conn.commit()
