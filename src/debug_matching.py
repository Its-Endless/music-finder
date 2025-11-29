# diagnostic for matching — save as src/debug_matching.py
import sqlite3
import sys
from collections import Counter
from src.fingerprint import fingerprint_file

DB_PATH = "fingerprints.db"

def load_some_db_hashes(limit=20):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hash, song_id, offset FROM fingerprints LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def load_all_db_hashes(sample_limit=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT hash FROM fingerprints")
    rows = cur.fetchall()
    conn.close()
    hashes = [r[0] for r in rows]
    if sample_limit:
        return hashes[:sample_limit], len(hashes)
    return hashes, len(hashes)

def main(query_path):
    print("1) Generating query hashes (first 40 shown):")
    hashes = fingerprint_file(query_path, song_name=None, do_store=False, db_path=DB_PATH)
    print(f" -> Query produced {len(hashes)} hashes")
    for i, (h, t) in enumerate(hashes[:40], start=1):
        print(f"{i:3d}: hash={h}  t={t}")

    print("\n2) Showing some DB rows (first 30 rows):")
    db_rows = load_some_db_hashes(limit=30)
    for i, row in enumerate(db_rows, start=1):
        print(f"{i:3d}: hash={row[0]}  song_id={row[1]}  offset={row[2]}")

    print("\n3) Comparing sets (counts + intersection sample):")
    db_hashes, db_total = load_all_db_hashes(sample_limit=1000)
    query_hashes = [h for h, _ in hashes]
    print(f" DB total hashes = {db_total}")
    print(f" Query total hashes = {len(query_hashes)}")
    db_set = set(db_hashes)
    q_set = set(query_hashes)
    inter = db_set & q_set
    print(f" Intersection count = {len(inter)}")
    if len(inter) > 0:
        print(" Sample matching hashes (up to 20):")
        for i, h in enumerate(list(inter)[:20], start=1):
            print(f" {i:2d}: {h}")
    else:
        print(" No hash strings overlap between query and DB (0 intersection).")
    # also show a small frequency distribution of top hashes in DB
    print("\n4) Top 10 most common DB hashes (sample):")
    if db_total > 0:
        # count frequency in DB (careful with large DBs)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT hash, COUNT(*) as c FROM fingerprints GROUP BY hash ORDER BY c DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        for i, (h, c) in enumerate(rows, start=1):
            print(f" {i:2d}: count={c} hash={h}")
    else:
        print(" DB appears empty.")
    print("\nDiagnostic complete.")
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m src.debug_matching path/to/query.wav")
        sys.exit(1)
    main(sys.argv[1])
