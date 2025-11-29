# src/matcher.py
"""
Simple matcher: compute hashes for a query file, look up matching hashes in the DB,
and score candidate songs by offset alignment.

Usage:
    # run as module (recommended)
    python -m src.matcher path/to/query.wav

The script will print the top candidates with a score and the best aligned offset.
"""
import sys
import sqlite3
from collections import Counter, defaultdict
from typing import List, Tuple

# import fingerprint helper to compute query hashes
from src.fingerprint import fingerprint_file

DB_PATH = "fingerprints.db"
TOP_K = 5  # how many top candidates to print

def load_matches_for_hash(conn: sqlite3.Connection, h: str) -> List[Tuple[int,int]]:
    """
    Return list of (song_id, offset) for a given hash string from DB.
    Cast values to int to avoid dtype issues.
    """
    cur = conn.cursor()
    cur.execute("SELECT song_id, offset FROM fingerprints WHERE hash = ?", (h,))
    rows = cur.fetchall()
    # ensure types are ints
    results = []
    for row in rows:
        try:
            song_id = int(row[0])
            offset = int(row[1])
            results.append((song_id, offset))
        except Exception:
            # skip malformed rows
            continue
    return results

def match_query_hashes(hashes: List[Tuple[str,int]], db_path: str = DB_PATH) -> List[Tuple[int,int,int]]:
    """
    Given list of (hash, t_query), find matches in DB and return ranked candidates.

    Returns list of (song_id, score, best_offset_delta)
    """
    conn = sqlite3.connect(db_path)
    # vote structure: votes[song_id][delta] = count
    votes = defaultdict(Counter)
    total_matches = 0

    for h, t_query in hashes:
        rows = load_matches_for_hash(conn, h)
        for song_id, t_db in rows:
            delta = t_db - t_query  # alignment offset (can be negative)
            votes[song_id][delta] += 1
            total_matches += 1

    conn.close()

    # score each song by its highest aligned vote (peak in delta histogram)
    results = []
    for song_id, delta_counts in votes.items():
        best_delta, best_count = delta_counts.most_common(1)[0]
        results.append((song_id, best_count, best_delta))

    # sort by best_count desc
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def print_top_candidates(results: List[Tuple[int,int,int]], db_path: str = DB_PATH, top_k: int = TOP_K):
    if not results:
        print("No matching fingerprints found in DB.")
        return

    # open DB to map song_id -> name
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print(f"Top {min(top_k, len(results))} candidates:")
    for rank, (song_id, score, delta) in enumerate(results[:top_k], start=1):
        cur.execute("SELECT name, path FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()
        name = row[0] if row else "<unknown>"
        path = row[1] if row else "<unknown>"
        print(f"{rank}. song_id={song_id} score={score} best_delta={delta}  name='{name}'  path='{path}'")
    conn.close()

def match_file(query_path: str, db_path: str = DB_PATH):
    print(f"Computing fingerprints for query: {query_path} ...")
    hashes = fingerprint_file(query_path, song_name=None, do_store=False, db_path=db_path)
    if not hashes:
        print("No hashes generated for query — try a longer/louder clip or change fingerprint params.")
        return

    print(f"Query produced {len(hashes)} hashes — searching DB '{db_path}' ...")
    results = match_query_hashes(hashes, db_path=db_path)
    print_top_candidates(results, db_path=db_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.matcher path/to/query.wav")
        sys.exit(1)
    match_file(sys.argv[1])
