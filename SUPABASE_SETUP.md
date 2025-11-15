# Supabase Setup Guide for Call Analysis App

This guide will help you migrate from the local SQLite database to Supabase (PostgreSQL cloud database).

## Prerequisites

1. A Supabase account (free tier available at https://supabase.com)
2. Python 3.8 or higher
3. The Call Analysis App repository

## Step 1: Create a Supabase Project

1. Go to https://app.supabase.com
2. Click "New Project"
3. Enter project details:
   - Name: `call-analysis-app` (or your preferred name)
   - Database Password: Choose a strong password (save this!)
   - Region: Choose the closest to your location
4. Wait for the project to be created (2-3 minutes)

## Step 2: Get Your Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** > **API**
2. Copy the following values:
   - **Project URL**: `https://your-project.supabase.co`
   - **anon/public key**: A long string starting with `eyJ...`

## Step 3: Create Database Schema

1. In your Supabase project, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the following SQL schema:

```sql
-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    agent_id SERIAL PRIMARY KEY,
    agent_name TEXT UNIQUE NOT NULL,
    department TEXT,
    start_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Calls table
CREATE TABLE IF NOT EXISTS calls (
    call_id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(agent_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    call_date DATE NOT NULL,
    call_type TEXT,
    duration_minutes REAL,
    transcript TEXT,
    sentiment TEXT,
    processing_time_seconds REAL,
    file_size_mb REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords table
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(call_id) ON DELETE CASCADE,
    keyword_phrase TEXT NOT NULL,
    confidence REAL,
    priority TEXT,
    match_type TEXT
);

-- QA Scores table
CREATE TABLE IF NOT EXISTS qa_scores (
    score_id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(call_id) ON DELETE CASCADE,
    scoring_method TEXT, -- 'rule_based' or 'nlp_enhanced'
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    confidence REAL,
    explanation TEXT,
    matched_phrase TEXT
);

-- Monthly summaries table
CREATE TABLE IF NOT EXISTS monthly_summaries (
    summary_id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(agent_id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_calls INTEGER DEFAULT 0,
    avg_rule_score REAL DEFAULT 0,
    avg_nlp_score REAL DEFAULT 0,
    total_duration_minutes REAL DEFAULT 0,
    positive_sentiment_count INTEGER DEFAULT 0,
    negative_sentiment_count INTEGER DEFAULT 0,
    neutral_sentiment_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, year, month)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calls_agent_date ON calls(agent_id, call_date);
CREATE INDEX IF NOT EXISTS idx_qa_scores_call ON qa_scores(call_id);
CREATE INDEX IF NOT EXISTS idx_keywords_call ON keywords(call_id);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_agent ON monthly_summaries(agent_id, year, month);

-- Create indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_calls_agent_id ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_keywords_call_id ON keywords(call_id);
CREATE INDEX IF NOT EXISTS idx_qa_scores_call_id ON qa_scores(call_id);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_agent_id ON monthly_summaries(agent_id);
```

4. Click **Run** to execute the SQL
5. Verify that all tables were created successfully (you should see "Success" messages)

## Step 4: Configure Row Level Security (RLS) - Optional but Recommended

For production use, enable Row Level Security to protect your data:

```sql
-- Enable RLS on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_summaries ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations for authenticated users
-- Adjust these based on your security requirements

-- Agents policies
CREATE POLICY "Enable all for authenticated users" ON agents
    FOR ALL USING (auth.role() = 'authenticated');

-- Calls policies
CREATE POLICY "Enable all for authenticated users" ON calls
    FOR ALL USING (auth.role() = 'authenticated');

-- Keywords policies
CREATE POLICY "Enable all for authenticated users" ON keywords
    FOR ALL USING (auth.role() = 'authenticated');

-- QA Scores policies
CREATE POLICY "Enable all for authenticated users" ON qa_scores
    FOR ALL USING (auth.role() = 'authenticated');

-- Monthly Summaries policies
CREATE POLICY "Enable all for authenticated users" ON monthly_summaries
    FOR ALL USING (auth.role() = 'authenticated');

-- If you want to allow access with the anon key (for development):
-- Replace 'authenticated' with 'anon' in the policies above
-- For production, use authentication with service role key
```

**Note**: If you're using the anon key for development, you may want to use simpler policies or disable RLS during development. For production, implement proper authentication.

## Step 5: Configure Your Application

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_here
   USE_LOCAL_DB=false
   ```

3. Install the required dependencies:
   ```bash
   pip install supabase python-dotenv
   ```
   
   Or install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 6: Test the Connection

Run the application to test the Supabase connection:

```bash
streamlit run app.py
```

You should see a message indicating successful connection to Supabase:
```
✓ Connected to Supabase database
✓ Supabase tables verified
```

## Step 7: Migrate Existing Data (Optional)

If you have existing data in your SQLite database that you want to migrate to Supabase:

1. Set `USE_LOCAL_DB=true` in your `.env` file temporarily
2. Export your data from SQLite
3. Create a migration script to import into Supabase
4. Set `USE_LOCAL_DB=false` to use Supabase

Example migration script structure:
```python
from database import CallAnalysisDB
import sqlite3

# Connect to both databases
sqlite_db = CallAnalysisDB(db_path="call_analysis.db")
# Configure for Supabase
supabase_db = CallAnalysisDB()  # Will use Supabase if configured

# Migrate agents
# ... your migration code here
```

## Troubleshooting

### Connection Issues

If you see connection errors:
1. Verify your `SUPABASE_URL` and `SUPABASE_KEY` are correct
2. Check that your Supabase project is active
3. Ensure you have internet connectivity
4. Check Supabase dashboard for any service issues

### Table Not Found Errors

If you see "table does not exist" errors:
1. Go back to **SQL Editor** in Supabase
2. Re-run the schema creation SQL
3. Check the **Table Editor** to verify tables exist

### Permission Errors

If you see permission/policy errors:
1. Check your RLS policies in Supabase
2. For development, you can disable RLS temporarily:
   ```sql
   ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
   ```
3. For production, configure proper authentication

### Falling Back to SQLite

If you need to use the local SQLite database instead:
1. Set `USE_LOCAL_DB=true` in your `.env` file
2. Restart the application

## Best Practices

1. **Security**:
   - Never commit your `.env` file to version control
   - Use the anon key for client-side operations only
   - For server-side operations, consider using the service role key
   - Enable RLS for production deployments

2. **Performance**:
   - The schema includes indexes for common queries
   - Monitor query performance in Supabase dashboard
   - Consider adding additional indexes based on your query patterns

3. **Backups**:
   - Supabase provides automatic backups on paid plans
   - For free tier, export your data regularly
   - Keep a local backup of important data

4. **Development vs Production**:
   - Use separate Supabase projects for development and production
   - Test thoroughly in development before deploying to production

## Support

- Supabase Documentation: https://supabase.com/docs
- Supabase Community: https://github.com/supabase/supabase/discussions
- Call Analysis App Issues: https://github.com/yourusername/CallAnalysisApp/issues

## Next Steps

After successful setup:
1. Test creating agents and uploading calls
2. Verify the dashboard displays data correctly
3. Configure backups and monitoring
4. Set up proper authentication for production use
