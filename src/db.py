"""
Tiny SQLite store for songs and fingerprints.
Schema:
  songs (id INTEGER PRIMARY KEY, name TEXT, path TEXT)
  fingerprints (hash TEXT, song_id INTEGER, offset INTEGER)
This is intentionally minimal for prototyping; later we'll add indexes and optimizations.
"""
import sqlite3
from typing import List, Tuple

class FingerprintDB:
    def __init__(self, path="fingerprints.db"):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self._ensure_schema()

    def _ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                name TEXT,
                path TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                hash TEXT,
                song_id INTEGER,
                offset INTEGER
            )
        """)
        # Make a simple index to speed lookups
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints(hash)")
        self.conn.commit()

    def insert_song(self, name: str, path: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO songs (name, path) VALUES (?, ?)", (name, path))
        self.conn.commit()
        return cur.lastrowid

    def insert_fingerprints(self, song_id: int, hashes: List[Tuple[str,int]]):
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT INTO fingerprints (hash, song_id, offset) VALUES (?, ?, ?)",
            [(h, song_id, int(offset)) for h, offset in hashes]
        )
        self.conn.commit()

    def find_hash(self, h: str) -> List[Tuple[int,int]]:
        """
        Return list of (song_id, offset) matching hash h
        """
        cur = self.conn.cursor()
        cur.execute("SELECT song_id, offset FROM fingerprints WHERE hash = ?", (h,))
        return cur.fetchall()

    def close(self):
        self.conn.close()
