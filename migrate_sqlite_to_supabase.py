import argparse
import json
import os
import sqlite3
from typing import Dict, Iterable, List, Sequence

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json


TABLE_COLUMNS = {
    "agents": [
        "agent_id",
        "agent_name",
        "department",
        "start_date",
        "is_active",
        "created_at",
    ],
    "calls": [
        "call_id",
        "agent_id",
        "filename",
        "call_date",
        "call_type",
        "duration_minutes",
        "transcript",
        "sentiment",
        "customer_sentiment",
        "customer_text_sample",
        "customer_sentiment_confidence",
        "processing_time_seconds",
        "file_size_mb",
        "created_at",
    ],
    "keywords": [
        "keyword_id",
        "call_id",
        "keyword_phrase",
        "confidence",
        "priority",
        "match_type",
    ],
    "qa_scores": [
        "score_id",
        "call_id",
        "scoring_method",
        "category",
        "score",
        "confidence",
        "explanation",
        "matched_phrase",
        "holistic_score",
        "frequency",
        "frequency_score",
        "semantic_quality",
        "distribution",
        "details_json",
        "text_scope",
    ],
    "monthly_summaries": [
        "summary_id",
        "agent_id",
        "year",
        "month",
        "total_calls",
        "avg_rule_score",
        "avg_nlp_score",
        "total_duration_minutes",
        "positive_sentiment_count",
        "negative_sentiment_count",
        "neutral_sentiment_count",
        "last_updated",
    ],
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Migrate historical CallAnalysisApp SQLite data into Supabase/Postgres."
    )
    parser.add_argument(
        "--sqlite-path",
        default="call_analysis.db",
        help="Path to the source SQLite database file.",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL"),
        help="Postgres connection string. Defaults to SUPABASE_DB_URL or DATABASE_URL.",
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("DB_SCHEMA", "call_analysis"),
        help="Destination Postgres schema.",
    )
    parser.add_argument(
        "--skip-monthly-summaries",
        action="store_true",
        help="Skip importing monthly_summaries if you prefer to rebuild them later.",
    )
    return parser.parse_args()


def get_sqlite_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row[1] for row in rows]


def fetch_rows(
    conn: sqlite3.Connection, table_name: str, desired_columns: Sequence[str]
) -> Iterable[Dict[str, object]]:
    available = get_sqlite_columns(conn, table_name)
    select_parts = []
    for column in desired_columns:
        if column in available:
            select_parts.append(column)
        else:
            select_parts.append(f"NULL AS {column}")

    conn.row_factory = sqlite3.Row
    query = f"SELECT {', '.join(select_parts)} FROM {table_name}"
    for row in conn.execute(query):
        yield dict(row)


def qname(schema: str, table_name: str):
    return sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table_name))


def reset_identity(cursor, schema: str, table_name: str, id_column: str):
    cursor.execute(
        sql.SQL(
            """
            SELECT setval(
                pg_get_serial_sequence(%s, %s),
                COALESCE((SELECT MAX({id_column}) FROM {table_ref}), 1),
                true
            )
            """
        ).format(
            id_column=sql.Identifier(id_column),
            table_ref=qname(schema, table_name),
        ),
        [f"{schema}.{table_name}", id_column],
    )


def migrate_agents(sqlite_conn, pg_cursor, schema: str) -> int:
    rows = list(fetch_rows(sqlite_conn, "agents", TABLE_COLUMNS["agents"]))
    for row in rows:
        pg_cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table_ref} (
                    agent_id, agent_name, department, start_date, is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (agent_id) DO UPDATE SET
                    agent_name = EXCLUDED.agent_name,
                    department = EXCLUDED.department,
                    start_date = EXCLUDED.start_date,
                    is_active = EXCLUDED.is_active,
                    created_at = EXCLUDED.created_at
                """
            ).format(table_ref=qname(schema, "agents")),
            [
                row["agent_id"],
                row["agent_name"],
                row["department"],
                row["start_date"],
                bool(row["is_active"]) if row["is_active"] is not None else True,
                row["created_at"],
            ],
        )
    return len(rows)


def migrate_calls(sqlite_conn, pg_cursor, schema: str) -> int:
    rows = list(fetch_rows(sqlite_conn, "calls", TABLE_COLUMNS["calls"]))
    for row in rows:
        pg_cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table_ref} (
                    call_id, agent_id, filename, call_date, call_type, duration_minutes,
                    transcript, sentiment, customer_sentiment, customer_text_sample,
                    customer_sentiment_confidence, processing_time_seconds, file_size_mb, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (call_id) DO UPDATE SET
                    agent_id = EXCLUDED.agent_id,
                    filename = EXCLUDED.filename,
                    call_date = EXCLUDED.call_date,
                    call_type = EXCLUDED.call_type,
                    duration_minutes = EXCLUDED.duration_minutes,
                    transcript = EXCLUDED.transcript,
                    sentiment = EXCLUDED.sentiment,
                    customer_sentiment = EXCLUDED.customer_sentiment,
                    customer_text_sample = EXCLUDED.customer_text_sample,
                    customer_sentiment_confidence = EXCLUDED.customer_sentiment_confidence,
                    processing_time_seconds = EXCLUDED.processing_time_seconds,
                    file_size_mb = EXCLUDED.file_size_mb,
                    created_at = EXCLUDED.created_at
                """
            ).format(table_ref=qname(schema, "calls")),
            [row[column] for column in TABLE_COLUMNS["calls"]],
        )
    return len(rows)


def migrate_keywords(sqlite_conn, pg_cursor, schema: str) -> int:
    rows = list(fetch_rows(sqlite_conn, "keywords", TABLE_COLUMNS["keywords"]))
    for row in rows:
        pg_cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table_ref} (
                    keyword_id, call_id, keyword_phrase, confidence, priority, match_type
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (keyword_id) DO UPDATE SET
                    call_id = EXCLUDED.call_id,
                    keyword_phrase = EXCLUDED.keyword_phrase,
                    confidence = EXCLUDED.confidence,
                    priority = EXCLUDED.priority,
                    match_type = EXCLUDED.match_type
                """
            ).format(table_ref=qname(schema, "keywords")),
            [row[column] for column in TABLE_COLUMNS["keywords"]],
        )
    return len(rows)


def parse_details_json(value):
    if value in (None, ""):
        return Json({})
    if isinstance(value, (dict, list)):
        return Json(value)
    try:
        return Json(json.loads(value))
    except (TypeError, json.JSONDecodeError):
        return Json({"raw": str(value)})


def migrate_qa_scores(sqlite_conn, pg_cursor, schema: str) -> int:
    rows = list(fetch_rows(sqlite_conn, "qa_scores", TABLE_COLUMNS["qa_scores"]))
    for row in rows:
        values = [row[column] for column in TABLE_COLUMNS["qa_scores"][:-2]]
        values.append(parse_details_json(row["details_json"]))
        values.append(row["text_scope"] or "agent_only")
        pg_cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table_ref} (
                    score_id, call_id, scoring_method, category, score, confidence,
                    explanation, matched_phrase, holistic_score, frequency, frequency_score,
                    semantic_quality, distribution, details_json, text_scope
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (score_id) DO UPDATE SET
                    call_id = EXCLUDED.call_id,
                    scoring_method = EXCLUDED.scoring_method,
                    category = EXCLUDED.category,
                    score = EXCLUDED.score,
                    confidence = EXCLUDED.confidence,
                    explanation = EXCLUDED.explanation,
                    matched_phrase = EXCLUDED.matched_phrase,
                    holistic_score = EXCLUDED.holistic_score,
                    frequency = EXCLUDED.frequency,
                    frequency_score = EXCLUDED.frequency_score,
                    semantic_quality = EXCLUDED.semantic_quality,
                    distribution = EXCLUDED.distribution,
                    details_json = EXCLUDED.details_json,
                    text_scope = EXCLUDED.text_scope
                """
            ).format(table_ref=qname(schema, "qa_scores")),
            values,
        )
    return len(rows)


def migrate_monthly_summaries(sqlite_conn, pg_cursor, schema: str) -> int:
    rows = list(
        fetch_rows(sqlite_conn, "monthly_summaries", TABLE_COLUMNS["monthly_summaries"])
    )
    for row in rows:
        pg_cursor.execute(
            sql.SQL(
                """
                INSERT INTO {table_ref} (
                    summary_id, agent_id, year, month, total_calls, avg_rule_score,
                    avg_nlp_score, total_duration_minutes, positive_sentiment_count,
                    negative_sentiment_count, neutral_sentiment_count, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (summary_id) DO UPDATE SET
                    agent_id = EXCLUDED.agent_id,
                    year = EXCLUDED.year,
                    month = EXCLUDED.month,
                    total_calls = EXCLUDED.total_calls,
                    avg_rule_score = EXCLUDED.avg_rule_score,
                    avg_nlp_score = EXCLUDED.avg_nlp_score,
                    total_duration_minutes = EXCLUDED.total_duration_minutes,
                    positive_sentiment_count = EXCLUDED.positive_sentiment_count,
                    negative_sentiment_count = EXCLUDED.negative_sentiment_count,
                    neutral_sentiment_count = EXCLUDED.neutral_sentiment_count,
                    last_updated = EXCLUDED.last_updated
                """
            ).format(table_ref=qname(schema, "monthly_summaries")),
            [row[column] for column in TABLE_COLUMNS["monthly_summaries"]],
        )
    return len(rows)


def print_counts(pg_cursor, schema: str):
    print("\nDestination counts:")
    for table_name in TABLE_COLUMNS:
        pg_cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(qname(schema, table_name))
        )
        print(f"  {table_name}: {pg_cursor.fetchone()[0]}")


def main():
    args = parse_args()
    if not args.database_url:
        raise ValueError(
            "Postgres connection string missing. Set SUPABASE_DB_URL or pass --database-url."
        )
    if not os.path.exists(args.sqlite_path):
        raise FileNotFoundError(f"SQLite database not found: {args.sqlite_path}")

    sqlite_conn = sqlite3.connect(args.sqlite_path)
    pg_conn = psycopg2.connect(args.database_url)

    try:
        pg_conn.autocommit = False
        with pg_conn.cursor() as pg_cursor:
            inserted = {}
            inserted["agents"] = migrate_agents(sqlite_conn, pg_cursor, args.schema)
            inserted["calls"] = migrate_calls(sqlite_conn, pg_cursor, args.schema)
            inserted["keywords"] = migrate_keywords(sqlite_conn, pg_cursor, args.schema)
            inserted["qa_scores"] = migrate_qa_scores(sqlite_conn, pg_cursor, args.schema)
            if not args.skip_monthly_summaries:
                inserted["monthly_summaries"] = migrate_monthly_summaries(
                    sqlite_conn, pg_cursor, args.schema
                )

            reset_identity(pg_cursor, args.schema, "agents", "agent_id")
            reset_identity(pg_cursor, args.schema, "calls", "call_id")
            reset_identity(pg_cursor, args.schema, "keywords", "keyword_id")
            reset_identity(pg_cursor, args.schema, "qa_scores", "score_id")
            reset_identity(pg_cursor, args.schema, "monthly_summaries", "summary_id")
            pg_conn.commit()

            print("Migration completed.")
            for table_name, count in inserted.items():
                print(f"  {table_name}: migrated {count} rows")
            print_counts(pg_cursor, args.schema)
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
