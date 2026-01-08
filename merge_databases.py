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

        cursor = local_conn.execute("SELECT COUNT(*) FROM analysis_results")
        before_results = cursor.fetchone()[0]

        # Merge calls table
        cursor = local_conn.execute("""
            INSERT OR IGNORE INTO calls
            SELECT * FROM hf.calls
        """)

        # Merge analysis_results table
        cursor = local_conn.execute("""
            INSERT OR IGNORE INTO analysis_results
            SELECT * FROM hf.analysis_results
        """)

        local_conn.commit()

        # Get counts after merge
        cursor = local_conn.execute("SELECT COUNT(*) FROM calls")
        after_calls = cursor.fetchone()[0]

        cursor = local_conn.execute("SELECT COUNT(*) FROM analysis_results")
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
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_db = os.path.join(script_dir, "call_analysis. db")

    print(f"\n📁 Script location: {script_dir}")
    print(f"📁 Looking for database:  {local_db}")
    print(f"📁 Database exists: {os.path.exists(local_db)}")

    if not os.path.exists(local_db):
        print(f"\n❌ Error: Local database not found")
        print(f"   Expected location: {local_db}")
        input("\nPress Enter to exit...")
        exit(1)

    print(f"\n📁 Local database: {local_db}")
    hf_db = input("📥 Enter path to downloaded HF database: ").strip('"')

    if merge_databases(local_db, hf_db):
        print("\n🎉 Success! You can now view the data in your dashboard.")
    else:
        print("\n❌ Merge failed. Local database unchanged.")

    input("\nPress Enter to exit...")