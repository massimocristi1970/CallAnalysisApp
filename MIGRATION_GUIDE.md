# Database Migration Guide

This guide explains how to migrate your existing Call Analysis App from SQLite to Supabase, or vice versa.

## Before You Start

**Important**: Always backup your data before performing any migration!

```bash
# Backup your SQLite database
cp call_analysis.db call_analysis.db.backup
```

## Migration Path 1: SQLite to Supabase

### Prerequisites
1. Completed Supabase setup (see [SUPABASE_SETUP.md](SUPABASE_SETUP.md))
2. Supabase project with tables created
3. `.env` file configured with Supabase credentials

### Step 1: Export Data from SQLite

Create a Python script to export your data:

```python
# export_from_sqlite.py
import sqlite3
import json
from datetime import datetime

def export_sqlite_to_json(db_path='call_analysis.db', output_file='export_data.json'):
    """Export all data from SQLite to JSON"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {}
    
    # Export agents
    cursor.execute("SELECT * FROM agents")
    data['agents'] = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(data['agents'])} agents")
    
    # Export calls
    cursor.execute("SELECT * FROM calls")
    data['calls'] = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(data['calls'])} calls")
    
    # Export keywords
    cursor.execute("SELECT * FROM keywords")
    data['keywords'] = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(data['keywords'])} keywords")
    
    # Export qa_scores
    cursor.execute("SELECT * FROM qa_scores")
    data['qa_scores'] = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(data['qa_scores'])} QA scores")
    
    # Export monthly_summaries
    cursor.execute("SELECT * FROM monthly_summaries")
    data['monthly_summaries'] = [dict(row) for row in cursor.fetchall()]
    print(f"Exported {len(data['monthly_summaries'])} monthly summaries")
    
    conn.close()
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\n✓ Data exported to {output_file}")
    return data

if __name__ == '__main__':
    export_sqlite_to_json()
```

Run the export:
```bash
python export_from_sqlite.py
```

### Step 2: Import Data to Supabase

Create a script to import the data:

```python
# import_to_supabase.py
import json
from database import CallAnalysisDB
import os

def import_json_to_supabase(input_file='export_data.json'):
    """Import JSON data to Supabase"""
    
    # Ensure we're using Supabase
    os.environ['USE_LOCAL_DB'] = 'false'
    
    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Initialize Supabase connection
    db = CallAnalysisDB()
    
    if not db.use_supabase:
        print("Error: Not connected to Supabase. Check your .env configuration.")
        return
    
    print("Connected to Supabase. Starting import...\n")
    
    # Import agents
    print(f"Importing {len(data['agents'])} agents...")
    for agent in data['agents']:
        try:
            # Remove auto-generated fields
            agent_data = {
                'agent_name': agent['agent_name'],
                'department': agent.get('department'),
                'start_date': agent.get('start_date'),
                'is_active': agent.get('is_active', True)
            }
            db.supabase.table('agents').insert(agent_data).execute()
        except Exception as e:
            print(f"  Warning: Could not import agent {agent['agent_name']}: {e}")
    
    # Get agent ID mapping (old ID -> new ID)
    agent_mapping = {}
    result = db.supabase.table('agents').select('agent_id, agent_name').execute()
    for row in result.data:
        # Find original agent
        orig_agent = next((a for a in data['agents'] if a['agent_name'] == row['agent_name']), None)
        if orig_agent:
            agent_mapping[orig_agent['agent_id']] = row['agent_id']
    
    # Import calls
    print(f"Importing {len(data['calls'])} calls...")
    call_mapping = {}
    for call in data['calls']:
        try:
            call_data = {
                'agent_id': agent_mapping.get(call['agent_id']),
                'filename': call['filename'],
                'call_date': call['call_date'],
                'call_type': call.get('call_type'),
                'duration_minutes': call.get('duration_minutes'),
                'transcript': call.get('transcript'),
                'sentiment': call.get('sentiment'),
                'processing_time_seconds': call.get('processing_time_seconds'),
                'file_size_mb': call.get('file_size_mb')
            }
            result = db.supabase.table('calls').insert(call_data).execute()
            call_mapping[call['call_id']] = result.data[0]['call_id']
        except Exception as e:
            print(f"  Warning: Could not import call {call['call_id']}: {e}")
    
    # Import keywords
    print(f"Importing {len(data['keywords'])} keywords...")
    for keyword in data['keywords']:
        try:
            if keyword['call_id'] in call_mapping:
                keyword_data = {
                    'call_id': call_mapping[keyword['call_id']],
                    'keyword_phrase': keyword['keyword_phrase'],
                    'confidence': keyword.get('confidence'),
                    'priority': keyword.get('priority'),
                    'match_type': keyword.get('match_type')
                }
                db.supabase.table('keywords').insert(keyword_data).execute()
        except Exception as e:
            print(f"  Warning: Could not import keyword: {e}")
    
    # Import QA scores
    print(f"Importing {len(data['qa_scores'])} QA scores...")
    for score in data['qa_scores']:
        try:
            if score['call_id'] in call_mapping:
                score_data = {
                    'call_id': call_mapping[score['call_id']],
                    'scoring_method': score['scoring_method'],
                    'category': score['category'],
                    'score': score['score'],
                    'confidence': score.get('confidence'),
                    'explanation': score.get('explanation'),
                    'matched_phrase': score.get('matched_phrase')
                }
                db.supabase.table('qa_scores').insert(score_data).execute()
        except Exception as e:
            print(f"  Warning: Could not import QA score: {e}")
    
    # Import monthly summaries
    print(f"Importing {len(data['monthly_summaries'])} monthly summaries...")
    for summary in data['monthly_summaries']:
        try:
            if summary['agent_id'] in agent_mapping:
                summary_data = {
                    'agent_id': agent_mapping[summary['agent_id']],
                    'year': summary['year'],
                    'month': summary['month'],
                    'total_calls': summary['total_calls'],
                    'avg_rule_score': summary['avg_rule_score'],
                    'avg_nlp_score': summary['avg_nlp_score'],
                    'total_duration_minutes': summary['total_duration_minutes'],
                    'positive_sentiment_count': summary['positive_sentiment_count'],
                    'negative_sentiment_count': summary['negative_sentiment_count'],
                    'neutral_sentiment_count': summary['neutral_sentiment_count']
                }
                db.supabase.table('monthly_summaries').insert(summary_data).execute()
        except Exception as e:
            print(f"  Warning: Could not import monthly summary: {e}")
    
    print("\n✓ Import completed!")

if __name__ == '__main__':
    import_json_to_supabase()
```

Run the import:
```bash
python import_to_supabase.py
```

### Step 3: Verify the Migration

Update your `.env` file to use Supabase:
```env
USE_LOCAL_DB=false
```

Start the application and verify your data:
```bash
streamlit run app.py
```

Check that:
- All agents are visible in the agent selector
- Historical calls are displayed correctly
- Dashboard shows accurate statistics

## Migration Path 2: Supabase to SQLite

If you need to move from Supabase back to SQLite (e.g., for local development):

### Step 1: Export from Supabase

```python
# export_from_supabase.py
import json
from database import CallAnalysisDB
import os

def export_supabase_to_json(output_file='export_data.json'):
    """Export all data from Supabase to JSON"""
    
    # Ensure we're using Supabase
    os.environ['USE_LOCAL_DB'] = 'false'
    
    db = CallAnalysisDB()
    
    if not db.use_supabase:
        print("Error: Not connected to Supabase.")
        return
    
    data = {}
    
    # Export agents
    result = db.supabase.table('agents').select('*').execute()
    data['agents'] = result.data
    print(f"Exported {len(data['agents'])} agents")
    
    # Export calls
    result = db.supabase.table('calls').select('*').execute()
    data['calls'] = result.data
    print(f"Exported {len(data['calls'])} calls")
    
    # Export keywords
    result = db.supabase.table('keywords').select('*').execute()
    data['keywords'] = result.data
    print(f"Exported {len(data['keywords'])} keywords")
    
    # Export qa_scores
    result = db.supabase.table('qa_scores').select('*').execute()
    data['qa_scores'] = result.data
    print(f"Exported {len(data['qa_scores'])} QA scores")
    
    # Export monthly_summaries
    result = db.supabase.table('monthly_summaries').select('*').execute()
    data['monthly_summaries'] = result.data
    print(f"Exported {len(data['monthly_summaries'])} monthly summaries")
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"\n✓ Data exported to {output_file}")

if __name__ == '__main__':
    export_supabase_to_json()
```

### Step 2: Import to SQLite

Use similar import logic as shown above, but targeting SQLite instead.

## Switching Between Databases

You can easily switch between databases by changing the `.env` file:

**Use SQLite:**
```env
USE_LOCAL_DB=true
```

**Use Supabase:**
```env
USE_LOCAL_DB=false
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_key_here
```

Then restart your application.

## Troubleshooting

### Issue: Data not appearing after migration

**Solution**: Check that:
1. All required tables exist in the target database
2. Foreign key relationships are maintained
3. Date formats are correct (YYYY-MM-DD)

### Issue: Duplicate key errors during import

**Solution**: 
- The target database may already have some data
- Clear the target database tables before importing
- Or modify the import script to handle duplicates

### Issue: Performance is slow after migration

**Solution**:
- For Supabase: Check that indexes are created (they should be from the schema)
- For SQLite: Run `VACUUM` to optimize the database

## Best Practices

1. **Always backup** before migrating
2. **Test with a subset** of data first
3. **Verify data integrity** after migration
4. **Keep both databases** during transition period
5. **Document your migration** for future reference

## Need Help?

If you encounter issues during migration:
1. Check the application logs for detailed error messages
2. Verify your database connections
3. Ensure all tables have the correct schema
4. Review the export JSON file for data integrity
