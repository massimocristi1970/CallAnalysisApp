# database.py
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Supabase (optional dependency)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase library not installed. Using SQLite only.")

class CallAnalysisDB:
    """Database handler for call analysis data - supports both SQLite and Supabase"""
    
    def __init__(self, db_path: str = "call_analysis.db"):
        self.db_path = db_path
        
        # Check if we should use Supabase
        use_local = os.getenv("USE_LOCAL_DB", "false").lower() == "true"
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        # Determine which backend to use
        if not use_local and SUPABASE_AVAILABLE and supabase_url and supabase_key:
            self.use_supabase = True
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print("✓ Connected to Supabase database")
        else:
            self.use_supabase = False
            self.supabase = None
            if not use_local and (not supabase_url or not supabase_key):
                print("⚠ Supabase credentials not found. Using local SQLite database.")
            else:
                print("✓ Using local SQLite database")
        
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        if self.use_supabase:
            self._init_supabase_database()
        else:
            self._init_sqlite_database()
    
    def _init_supabase_database(self):
        """Initialize Supabase database schema"""
        # Supabase tables should be created via the Supabase dashboard or SQL editor
        # This method just verifies the connection
        try:
            # Test connection by querying agents table
            result = self.supabase.table('agents').select("agent_id").limit(1).execute()
            print("✓ Supabase tables verified")
        except Exception as e:
            print(f"⚠ Warning: Could not verify Supabase tables. Please ensure tables are created.")
            print(f"   Error: {str(e)}")
            print("\n   To create tables in Supabase, run the SQL schema provided in SUPABASE_SETUP.md")
    
    def _init_sqlite_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT UNIQUE NOT NULL,
                    department TEXT,
                    start_date DATE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    filename TEXT NOT NULL,
                    call_date DATE NOT NULL,
                    call_type TEXT,
                    duration_minutes REAL,
                    transcript TEXT,
                    sentiment TEXT,
                    processing_time_seconds REAL,
                    file_size_mb REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            """)
            
            # Keywords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id INTEGER,
                    keyword_phrase TEXT NOT NULL,
                    confidence REAL,
                    priority TEXT,
                    match_type TEXT,
                    FOREIGN KEY (call_id) REFERENCES calls (call_id)
                )
            """)
            
            # QA Scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qa_scores (
                    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id INTEGER,
                    scoring_method TEXT, -- 'rule_based' or 'nlp_enhanced'
                    category TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    confidence REAL,
                    explanation TEXT,
                    matched_phrase TEXT,
                    FOREIGN KEY (call_id) REFERENCES calls (call_id)
                )
            """)
            
            # Monthly summaries table for faster dashboard queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_summaries (
                    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    year INTEGER,
                    month INTEGER,
                    total_calls INTEGER DEFAULT 0,
                    avg_rule_score REAL DEFAULT 0,
                    avg_nlp_score REAL DEFAULT 0,
                    total_duration_minutes REAL DEFAULT 0,
                    positive_sentiment_count INTEGER DEFAULT 0,
                    negative_sentiment_count INTEGER DEFAULT 0,
                    neutral_sentiment_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id),
                    UNIQUE(agent_id, year, month)
                )
            """)
            
            # Indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_agent_date ON calls (agent_id, call_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_scores_call ON qa_scores (call_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_call ON keywords (call_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_summaries_agent ON monthly_summaries (agent_id, year, month)")
            
            conn.commit()
    
    def add_agent(self, agent_name: str, department: str = None) -> int:
        """Add a new agent"""
        if self.use_supabase:
            return self._add_agent_supabase(agent_name, department)
        else:
            return self._add_agent_sqlite(agent_name, department)
    
    def _add_agent_supabase(self, agent_name: str, department: str = None) -> int:
        """Add agent to Supabase"""
        try:
            # Check if agent exists
            result = self.supabase.table('agents').select("agent_id").eq('agent_name', agent_name).execute()
            
            if result.data:
                return result.data[0]['agent_id']
            
            # Insert new agent
            data = {
                'agent_name': agent_name,
                'department': department,
                'start_date': str(date.today()),
                'is_active': True
            }
            result = self.supabase.table('agents').insert(data).execute()
            return result.data[0]['agent_id']
        except Exception as e:
            print(f"Error adding agent to Supabase: {e}")
            raise
    
    def _add_agent_sqlite(self, agent_name: str, department: str = None) -> int:
        """Add agent to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO agents (agent_name, department, start_date)
                VALUES (?, ?, ?)
            """, (agent_name, department, date.today()))
            
            # Get agent_id
            cursor.execute("SELECT agent_id FROM agents WHERE agent_name = ?", (agent_name,))
            return cursor.fetchone()[0]
    
    def save_call_analysis(self, agent_name: str, call_data: Dict[str, Any]) -> int:
        """Save complete call analysis to database"""
        if self.use_supabase:
            return self._save_call_analysis_supabase(agent_name, call_data)
        else:
            return self._save_call_analysis_sqlite(agent_name, call_data)
    
    def _save_call_analysis_supabase(self, agent_name: str, call_data: Dict[str, Any]) -> int:
        """Save call analysis to Supabase"""
        try:
            # Get or create agent
            agent_id = self.add_agent(agent_name)
            
            # Extract metadata
            metadata = call_data.get('metadata', {})
            
            # Insert call record
            call_record = {
                'agent_id': agent_id,
                'filename': call_data['filename'],
                'call_date': str(call_data.get('call_date', date.today())),
                'call_type': call_data.get('call_type', 'Unknown'),
                'duration_minutes': metadata.get('duration_minutes', 0),
                'transcript': call_data['transcript'],
                'sentiment': call_data['sentiment'],
                'processing_time_seconds': call_data.get('processing_time', 0),
                'file_size_mb': metadata.get('file_size_mb', 0)
            }
            
            result = self.supabase.table('calls').insert(call_record).execute()
            call_id = result.data[0]['call_id']
            
            # Save keywords
            if call_data.get('keywords_enhanced'):
                keywords_data = []
                for keyword in call_data['keywords_enhanced']:
                    keywords_data.append({
                        'call_id': call_id,
                        'keyword_phrase': keyword.get('phrase', ''),
                        'confidence': keyword.get('confidence', 0),
                        'priority': keyword.get('priority', 'medium'),
                        'match_type': keyword.get('match_type', 'exact')
                    })
                if keywords_data:
                    self.supabase.table('keywords').insert(keywords_data).execute()
            
            # Save QA scores - Rule-based
            qa_scores_data = []
            for category, result_data in call_data.get('qa_results', {}).items():
                qa_scores_data.append({
                    'call_id': call_id,
                    'scoring_method': 'rule_based',
                    'category': category,
                    'score': result_data['score'],
                    'confidence': result_data.get('confidence', 0),
                    'explanation': result_data['explanation'],
                    'matched_phrase': result_data.get('matched_phrase', '')
                })
            
            # Save QA scores - NLP Enhanced
            for category, result_data in call_data.get('qa_results_nlp', {}).items():
                qa_scores_data.append({
                    'call_id': call_id,
                    'scoring_method': 'nlp_enhanced',
                    'category': category,
                    'score': result_data['score'],
                    'confidence': result_data.get('confidence', 0),
                    'explanation': result_data['explanation'],
                    'matched_phrase': result_data.get('matched_phrase', '')
                })
            
            if qa_scores_data:
                self.supabase.table('qa_scores').insert(qa_scores_data).execute()
            
            # Update monthly summary
            self.update_monthly_summary(agent_id, call_data.get('call_date', date.today()))
            
            return call_id
            
        except Exception as e:
            print(f"Error saving call analysis to Supabase: {e}")
            raise
    
    def _save_call_analysis_sqlite(self, agent_name: str, call_data: Dict[str, Any]) -> int:
        """Save call analysis to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create agent
            agent_id = self.add_agent(agent_name)
            
            # Extract metadata
            metadata = call_data.get('metadata', {})
            
            # Insert call record
            cursor.execute("""
                INSERT INTO calls (
                    agent_id, filename, call_date, call_type, duration_minutes,
                    transcript, sentiment, processing_time_seconds, file_size_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                call_data['filename'],
                call_data.get('call_date', date.today()),
                call_data.get('call_type', 'Unknown'),
                metadata.get('duration_minutes', 0),
                call_data['transcript'],
                call_data['sentiment'],
                call_data.get('processing_time', 0),
                metadata.get('file_size_mb', 0)
            ))
            
            call_id = cursor.lastrowid
            
            # Save keywords
            for keyword in call_data.get('keywords_enhanced', []):
                cursor.execute("""
                    INSERT INTO keywords (call_id, keyword_phrase, confidence, priority, match_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    call_id,
                    keyword.get('phrase', ''),
                    keyword.get('confidence', 0),
                    keyword.get('priority', 'medium'),
                    keyword.get('match_type', 'exact')
                ))
            
            # Save QA scores - Rule-based
            for category, result in call_data.get('qa_results', {}).items():
                cursor.execute("""
                    INSERT INTO qa_scores (call_id, scoring_method, category, score, confidence, explanation, matched_phrase)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_id, 'rule_based', category, result['score'],
                    result.get('confidence', 0), result['explanation'],
                    result.get('matched_phrase', '')
                ))
            
            # Save QA scores - NLP Enhanced
            for category, result in call_data.get('qa_results_nlp', {}).items():
                cursor.execute("""
                    INSERT INTO qa_scores (call_id, scoring_method, category, score, confidence, explanation, matched_phrase)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_id, 'nlp_enhanced', category, result['score'],
                    result.get('confidence', 0), result['explanation'],
                    result.get('matched_phrase', '')
                ))
            
            conn.commit()
            
            # Update monthly summary
            self.update_monthly_summary(agent_id, call_data.get('call_date', date.today()))
            
            return call_id
    
    def update_monthly_summary(self, agent_id: int, call_date: date):
        """Update monthly summary for an agent"""
        if self.use_supabase:
            self._update_monthly_summary_supabase(agent_id, call_date)
        else:
            self._update_monthly_summary_sqlite(agent_id, call_date)
    
    def _update_monthly_summary_supabase(self, agent_id: int, call_date: date):
        """Update monthly summary in Supabase"""
        year, month = call_date.year, call_date.month
        
        try:
            # Get all calls for this agent and month
            calls_result = self.supabase.table('calls').select(
                "call_id, duration_minutes, sentiment"
            ).eq('agent_id', agent_id).gte(
                'call_date', f"{year}-{month:02d}-01"
            ).lt(
                'call_date', f"{year}-{month+1 if month < 12 else 1:02d}-01" if month < 12 else f"{year+1}-01-01"
            ).execute()
            
            calls = calls_result.data
            total_calls = len(calls)
            
            if total_calls == 0:
                return
            
            # Calculate stats
            total_duration = sum(c.get('duration_minutes', 0) for c in calls)
            positive_count = sum(1 for c in calls if c.get('sentiment') == 'Positive')
            negative_count = sum(1 for c in calls if c.get('sentiment') == 'Negative')
            neutral_count = sum(1 for c in calls if c.get('sentiment') == 'Neutral')
            
            # Get QA scores for these calls
            call_ids = [c['call_id'] for c in calls]
            qa_result = self.supabase.table('qa_scores').select(
                "scoring_method, score"
            ).in_('call_id', call_ids).execute()
            
            qa_scores = qa_result.data
            rule_scores = [s['score'] for s in qa_scores if s['scoring_method'] == 'rule_based']
            nlp_scores = [s['score'] for s in qa_scores if s['scoring_method'] == 'nlp_enhanced']
            
            avg_rule_score = sum(rule_scores) / len(rule_scores) if rule_scores else 0
            avg_nlp_score = sum(nlp_scores) / len(nlp_scores) if nlp_scores else 0
            
            # Check if summary exists
            existing = self.supabase.table('monthly_summaries').select("summary_id").eq(
                'agent_id', agent_id
            ).eq('year', year).eq('month', month).execute()
            
            summary_data = {
                'agent_id': agent_id,
                'year': year,
                'month': month,
                'total_calls': total_calls,
                'avg_rule_score': avg_rule_score,
                'avg_nlp_score': avg_nlp_score,
                'total_duration_minutes': total_duration,
                'positive_sentiment_count': positive_count,
                'negative_sentiment_count': negative_count,
                'neutral_sentiment_count': neutral_count
            }
            
            if existing.data:
                # Update existing
                self.supabase.table('monthly_summaries').update(summary_data).eq(
                    'summary_id', existing.data[0]['summary_id']
                ).execute()
            else:
                # Insert new
                self.supabase.table('monthly_summaries').insert(summary_data).execute()
                
        except Exception as e:
            print(f"Error updating monthly summary in Supabase: {e}")
    
    def _update_monthly_summary_sqlite(self, agent_id: int, call_date: date):
        """Update monthly summary in SQLite"""
        year, month = call_date.year, call_date.month
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate monthly stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN qs.score END) as avg_nlp_score,
                    SUM(c.duration_minutes) as total_duration,
                    SUM(CASE WHEN c.sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN c.sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN c.sentiment = 'Neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM calls c
                LEFT JOIN qa_scores qs ON c.call_id = qs.call_id
                WHERE c.agent_id = ? 
                AND strftime('%Y', c.call_date) = ? 
                AND strftime('%m', c.call_date) = ?
            """, (agent_id, str(year), f"{month:02d}"))
            
            stats = cursor.fetchone()
            
            # Insert or update monthly summary
            cursor.execute("""
                INSERT OR REPLACE INTO monthly_summaries (
                    agent_id, year, month, total_calls, avg_rule_score, avg_nlp_score,
                    total_duration_minutes, positive_sentiment_count, 
                    negative_sentiment_count, neutral_sentiment_count, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (agent_id, year, month, *stats))
            
            conn.commit()
    
    def get_agent_scores_by_month(self, agent_name: str = None, year: int = None) -> pd.DataFrame:
        """Get agent scores by month"""
        if self.use_supabase:
            return self._get_agent_scores_by_month_supabase(agent_name, year)
        else:
            return self._get_agent_scores_by_month_sqlite(agent_name, year)
    
    def _get_agent_scores_by_month_supabase(self, agent_name: str = None, year: int = None) -> pd.DataFrame:
        """Get agent scores by month from Supabase"""
        try:
            # Build query
            query = self.supabase.table('monthly_summaries').select(
                "*, agents!inner(agent_name, is_active)"
            ).eq('agents.is_active', True)
            
            if agent_name:
                query = query.eq('agents.agent_name', agent_name)
            if year:
                query = query.eq('year', year)
            
            result = query.order('year', desc=True).order('month', desc=True).execute()
            
            # Convert to DataFrame
            if not result.data:
                return pd.DataFrame()
            
            # Flatten the nested structure
            data = []
            for row in result.data:
                data.append({
                    'agent_name': row['agents']['agent_name'],
                    'year': row['year'],
                    'month': row['month'],
                    'total_calls': row['total_calls'],
                    'avg_rule_score': round(row['avg_rule_score'], 2),
                    'avg_nlp_score': round(row['avg_nlp_score'], 2),
                    'total_duration_minutes': round(row['total_duration_minutes'], 1),
                    'positive_sentiment_count': row['positive_sentiment_count'],
                    'negative_sentiment_count': row['negative_sentiment_count'],
                    'neutral_sentiment_count': row['neutral_sentiment_count']
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error getting agent scores from Supabase: {e}")
            return pd.DataFrame()
    
    def _get_agent_scores_by_month_sqlite(self, agent_name: str = None, year: int = None) -> pd.DataFrame:
        """Get agent scores by month from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    a.agent_name,
                    ms.year,
                    ms.month,
                    ms.total_calls,
                    ROUND(ms.avg_rule_score, 2) as avg_rule_score,
                    ROUND(ms.avg_nlp_score, 2) as avg_nlp_score,
                    ROUND(ms.total_duration_minutes, 1) as total_duration_minutes,
                    ms.positive_sentiment_count,
                    ms.negative_sentiment_count,
                    ms.neutral_sentiment_count
                FROM monthly_summaries ms
                JOIN agents a ON ms.agent_id = a.agent_id
                WHERE a.is_active = 1
            """
            
            params = []
            if agent_name:
                query += " AND a.agent_name = ?"
                params.append(agent_name)
            if year:
                query += " AND ms.year = ?"
                params.append(year)
            
            query += " ORDER BY a.agent_name, ms.year DESC, ms.month DESC"
            
            return pd.read_sql_query(query, conn, params=params)
    
    def get_dashboard_data(self, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        if not start_date:
            start_date = date.today().replace(month=1, day=1)  # Start of current year
        if not end_date:
            end_date = date.today()
        
        if self.use_supabase:
            return self._get_dashboard_data_supabase(start_date, end_date)
        else:
            return self._get_dashboard_data_sqlite(start_date, end_date)
    
    def _get_dashboard_data_supabase(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get dashboard data from Supabase"""
        try:
            # Get all calls in date range
            calls_result = self.supabase.table('calls').select(
                "call_id, agent_id, call_date, duration_minutes, sentiment"
            ).gte('call_date', str(start_date)).lte('call_date', str(end_date)).execute()
            
            calls = calls_result.data
            
            if not calls:
                return {
                    'overview': {},
                    'agent_performance': pd.DataFrame(),
                    'monthly_trends': pd.DataFrame(),
                    'category_breakdown': pd.DataFrame()
                }
            
            call_ids = [c['call_id'] for c in calls]
            
            # Get QA scores for these calls
            qa_result = self.supabase.table('qa_scores').select(
                "call_id, scoring_method, category, score"
            ).in_('call_id', call_ids).execute()
            
            qa_scores = qa_result.data
            
            # Calculate overview metrics
            total_agents = len(set(c['agent_id'] for c in calls))
            total_calls = len(calls)
            rule_scores = [s['score'] for s in qa_scores if s['scoring_method'] == 'rule_based']
            nlp_scores = [s['score'] for s in qa_scores if s['scoring_method'] == 'nlp_enhanced']
            
            overview = {
                'total_agents': total_agents,
                'total_calls': total_calls,
                'avg_rule_score': sum(rule_scores) / len(rule_scores) if rule_scores else 0,
                'avg_nlp_score': sum(nlp_scores) / len(nlp_scores) if nlp_scores else 0,
                'total_duration_minutes': sum(c.get('duration_minutes', 0) for c in calls)
            }
            
            # Get agent performance
            agents_result = self.supabase.table('agents').select(
                "agent_id, agent_name, department"
            ).eq('is_active', True).execute()
            
            agent_performance_data = []
            for agent in agents_result.data:
                agent_calls = [c for c in calls if c['agent_id'] == agent['agent_id']]
                if not agent_calls:
                    continue
                
                agent_call_ids = [c['call_id'] for c in agent_calls]
                agent_qa = [s for s in qa_scores if s['call_id'] in agent_call_ids]
                
                agent_rule_scores = [s['score'] for s in agent_qa if s['scoring_method'] == 'rule_based']
                agent_nlp_scores = [s['score'] for s in agent_qa if s['scoring_method'] == 'nlp_enhanced']
                
                agent_performance_data.append({
                    'agent_name': agent['agent_name'],
                    'department': agent.get('department'),
                    'total_calls': len(agent_calls),
                    'avg_rule_score': sum(agent_rule_scores) / len(agent_rule_scores) if agent_rule_scores else 0,
                    'avg_nlp_score': sum(agent_nlp_scores) / len(agent_nlp_scores) if agent_nlp_scores else 0,
                    'total_duration_minutes': sum(c.get('duration_minutes', 0) for c in agent_calls),
                    'positive_calls': sum(1 for c in agent_calls if c.get('sentiment') == 'Positive'),
                    'negative_calls': sum(1 for c in agent_calls if c.get('sentiment') == 'Negative')
                })
            
            agent_performance = pd.DataFrame(agent_performance_data).sort_values('avg_rule_score', ascending=False) if agent_performance_data else pd.DataFrame()
            
            # Monthly trends
            monthly_data = {}
            for call in calls:
                month_key = call['call_date'][:7]  # YYYY-MM
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'calls': [], 'qa_scores': []}
                monthly_data[month_key]['calls'].append(call['call_id'])
            
            monthly_trends_data = []
            for month_key in sorted(monthly_data.keys()):
                month_call_ids = monthly_data[month_key]['calls']
                month_qa = [s for s in qa_scores if s['call_id'] in month_call_ids]
                month_rule_scores = [s['score'] for s in month_qa if s['scoring_method'] == 'rule_based']
                month_nlp_scores = [s['score'] for s in month_qa if s['scoring_method'] == 'nlp_enhanced']
                
                monthly_trends_data.append({
                    'month': month_key,
                    'total_calls': len(month_call_ids),
                    'avg_rule_score': sum(month_rule_scores) / len(month_rule_scores) if month_rule_scores else 0,
                    'avg_nlp_score': sum(month_nlp_scores) / len(month_nlp_scores) if month_nlp_scores else 0
                })
            
            monthly_trends = pd.DataFrame(monthly_trends_data) if monthly_trends_data else pd.DataFrame()
            
            # Category breakdown
            category_data = {}
            for score in qa_scores:
                key = (score['category'], score['scoring_method'])
                if key not in category_data:
                    category_data[key] = {'scores': [], 'count': 0}
                category_data[key]['scores'].append(score['score'])
                category_data[key]['count'] += 1
            
            category_breakdown_data = []
            for (category, method), data in category_data.items():
                category_breakdown_data.append({
                    'category': category,
                    'scoring_method': method,
                    'avg_score': sum(data['scores']) / len(data['scores']),
                    'total_evaluations': data['count']
                })
            
            category_breakdown = pd.DataFrame(category_breakdown_data) if category_breakdown_data else pd.DataFrame()
            
            return {
                'overview': overview,
                'agent_performance': agent_performance,
                'monthly_trends': monthly_trends,
                'category_breakdown': category_breakdown
            }
            
        except Exception as e:
            print(f"Error getting dashboard data from Supabase: {e}")
            return {
                'overview': {},
                'agent_performance': pd.DataFrame(),
                'monthly_trends': pd.DataFrame(),
                'category_breakdown': pd.DataFrame()
            }
    
    def _get_dashboard_data_sqlite(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get dashboard data from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            # Overall metrics
            overview_query = """
                SELECT 
                    COUNT(DISTINCT c.agent_id) as total_agents,
                    COUNT(c.call_id) as total_calls,
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN qs.score END) as avg_nlp_score,
                    SUM(c.duration_minutes) as total_duration_minutes
                FROM calls c
                LEFT JOIN qa_scores qs ON c.call_id = qs.call_id
                WHERE c.call_date BETWEEN ? AND ?
            """
            overview = pd.read_sql_query(overview_query, conn, params=[start_date, end_date])
            
            # Agent performance
            agent_performance_query = """
                SELECT 
                    a.agent_name,
                    a.department,
                    COUNT(c.call_id) as total_calls,
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN qs.score END) as avg_nlp_score,
                    SUM(c.duration_minutes) as total_duration_minutes,
                    SUM(CASE WHEN c.sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_calls,
                    SUM(CASE WHEN c.sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_calls
                FROM agents a
                LEFT JOIN calls c ON a.agent_id = c.agent_id
                LEFT JOIN qa_scores qs ON c.call_id = qs.call_id
                WHERE a.is_active = 1 AND c.call_date BETWEEN ? AND ?
                GROUP BY a.agent_id
                ORDER BY avg_rule_score DESC
            """
            agent_performance = pd.read_sql_query(agent_performance_query, conn, params=[start_date, end_date])
            
            # Monthly trends
            monthly_trends_query = """
                SELECT 
                    strftime('%Y-%m', c.call_date) as month,
                    COUNT(c.call_id) as total_calls,
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN qs.score END) as avg_nlp_score
                FROM calls c
                LEFT JOIN qa_scores qs ON c.call_id = qs.call_id
                WHERE c.call_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', c.call_date)
                ORDER BY month
            """
            monthly_trends = pd.read_sql_query(monthly_trends_query, conn, params=[start_date, end_date])
            
            # Category breakdown
            category_breakdown_query = """
                SELECT 
                    qs.category,
                    qs.scoring_method,
                    AVG(qs.score) as avg_score,
                    COUNT(*) as total_evaluations
                FROM qa_scores qs
                JOIN calls c ON qs.call_id = c.call_id
                WHERE c.call_date BETWEEN ? AND ?
                GROUP BY qs.category, qs.scoring_method
                ORDER BY qs.category, qs.scoring_method
            """
            category_breakdown = pd.read_sql_query(category_breakdown_query, conn, params=[start_date, end_date])
            
            return {
                'overview': overview.to_dict('records')[0] if not overview.empty else {},
                'agent_performance': agent_performance,
                'monthly_trends': monthly_trends,
                'category_breakdown': category_breakdown
            }
    
    def get_all_agents(self) -> List[str]:
        """Get list of all active agents"""
        if self.use_supabase:
            return self._get_all_agents_supabase()
        else:
            return self._get_all_agents_sqlite()
    
    def _get_all_agents_supabase(self) -> List[str]:
        """Get all agents from Supabase"""
        try:
            result = self.supabase.table('agents').select(
                "agent_name"
            ).eq('is_active', True).order('agent_name').execute()
            return [row['agent_name'] for row in result.data]
        except Exception as e:
            print(f"Error getting agents from Supabase: {e}")
            return []
    
    def _get_all_agents_sqlite(self) -> List[str]:
        """Get all agents from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent_name FROM agents WHERE is_active = 1 ORDER BY agent_name")
            return [row[0] for row in cursor.fetchall()]
    
    def delete_call(self, call_id: int):
        """Delete a call and all related data"""
        if self.use_supabase:
            self._delete_call_supabase(call_id)
        else:
            self._delete_call_sqlite(call_id)
    
    def _delete_call_supabase(self, call_id: int):
        """Delete call from Supabase"""
        try:
            # Get agent and date for summary update
            result = self.supabase.table('calls').select(
                "agent_id, call_date"
            ).eq('call_id', call_id).execute()
            
            if result.data:
                agent_id = result.data[0]['agent_id']
                call_date = datetime.strptime(result.data[0]['call_date'], '%Y-%m-%d').date()
                
                # Delete related records (Supabase should handle cascading deletes if configured)
                self.supabase.table('keywords').delete().eq('call_id', call_id).execute()
                self.supabase.table('qa_scores').delete().eq('call_id', call_id).execute()
                self.supabase.table('calls').delete().eq('call_id', call_id).execute()
                
                # Update monthly summary
                self.update_monthly_summary(agent_id, call_date)
                
        except Exception as e:
            print(f"Error deleting call from Supabase: {e}")
    
    def _delete_call_sqlite(self, call_id: int):
        """Delete call from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get agent and date for summary update
            cursor.execute("SELECT agent_id, call_date FROM calls WHERE call_id = ?", (call_id,))
            result = cursor.fetchone()
            if result:
                agent_id, call_date = result
                
                # Delete related records
                cursor.execute("DELETE FROM keywords WHERE call_id = ?", (call_id,))
                cursor.execute("DELETE FROM qa_scores WHERE call_id = ?", (call_id,))
                cursor.execute("DELETE FROM calls WHERE call_id = ?", (call_id,))
                
                conn.commit()
                
                # Update monthly summary
                self.update_monthly_summary(agent_id, call_date)