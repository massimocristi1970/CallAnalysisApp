import os
import sqlite3
import time
from analyser import get_sentiment

DB_PATH = os.getenv("CALL_ANALYSIS_DB", "call_analysis.db")
TARGET_SENTIMENT_VERSION = 1  # bump this when sentiment logic changes

def ensure_meta_table(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS app_meta (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()

def get_meta(conn, key, default=None):
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else default

def set_meta(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()

def recalculate_sentiment(conn):
    cur = conn.cursor()
    cur.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL")
    calls = cur.fetchall()
    total = len(calls)
    if total == 0:
        print("No calls to process.")
        return

    print(f"Recalculating sentiment for {total} calls...")
    updated = 0
    for call_id, transcript in calls:
        if transcript and transcript.strip():
            new_sentiment = get_sentiment(transcript)
            cur.execute("UPDATE calls SET sentiment = ? WHERE call_id = ?", (new_sentiment, call_id))
            updated += 1
            if updated % 100 == 0:
                conn.commit()
                print(f"  Processed {updated}/{total}")
    conn.commit()
    print(f"✅ Done.  Updated sentiment for {updated} calls.")

def run_if_needed():
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    try:
        # Optional: switch to WAL for better concurrency
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass

        ensure_meta_table(conn)

        # Acquire a write lock so only one instance recalculates at once
        try:
            conn.execute("BEGIN IMMEDIATE;")
        except sqlite3.OperationalError:
            # If another process holds lock, wait a bit and try once more
            time.sleep(1)
            conn.execute("BEGIN IMMEDIATE;")

        current = get_meta(conn, "sentiment_version", "0")
        if int(current) < TARGET_SENTIMENT_VERSION:
            print(f"Sentiment version {current} < {TARGET_SENTIMENT_VERSION} -> running recalculation")
            try:
                recalculate_sentiment(conn)
                set_meta(conn, "sentiment_version", TARGET_SENTIMENT_VERSION)
            except Exception:
                conn.execute("ROLLBACK;")
                raise
        else:
            print("Sentiment recalculation not required (version up-to-date).")

        conn.execute("COMMIT;")
    finally:
        conn.close()

if __name__ == "__main__":
    run_if_needed()