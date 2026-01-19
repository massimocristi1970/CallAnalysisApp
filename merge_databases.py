"""
Database Merger for Call Analysis App
Merges Hugging Face database into local database
"""

import sqlite3
import shutil
import os
from datetime import datetime


def merge_databases(local_db, hf_db):
    """Merge HF database into local database"""

    # Validate files exist
    if not os.path.exists(local_db):
        print(f"❌ Error: Local database not found:  {local_db}")
        return False

    if not os.path.exists(hf_db):
        print(f"❌ Error: HF database not found: {hf_db}")
        return False

    # Backup local database first
    backup_name = f"call_analysis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(local_db, backup_name)
    print(f"✅ Backup created:  {backup_name}")

    try:
        # Connect to local database
        local_conn = sqlite3.connect(local_db)
        local_conn.execute(f"ATTACH '{hf_db}' AS hf")

        # Get counts before merge
        cursor = local_conn.execute("SELECT COUNT(*) FROM calls")
        before_calls = cursor.fetchone()[0]

        cursor = local_conn.execute("SELECT COUNT(*) FROM qa_scores")
        before_results = cursor.fetchone()[0]

        # Merge calls table (HF schema has fewer columns than local)
        cursor = local_conn.execute("""
            INSERT OR IGNORE INTO calls (
                call_id,
                agent_id,
                filename,
                call_date,
                call_type,
                duration_minutes,
                transcript,
                sentiment,
                processing_time_seconds,
                file_size_mb,
                created_at
            )
            SELECT call_id,
                agent_id,
                filename,
                call_date,
                call_type,
                duration_minutes,
                transcript,
                sentiment,
                processing_time_seconds,
                file_size_mb,
                created_at
            FROM hf.calls
        """)

        # Merge qa_scores table (schema-safe)
        local_cols = [r[1] for r in local_conn.execute("PRAGMA table_info(qa_scores)").fetchall()]
        hf_cols = [r[1] for r in local_conn.execute("PRAGMA table_info(hf.qa_scores)").fetchall()]
        shared = [c for c in local_cols if c in hf_cols]

        if not shared:
            raise RuntimeError("No shared columns found between local qa_scores and hf.qa_scores")

        cols_csv = ", ".join(shared)

        cursor = local_conn.execute(f"""
            INSERT OR IGNORE INTO qa_scores ({cols_csv})
            SELECT {cols_csv} FROM hf.qa_scores
        """)

        local_conn.commit()

        # Get counts after merge
        cursor = local_conn.execute("SELECT COUNT(*) FROM calls")
        after_calls = cursor.fetchone()[0]

        cursor = local_conn.execute("SELECT COUNT(*) FROM qa_scores")
        after_results = cursor.fetchone()[0]

        local_conn.close()

        # Show results
        calls_added = after_calls - before_calls
        results_added = after_results - before_results

        print(f"\n✅ Merge Complete!")
        print(f"   📊 Calls:  {before_calls} → {after_calls} (+{calls_added})")
        print(f"   📊 Results: {before_results} → {after_results} (+{results_added})")
        print(f"\n✅ Local database updated successfully!")

        return True

    except Exception as e:
        print(f"❌ Error during merge:  {e}")
        print(f"⚠️ Restoring from backup:  {backup_name}")
        shutil.copy(backup_name, local_db)
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("  Call Analysis Database Merger")
    print("=" * 50)

    # Use absolute path to be safe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_db = os.path.join(script_dir, "call_analysis.db")

    print(f"\n📁 Script location: {script_dir}")
    print(f"📁 Looking for database: {local_db}")
    print(f"📁 Database exists: {os.path.exists(local_db)}")

    if not os.path.exists(local_db):
        print(f"\n❌ Error: Local database not found")
        print(f"   Expected location: {local_db}")
        input("\nPress Enter to exit...")
        exit(1)

    print(f"\n📁 Local database found!")
    print(f"\n🔍 Opening file picker...")
    print(f"   Select the downloaded Hugging Face database file")

    # Import file dialog
    from tkinter import Tk, filedialog

    # Hide the root tkinter window
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # Open file picker dialog
    hf_db = filedialog.askopenfilename(
        title="Select Hugging Face Database File",
        filetypes=[
            ("Database files", "*.db"),
            ("All files", "*.*")
        ],
        initialdir=os.path.expanduser("~/Downloads")  # Start in Downloads folder
    )

    root.destroy()

    # Check if user cancelled
    if not hf_db:
        print("\n❌ No file selected.  Exiting.")
        input("\nPress Enter to exit...")
        exit(0)

    print(f"\n📥 Selected file: {hf_db}")

    if merge_databases(local_db, hf_db):
        print("\n🎉 Success! You can now view the data in your dashboard.")
    else:
        print("\n❌ Merge failed. Local database unchanged.")

    input("\nPress Enter to exit...")