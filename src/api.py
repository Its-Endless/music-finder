# src/api.py
import os
import tempfile
from flask import Flask, request, jsonify
from pathlib import Path
from src.fingerprint import fingerprint_file
from src.matcher import match_query_hashes
import sqlite3
from pydub import AudioSegment   # for webm → wav conversion

DB_PATH = "fingerprints.db"
ALLOWED_EXT = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".webm"}

app = Flask(__name__)

def map_song_meta(results, db_path=DB_PATH):
    """Given results [(song_id, score, delta), ...] return enriched dicts with name/path."""
    out = []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    for song_id, score, delta in results:
        cur.execute("SELECT name, path FROM songs WHERE id = ?", (song_id,))
        row = cur.fetchone()
        name = row[0] if row else "<unknown>"
        path = row[1] if row else "<unknown>"
        out.append({
            "song_id": int(song_id),
            "name": name,
            "path": path,
            "score": int(score),
            "best_delta": int(delta),
        })
    conn.close()
    return out


@app.route("/match", methods=["POST"])
def match_upload():
    """
    Accepts multipart/form-data file upload form field named 'file'.
    Returns JSON with top candidates.
    """

    # --- Check for file ---
    if "file" not in request.files:
        return jsonify({"error": "no file provided, use form field 'file'"}), 400

    f = request.files["file"]
    filename = f.filename or "upload"
    ext = Path(filename).suffix.lower()

    if ext and ext not in ALLOWED_EXT:
        return jsonify({"error": f"unsupported file extension: {ext}"}), 400

    # --- Save uploaded file to a temporary path ---
    tmp_dir = tempfile.mkdtemp(prefix="shazam_tmp_")
    tmp_path = Path(tmp_dir) / filename
    f.save(str(tmp_path))

    try:
        # ===============================================================
        # CONVERT WEBM → WAV IF NEEDED
        # ===============================================================
        if tmp_path.suffix.lower() == ".webm":
            wav_path = tmp_path.with_suffix(".wav")
            audio = AudioSegment.from_file(str(tmp_path), format="webm")
            audio.export(str(wav_path), format="wav")
            tmp_path = wav_path  # use wav file from here onwards

        # ===============================================================
        # FINGERPRINT THE FILE
        # ===============================================================
        hashes = fingerprint_file(str(tmp_path), song_name=None, do_store=False, db_path=DB_PATH)

        if not hashes:
            return jsonify({"error": "no hashes generated for the uploaded file (too quiet/short?)"}), 400

        # ===============================================================
        # MATCH AGAINST DB
        # ===============================================================
        results = match_query_hashes(hashes, db_path=DB_PATH)

        if not results:
            return jsonify({
                "query_hashes": len(hashes),
                "matches_found": 0,
                "top_candidates": []
            }), 200

        # Convert DB results into JSON-serializable format
        top = map_song_meta(results, db_path=DB_PATH)

        # Add a normalized score
        total = len(hashes)
        for item in top:
            item["score_normalized"] = round(item["score"] / total, 4)

        return jsonify({
            "query_hashes": total,
            "matches_found": sum([r[1] for r in results]),
            "top_candidates": top
        }), 200

    finally:
        # Cleanup temporary files
        try:
            tmp_path.unlink(missing_ok=True)
            os.rmdir(tmp_dir)
        except:
            pass


@app.route("/")
def index():
    return jsonify({"message": "Shazam-clone API running. POST a file to /match as form field 'file'."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)