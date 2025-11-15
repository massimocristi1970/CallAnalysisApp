# Quick Start Guide - Using Supabase

This is a condensed guide to get you up and running with Supabase in minutes.

## 5-Minute Setup

### 1. Create Supabase Project (2 minutes)
1. Go to https://supabase.com and sign up
2. Click "New Project"
3. Name: `call-analysis-app`, choose password & region
4. Wait for project creation

### 2. Create Database Tables (2 minutes)
1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy-paste this SQL:

```sql
-- Quick setup schema
CREATE TABLE agents (
    agent_id SERIAL PRIMARY KEY,
    agent_name TEXT UNIQUE NOT NULL,
    department TEXT,
    start_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calls (
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

CREATE TABLE keywords (
    keyword_id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(call_id) ON DELETE CASCADE,
    keyword_phrase TEXT NOT NULL,
    confidence REAL,
    priority TEXT,
    match_type TEXT
);

CREATE TABLE qa_scores (
    score_id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(call_id) ON DELETE CASCADE,
    scoring_method TEXT,
    category TEXT NOT NULL,
    score INTEGER NOT NULL,
    confidence REAL,
    explanation TEXT,
    matched_phrase TEXT
);

CREATE TABLE monthly_summaries (
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

-- Indexes for performance
CREATE INDEX idx_calls_agent_date ON calls(agent_id, call_date);
CREATE INDEX idx_qa_scores_call ON qa_scores(call_id);
CREATE INDEX idx_keywords_call ON keywords(call_id);
CREATE INDEX idx_monthly_summaries_agent ON monthly_summaries(agent_id, year, month);
```

4. Click **Run** (should see "Success" messages)

### 3. Configure Application (1 minute)
1. In Supabase, go to **Settings** > **API**
2. Copy your **Project URL** and **anon public key**
3. In your app folder, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and paste your credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=eyJ...your_key_here
   USE_LOCAL_DB=false
   ```

### 4. Run the App
```bash
pip install supabase python-dotenv
streamlit run app.py
```

You should see:
```
✓ Connected to Supabase database
✓ Supabase tables verified
```

## That's It!

You're now running with Supabase. Your data is stored in the cloud and accessible from anywhere.

## What's Next?

- Add your first agent and process a call
- Check the dashboard: `streamlit run dashboard.py --server.port 8503`
- Read [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for advanced features
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) to migrate existing data

## Common Issues

**"Could not verify Supabase tables"**
→ Re-run the SQL schema in Supabase SQL Editor

**"Connection failed"**
→ Check your SUPABASE_URL and SUPABASE_KEY in .env

**Falls back to SQLite**
→ Make sure `USE_LOCAL_DB=false` in .env

## Need More Help?

See the full guide: [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
