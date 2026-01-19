"""
Database Merger for Call Analysis App
Merges Hugging Face database into local database

FIXED: Now properly handles call_id conflicts by:
1. Using filename + call_date to detect true duplicates (not call_id)
2. Letting SQLite auto-generate new call_ids for merged records
3. Properly mapping old call_ids to new call_ids for related tables
4. Merging all tables: agents, calls, qa_scores, keywords
"""

import sqlite3
import os
from datetime import datetime


def merge_databases(local_db, hf_db):
    """Merge HF database into local database"""

    # Validate files exist
    if not os.path.exists(local_db):
        print(f"Error: Local database not found: {local_db}")
        return False

    if not os.path.exists(hf_db):
        print(f"Error: HF database not found: {hf_db}")
        return False

    try:
        # Connect to local database
        local_conn = sqlite3.connect(local_db)
        local_conn.row_factory = sqlite3.Row
        local_conn.execute(f"ATTACH '{hf_db}' AS hf")

        # Get counts before merge
        cursor = local_conn.execute("SELECT COUNT(*) FROM calls")
        before_calls = cursor.fetchone()[0]

        cursor = local_conn.execute("SELECT COUNT(*) FROM qa_scores")
        before_qa_scores = cursor.fetchone()[0]

        # Check if keywords table exists in both databases
        cursor = local_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
        local_has_keywords = cursor.fetchone() is not None
        cursor = local_conn.execute("SELECT name FROM hf.sqlite_master WHERE type='table' AND name='keywords'")
        hf_has_keywords = cursor.fetchone() is not None

        before_keywords = 0
        if local_has_keywords:
            cursor = local_conn.execute("SELECT COUNT(*) FROM keywords")
            before_keywords = cursor.fetchone()[0]

        # ============================================================
        # STEP 1: Merge agents table first (needed for foreign keys)
        # ============================================================
        print("\n   Merging agents...")
        
        # Get existing agent names in local db
        cursor = local_conn.execute("SELECT agent_name FROM agents")
        existing_agents = {row[0] for row in cursor.fetchall()}
        
        # Get agents from HF db and insert new ones
        cursor = local_conn.execute("""
            SELECT agent_name, department, start_date, is_active, created_at 
            FROM hf.agents
        """)
        hf_agents = cursor.fetchall()
        
        agents_added = 0
        for agent in hf_agents:
            if agent['agent_name'] not in existing_agents:
                local_conn.execute("""
                    INSERT INTO agents (agent_name, department, start_date, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent['agent_name'], agent['department'], agent['start_date'], 
                      agent['is_active'], agent['created_at']))
                agents_added += 1
        
        local_conn.commit()
        print(f"      Agents added: {agents_added}")

        # ============================================================
        # STEP 2: Build agent_id mapping (HF agent_id -> local agent_id)
        # ============================================================
        # Create mapping from HF agent_id to local agent_id via agent_name
        cursor = local_conn.execute("""
            SELECT hf.agent_id as hf_agent_id, local.agent_id as local_agent_id
            FROM hf.agents hf
            JOIN agents local ON hf.agent_name = local.agent_name
        """)
        agent_id_map = {row['hf_agent_id']: row['local_agent_id'] for row in cursor.fetchall()}

        # ============================================================
        # STEP 3: Get existing calls to detect true duplicates
        # ============================================================
        # Use filename + call_date as the unique identifier for a call
        cursor = local_conn.execute("SELECT filename, call_date FROM calls")
        existing_calls = {(row['filename'], row['call_date']) for row in cursor.fetchall()}
        
        print(f"\n   Existing calls in local db: {len(existing_calls)}")

        # ============================================================
        # STEP 4: Merge calls table (without copying call_id)
        # ============================================================
        print("   Merging calls...")
        
        # Get all calls from HF database
        cursor = local_conn.execute("""
            SELECT call_id, agent_id, filename, call_date, call_type, 
                   duration_minutes, transcript, sentiment, 
                   processing_time_seconds, file_size_mb, created_at
            FROM hf.calls
        """)
        hf_calls = cursor.fetchall()
        
        # Track mapping from old call_id to new call_id
        call_id_map = {}
        calls_added = 0
        calls_skipped = 0
        
        for call in hf_calls:
            # Check if this is a true duplicate (same filename + call_date)
            call_key = (call['filename'], call['call_date'])
            
            if call_key in existing_calls:
                # Skip duplicate - but we need to find its local call_id for related records
                cursor = local_conn.execute(
                    "SELECT call_id FROM calls WHERE filename = ? AND call_date = ?",
                    (call['filename'], call['call_date'])
                )
                existing_call = cursor.fetchone()
                if existing_call:
                    call_id_map[call['call_id']] = existing_call['call_id']
                calls_skipped += 1
                continue
            
            # Map the agent_id to local agent_id
            local_agent_id = agent_id_map.get(call['agent_id'], call['agent_id'])
            
            # Insert the call WITHOUT specifying call_id (let SQLite auto-generate)
            cursor = local_conn.execute("""
                INSERT INTO calls (
                    agent_id, filename, call_date, call_type, 
                    duration_minutes, transcript, sentiment, 
                    processing_time_seconds, file_size_mb, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                local_agent_id, call['filename'], call['call_date'], call['call_type'],
                call['duration_minutes'], call['transcript'], call['sentiment'],
                call['processing_time_seconds'], call['file_size_mb'], call['created_at']
            ))
            
            # Map old call_id to new call_id
            new_call_id = cursor.lastrowid
            call_id_map[call['call_id']] = new_call_id
            calls_added += 1
            existing_calls.add(call_key)  # Add to set to prevent duplicates within same merge
        
        local_conn.commit()
        print(f"      Calls added: {calls_added}")
        print(f"      Calls skipped (duplicates): {calls_skipped}")

        # ============================================================
        # STEP 5: Merge qa_scores table (map call_ids)
        # ============================================================
        print("   Merging QA scores...")
        
        # Get shared columns between local and HF qa_scores (excluding score_id)
        local_cols = [r[1] for r in local_conn.execute("PRAGMA table_info(qa_scores)").fetchall()]
        hf_cols = [r[1] for r in local_conn.execute("PRAGMA hf.table_info(qa_scores)").fetchall()]
        shared_cols = [c for c in local_cols if c in hf_cols and c != 'score_id']
        
        if 'call_id' not in shared_cols:
            raise RuntimeError("qa_scores table must have call_id column")
        
        # Get all qa_scores from HF database
        cols_for_select = ", ".join(shared_cols)
        cursor = local_conn.execute(f"SELECT {cols_for_select} FROM hf.qa_scores")
        hf_qa_scores = cursor.fetchall()
        
        qa_scores_added = 0
        qa_scores_skipped = 0
        
        for score in hf_qa_scores:
            old_call_id = score['call_id']
            
            # Check if we have a mapping for this call_id
            if old_call_id not in call_id_map:
                qa_scores_skipped += 1
                continue
            
            new_call_id = call_id_map[old_call_id]
            
            # Build the insert with mapped call_id
            values = []
            for col in shared_cols:
                if col == 'call_id':
                    values.append(new_call_id)
                else:
                    values.append(score[col])
            
            cols_for_insert = ", ".join(shared_cols)
            placeholders = ", ".join(["?" for _ in shared_cols])
            
            local_conn.execute(f"""
                INSERT INTO qa_scores ({cols_for_insert})
                VALUES ({placeholders})
            """, values)
            qa_scores_added += 1
        
        local_conn.commit()
        print(f"      QA scores added: {qa_scores_added}")
        if qa_scores_skipped > 0:
            print(f"      QA scores skipped (no matching call): {qa_scores_skipped}")

        # ============================================================
        # STEP 6: Merge keywords table (if it exists in both dbs)
        # ============================================================
        keywords_added = 0
        if local_has_keywords and hf_has_keywords:
            print("   Merging keywords...")
            
            # Get shared columns (excluding keyword_id)
            local_kw_cols = [r[1] for r in local_conn.execute("PRAGMA table_info(keywords)").fetchall()]
            hf_kw_cols = [r[1] for r in local_conn.execute("PRAGMA hf.table_info(keywords)").fetchall()]
            shared_kw_cols = [c for c in local_kw_cols if c in hf_kw_cols and c != 'keyword_id']
            
            if 'call_id' in shared_kw_cols:
                # Get all keywords from HF database
                cols_for_select = ", ".join(shared_kw_cols)
                cursor = local_conn.execute(f"SELECT {cols_for_select} FROM hf.keywords")
                hf_keywords = cursor.fetchall()
                
                keywords_skipped = 0
                
                for keyword in hf_keywords:
                    old_call_id = keyword['call_id']
                    
                    # Check if we have a mapping for this call_id
                    if old_call_id not in call_id_map:
                        keywords_skipped += 1
                        continue
                    
                    new_call_id = call_id_map[old_call_id]
                    
                    # Build the insert with mapped call_id
                    values = []
                    for col in shared_kw_cols:
                        if col == 'call_id':
                            values.append(new_call_id)
                        else:
                            values.append(keyword[col])
                    
                    cols_for_insert = ", ".join(shared_kw_cols)
                    placeholders = ", ".join(["?" for _ in shared_kw_cols])
                    
                    local_conn.execute(f"""
                        INSERT INTO keywords ({cols_for_insert})
                        VALUES ({placeholders})
                    """, values)
                    keywords_added += 1
                
                local_conn.commit()
                print(f"      Keywords added: {keywords_added}")
                if keywords_skipped > 0:
                    print(f"      Keywords skipped (no matching call): {keywords_skipped}")
        elif hf_has_keywords and not local_has_keywords:
            print("   Skipping keywords (table doesn't exist in local db)")

        # ============================================================
        # Get final counts
        # ============================================================
        cursor = local_conn.execute("SELECT COUNT(*) FROM calls")
        after_calls = cursor.fetchone()[0]

        cursor = local_conn.execute("SELECT COUNT(*) FROM qa_scores")
        after_qa_scores = cursor.fetchone()[0]

        after_keywords = 0
        if local_has_keywords:
            cursor = local_conn.execute("SELECT COUNT(*) FROM keywords")
            after_keywords = cursor.fetchone()[0]

        local_conn.close()

        # Show results
        print(f"\n{'='*50}")
        print(f"  MERGE COMPLETE!")
        print(f"{'='*50}")
        print(f"   Calls:     {before_calls} -> {after_calls} (+{after_calls - before_calls})")
        print(f"   QA Scores: {before_qa_scores} -> {after_qa_scores} (+{after_qa_scores - before_qa_scores})")
        if local_has_keywords:
            print(f"   Keywords:  {before_keywords} -> {after_keywords} (+{after_keywords - before_keywords})")
        print(f"\n   Local database updated successfully!")

        return True

    except Exception as e:
        print(f"Error during merge: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("  Call Analysis Database Merger")
    print("=" * 50)

    # Use absolute path to be safe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_db = os.path.join(script_dir, "call_analysis.db")

    print(f"\n   Script location: {script_dir}")
    print(f"   Looking for database: {local_db}")
    print(f"   Database exists: {os.path.exists(local_db)}")

    if not os.path.exists(local_db):
        print(f"\n   Error: Local database not found")
        print(f"   Expected location: {local_db}")
        input("\nPress Enter to exit...")
        exit(1)

    print(f"\n   Local database found!")
    print(f"\n   Opening file picker...")
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
        print("\n   No file selected. Exiting.")
        input("\nPress Enter to exit...")
        exit(0)

    print(f"\n   Selected file: {hf_db}")

    if merge_databases(local_db, hf_db):
        print("\n   Success! You can now view the data in your dashboard.")
    else:
        print("\n   Merge failed. Check the error above.")

    input("\nPress Enter to exit...")
