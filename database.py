# database.py
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from database_postgres import PostgresCallAnalysisDB

class CallAnalysisDB:
    """Database handler for call analysis data"""

    def __new__(cls, db_path: str = "call_analysis.db"):
        backend = os.getenv("DATABASE_BACKEND", "sqlite").strip().lower()
        if backend in {"postgres", "postgresql", "supabase"}:
            database_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
            source = "SUPABASE_DB_URL" if os.getenv("SUPABASE_DB_URL") else "DATABASE_URL"
            if not database_url:
                raise ValueError("SUPABASE_DB_URL or DATABASE_URL must be set when DATABASE_BACKEND=postgres")
            parsed = urlparse(database_url)
            print(
                "[DB DEBUG] backend=postgres "
                f"source={source} "
                f"scheme={parsed.scheme or 'unknown'} "
                f"host={parsed.hostname or 'missing'} "
                f"port={parsed.port or 'missing'} "
                f"user={parsed.username or 'missing'} "
                f"db={parsed.path.lstrip('/') or 'missing'}"
            )
            schema = os.getenv("DB_SCHEMA", "call_analysis")
            return PostgresCallAnalysisDB(database_url=database_url, schema=schema)
        return super().__new__(cls)
    
    def __init__(self, db_path: str = "call_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
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
                    customer_sentiment TEXT,
                    customer_text_sample TEXT,
                    customer_sentiment_confidence REAL,
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
                    score REAL NOT NULL,
                    confidence REAL,
                    explanation TEXT,
                    matched_phrase TEXT,
                    holistic_score REAL,
                    frequency REAL,
                    frequency_score REAL,
                    semantic_quality REAL,
                    distribution REAL,
                    details_json TEXT,
                    text_scope TEXT,
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

            migration_statements = [
                "ALTER TABLE calls ADD COLUMN customer_sentiment TEXT",
                "ALTER TABLE calls ADD COLUMN customer_text_sample TEXT",
                "ALTER TABLE calls ADD COLUMN customer_sentiment_confidence REAL",
                "ALTER TABLE qa_scores ADD COLUMN holistic_score REAL",
                "ALTER TABLE qa_scores ADD COLUMN frequency REAL",
                "ALTER TABLE qa_scores ADD COLUMN frequency_score REAL",
                "ALTER TABLE qa_scores ADD COLUMN semantic_quality REAL",
                "ALTER TABLE qa_scores ADD COLUMN distribution REAL",
                "ALTER TABLE qa_scores ADD COLUMN details_json TEXT",
                "ALTER TABLE qa_scores ADD COLUMN text_scope TEXT"
            ]
            for statement in migration_statements:
                try:
                    cursor.execute(statement)
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
    
    def add_agent(self, agent_name: str, department: str = None) -> int:
        """Add a new agent"""
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            agent_id = self.add_agent(agent_name, call_data.get("department"))
            metadata = call_data.get('metadata', {})

            cursor.execute("""
                INSERT INTO calls (
                    agent_id, filename, call_date, call_type, duration_minutes,
                    transcript, sentiment, customer_sentiment, customer_text_sample,
                    customer_sentiment_confidence, processing_time_seconds, file_size_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                call_data['filename'],
                call_data.get('call_date', date.today()),
                call_data.get('call_type', 'Unknown'),
                metadata.get('duration_minutes', 0),
                call_data['transcript'],
                call_data.get('sentiment', 'Unknown'),
                call_data.get('customer_sentiment', 'unknown'),
                call_data.get('customer_text_sample', ''),
                call_data.get('customer_sentiment_confidence', 0),
                call_data.get('processing_time', 0),
                metadata.get('file_size_mb', 0)
            ))

            call_id = cursor.lastrowid

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

            for category, result in call_data.get('qa_results', {}).items():
                cursor.execute("""
                    INSERT INTO qa_scores (
                        call_id, scoring_method, category, score, confidence, explanation,
                        matched_phrase, holistic_score, frequency, frequency_score,
                        semantic_quality, distribution, details_json, text_scope
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_id,
                    'rule_based',
                    category,
                    result['score'],
                    result.get('confidence', 0),
                    result['explanation'],
                    result.get('matched_phrase', ''),
                    result.get('holistic_score', result.get('score', 0)),
                    result.get('frequency', 0),
                    result.get('frequency_score'),
                    result.get('semantic_quality'),
                    result.get('distribution'),
                    json.dumps(result.get('details', {})),
                    result.get('text_scope', 'agent_only')
                ))

            for category, result in call_data.get('qa_results_nlp', {}).items():
                cursor.execute("""
                    INSERT INTO qa_scores (
                        call_id, scoring_method, category, score, confidence, explanation,
                        matched_phrase, holistic_score, frequency, frequency_score,
                        semantic_quality, distribution, details_json, text_scope
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_id,
                    'nlp_enhanced',
                    category,
                    result['score'],
                    result.get('confidence', 0),
                    result['explanation'],
                    result.get('matched_phrase', ''),
                    result.get('holistic_score', result.get('score', 0)),
                    result.get('frequency', 0),
                    result.get('frequency_score'),
                    result.get('semantic_quality'),
                    result.get('distribution'),
                    json.dumps(result.get('details', {})),
                    result.get('text_scope', 'agent_only')
                ))

            conn.commit()
            self.update_monthly_summary(agent_id, call_data.get('call_date', date.today()))
            return call_id
    
    def update_monthly_summary(self, agent_id: int, call_date: date):
        """Update monthly summary for an agent"""
        year, month = call_date.year, call_date.month

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    COALESCE(SUM(c.duration_minutes), 0) as total_duration,
                    SUM(CASE WHEN LOWER(COALESCE(c.customer_sentiment, c.sentiment, '')) = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN LOWER(COALESCE(c.customer_sentiment, c.sentiment, '')) = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN LOWER(COALESCE(c.customer_sentiment, c.sentiment, '')) = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM calls c
                WHERE c.agent_id = ?
                AND strftime('%Y', c.call_date) = ?
                AND strftime('%m', c.call_date) = ?
            """, (agent_id, str(year), f"{month:02d}"))
            call_stats = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN COALESCE(qs.holistic_score, qs.score) END) as avg_nlp_score
                FROM qa_scores qs
                JOIN calls c ON qs.call_id = c.call_id
                WHERE c.agent_id = ?
                AND strftime('%Y', c.call_date) = ?
                AND strftime('%m', c.call_date) = ?
            """, (agent_id, str(year), f"{month:02d}"))
            score_stats = cursor.fetchone()

            stats = (
                call_stats[0] or 0,
                score_stats[0] or 0,
                score_stats[1] or 0,
                call_stats[1] or 0,
                call_stats[2] or 0,
                call_stats[3] or 0,
                call_stats[4] or 0,
            )

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
            start_date = date.today().replace(month=1, day=1)
        if not end_date:
            end_date = date.today()

        with sqlite3.connect(self.db_path) as conn:
            overview_calls_query = """
                SELECT 
                    COUNT(DISTINCT c.agent_id) as total_agents,
                    COUNT(*) as total_calls,
                    COALESCE(SUM(c.duration_minutes), 0) as total_duration_minutes
                FROM calls c
                WHERE c.call_date BETWEEN ? AND ?
            """
            overview_calls = pd.read_sql_query(overview_calls_query, conn, params=[start_date, end_date])

            overview_scores_query = """
                SELECT 
                    AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as avg_rule_score,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN COALESCE(qs.holistic_score, qs.score) END) as avg_nlp_score
                FROM qa_scores qs
                JOIN calls c ON qs.call_id = c.call_id
                WHERE c.call_date BETWEEN ? AND ?
            """
            overview_scores = pd.read_sql_query(overview_scores_query, conn, params=[start_date, end_date])
            overview = {
                **(overview_calls.to_dict('records')[0] if not overview_calls.empty else {}),
                **(overview_scores.to_dict('records')[0] if not overview_scores.empty else {})
            }

            agent_performance_query = """
                WITH scores_by_call AS (
                    SELECT 
                        qs.call_id,
                        AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as rule_score,
                        AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN COALESCE(qs.holistic_score, qs.score) END) as nlp_score
                    FROM qa_scores qs
                    GROUP BY qs.call_id
                )
                SELECT 
                    a.agent_name,
                    a.department,
                    COUNT(c.call_id) as total_calls,
                    AVG(sbc.rule_score) as avg_rule_score,
                    AVG(sbc.nlp_score) as avg_nlp_score,
                    COALESCE(SUM(c.duration_minutes), 0) as total_duration_minutes,
                    SUM(CASE WHEN LOWER(COALESCE(c.customer_sentiment, c.sentiment, '')) = 'positive' THEN 1 ELSE 0 END) as positive_calls,
                    SUM(CASE WHEN LOWER(COALESCE(c.customer_sentiment, c.sentiment, '')) = 'negative' THEN 1 ELSE 0 END) as negative_calls
                FROM agents a
                LEFT JOIN calls c ON a.agent_id = c.agent_id AND c.call_date BETWEEN ? AND ?
                LEFT JOIN scores_by_call sbc ON c.call_id = sbc.call_id
                WHERE a.is_active = 1
                GROUP BY a.agent_id, a.agent_name, a.department
                HAVING COUNT(c.call_id) > 0
                ORDER BY avg_rule_score DESC
            """
            agent_performance = pd.read_sql_query(agent_performance_query, conn, params=[start_date, end_date])

            monthly_trends_query = """
                WITH scores_by_call AS (
                    SELECT 
                        qs.call_id,
                        AVG(CASE WHEN qs.scoring_method = 'rule_based' THEN qs.score END) as rule_score,
                        AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN COALESCE(qs.holistic_score, qs.score) END) as nlp_score
                    FROM qa_scores qs
                    GROUP BY qs.call_id
                )
                SELECT 
                    strftime('%Y-%m', c.call_date) as month,
                    COUNT(*) as total_calls,
                    AVG(sbc.rule_score) as avg_rule_score,
                    AVG(sbc.nlp_score) as avg_nlp_score
                FROM calls c
                LEFT JOIN scores_by_call sbc ON c.call_id = sbc.call_id
                WHERE c.call_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', c.call_date)
                ORDER BY month
            """
            monthly_trends = pd.read_sql_query(monthly_trends_query, conn, params=[start_date, end_date])

            category_breakdown_query = """
                SELECT 
                    qs.category,
                    qs.scoring_method,
                    AVG(CASE WHEN qs.scoring_method = 'nlp_enhanced' THEN COALESCE(qs.holistic_score, qs.score) ELSE qs.score END) as avg_score,
                    COUNT(*) as total_evaluations
                FROM qa_scores qs
                JOIN calls c ON qs.call_id = c.call_id
                WHERE c.call_date BETWEEN ? AND ?
                GROUP BY qs.category, qs.scoring_method
                ORDER BY qs.category, qs.scoring_method
            """
            category_breakdown = pd.read_sql_query(category_breakdown_query, conn, params=[start_date, end_date])

            return {
                'overview': overview,
                'agent_performance': agent_performance,
                'monthly_trends': monthly_trends,
                'category_breakdown': category_breakdown
            }
    
    def get_all_agents(self) -> List[str]:
        """Get list of all active agents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent_name FROM agents WHERE is_active = 1 ORDER BY agent_name")
            return [row[0] for row in cursor.fetchall()]
    
    def delete_call(self, call_id: int):
        """Delete a call and all related data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get agent and date for summary update
            cursor.execute("SELECT agent_id, call_date FROM calls WHERE call_id = ?", (call_id,))
            result = cursor. fetchone()
            if result:
                agent_id, call_date = result
                
                # Delete related records
                cursor.execute("DELETE FROM keywords WHERE call_id = ?", (call_id,))
                cursor.execute("DELETE FROM qa_scores WHERE call_id = ?", (call_id,))
                cursor.execute("DELETE FROM calls WHERE call_id = ?", (call_id,))
                
                conn.commit()
                
                # Update monthly summary
                self. update_monthly_summary(agent_id, call_date)

    def reassign_calls_to_agent(self, from_agent_name: str, to_agent_name: str, call_ids: List[int] = None) -> int:
        """
        Reassign calls from one agent to another.
        
        Args:
            from_agent_name: The misspelled/incorrect agent name
            to_agent_name: The correct agent name to reassign calls to
            call_ids: Optional list of specific call_ids to reassign.  If None, reassigns ALL calls.
        
        Returns:
            Number of calls reassigned
        """
        with sqlite3. connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get the source agent_id
            cursor.execute("SELECT agent_id FROM agents WHERE agent_name = ?", (from_agent_name,))
            from_result = cursor.fetchone()
            if not from_result:
                raise ValueError(f"Agent '{from_agent_name}' not found in database")
            from_agent_id = from_result[0]
            
            # Get or create the destination agent
            to_agent_id = self.add_agent(to_agent_name)
            
            # Get the call dates that will be affected (for updating monthly summaries)
            if call_ids:
                placeholders = ','.join(['?' for _ in call_ids])
                cursor.execute(f"""
                    SELECT DISTINCT call_id, call_date FROM calls 
                    WHERE agent_id = ? AND call_id IN ({placeholders})
                """, [from_agent_id] + call_ids)
            else:
                cursor.execute("""
                    SELECT DISTINCT call_id, call_date FROM calls WHERE agent_id = ? 
                """, (from_agent_id,))
            
            affected_calls = cursor. fetchall()
            affected_dates = set(row[1] for row in affected_calls)
            
            # Reassign the calls
            if call_ids:
                placeholders = ','.join(['?' for _ in call_ids])
                cursor.execute(f"""
                    UPDATE calls SET agent_id = ? 
                    WHERE agent_id = ? AND call_id IN ({placeholders})
                """, [to_agent_id, from_agent_id] + call_ids)
            else:
                cursor.execute("""
                    UPDATE calls SET agent_id = ?  WHERE agent_id = ?
                """, (to_agent_id, from_agent_id))
            
            reassigned_count = cursor.rowcount
            conn.commit()
            
            # Update monthly summaries for both agents for all affected months
            for call_date_str in affected_dates:
                if isinstance(call_date_str, str):
                    call_date_obj = datetime.strptime(call_date_str, '%Y-%m-%d'). date()
                else:
                    call_date_obj = call_date_str
                self.update_monthly_summary(from_agent_id, call_date_obj)
                self.update_monthly_summary(to_agent_id, call_date_obj)
            
            return reassigned_count

    def merge_agents(self, misspelled_name: str, correct_name: str, delete_misspelled: bool = True) -> Dict[str, Any]:
        """
        Merge a misspelled agent into the correct agent, moving all calls.
        
        Args:
            misspelled_name: The incorrect/misspelled agent name
            correct_name: The correct agent name
            delete_misspelled: Whether to deactivate the misspelled agent after merge
        
        Returns:
            Dictionary with merge results
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check misspelled agent exists
            cursor.execute("SELECT agent_id, agent_name FROM agents WHERE agent_name = ?", (misspelled_name,))
            misspelled = cursor.fetchone()
            if not misspelled:
                raise ValueError(f"Agent '{misspelled_name}' not found")
            
            # Get call count before merge
            cursor.execute("SELECT COUNT(*) FROM calls WHERE agent_id = ?", (misspelled[0],))
            call_count = cursor.fetchone()[0]
            
            # Reassign all calls
            reassigned = self. reassign_calls_to_agent(misspelled_name, correct_name)
            
            # Optionally deactivate the misspelled agent
            if delete_misspelled:
                cursor.execute("""
                    UPDATE agents SET is_active = 0 WHERE agent_name = ? 
                """, (misspelled_name,))
                conn.commit()
            
            return {
                'misspelled_agent': misspelled_name,
                'correct_agent': correct_name,
                'calls_reassigned': reassigned,
                'misspelled_deactivated': delete_misspelled
            }

    def list_agents_with_call_counts(self) -> List[Dict[str, Any]]:
        """List all agents with their call counts to help identify misspellings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    a. agent_id,
                    a.agent_name,
                    a.is_active,
                    COUNT(c.call_id) as call_count
                FROM agents a
                LEFT JOIN calls c ON a.agent_id = c.agent_id
                GROUP BY a.agent_id
                ORDER BY a. agent_name
            """)
            return [
                {'agent_id': row[0], 'agent_name': row[1], 'is_active': bool(row[2]), 'call_count': row[3]}
                for row in cursor.fetchall()
            ]