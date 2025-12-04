# customer_sentiment_api.py
from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('call_analysis.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/customer-sentiment/overview")
def customer_sentiment_overview():
    """Get overall customer sentiment statistics"""
    where_sql = "1=1"
    params = []
    
    # Add filters
    if request.args.get("start_date"):
        where_sql += " AND call_date >= ?"
        params.append(request.args.get("start_date"))
    if request.args.get("end_date"):
        where_sql += " AND call_date <= ?"
        params.append(request. args.get("end_date"))
    if request.args.get("agent_id"):
        where_sql += " AND agent_id = ?"
        params.append(request. args.get("agent_id"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Overall distribution
    cur.execute(f"""
        SELECT 
            customer_sentiment,
            COUNT(*) as count
        FROM calls 
        WHERE customer_sentiment IS NOT NULL AND {where_sql}
        GROUP BY customer_sentiment
    """, params)
    
    distribution = {row["customer_sentiment"]: row["count"] for row in cur.fetchall()}
    
    # Comparison with overall sentiment
    cur.execute(f"""
        SELECT 
            sentiment as overall_sentiment,
            customer_sentiment,
            COUNT(*) as count
        FROM calls 
        WHERE customer_sentiment IS NOT NULL AND sentiment IS NOT NULL AND {where_sql}
        GROUP BY sentiment, customer_sentiment
    """, params)
    
    comparison_data = []
    for row in cur.fetchall():
        comparison_data.append({
            "overall_sentiment": row["overall_sentiment"],
            "customer_sentiment": row["customer_sentiment"],
            "count": row["count"]
        })
    
    conn. close()
    
    return jsonify({
        "distribution": distribution,
        "comparison": comparison_data,
        "labels": ["positive", "negative", "neutral", "unknown"],
        "colors": ["#22c55e", "#ef4444", "#94a3b8", "#6b7280"]
    })

@app.route("/api/customer-sentiment/by-agent")
def customer_sentiment_by_agent():
    """Get customer sentiment breakdown by agent"""
    where_sql = "1=1"
    params = []
    
    # Add filters
    if request.args.get("start_date"):
        where_sql += " AND c.call_date >= ?"
        params.append(request.args.get("start_date"))
    if request.args.get("end_date"):
        where_sql += " AND c.call_date <= ?"
        params. append(request.args.get("end_date"))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"""
        SELECT 
            a.agent_name,
            c.customer_sentiment,
            COUNT(*) as count,
            AVG(c.customer_sentiment_confidence) as avg_confidence
        FROM calls c
        LEFT JOIN agents a ON c.agent_id = a.agent_id
        WHERE c.customer_sentiment IS NOT NULL AND {where_sql}
        GROUP BY a.agent_name, c.customer_sentiment
        ORDER BY a.agent_name
    """, params)
    
    by_agent = {}
    for row in cur.fetchall():
        agent_name = row["agent_name"] or "Unknown"
        if agent_name not in by_agent:
            by_agent[agent_name] = {
                "agent_name": agent_name,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "unknown": 0,
                "avg_confidence": 0
            }
        
        sentiment = row["customer_sentiment"]
        by_agent[agent_name][sentiment] = row["count"]
        by_agent[agent_name]["avg_confidence"] = row["avg_confidence"] or 0
    
    conn. close()
    
    return jsonify({"by_agent": list(by_agent.values())})

@app.route("/api/customer-sentiment/samples/<sentiment>")
def get_sentiment_samples(sentiment):
    """Get sample customer text for a specific sentiment"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            call_id,
            customer_text_sample,
            customer_sentiment_confidence,
            call_date,
            duration_minutes
        FROM calls 
        WHERE customer_sentiment = ?  AND customer_text_sample IS NOT NULL
        ORDER BY customer_sentiment_confidence DESC
        LIMIT 10
    """, (sentiment,))
    
    samples = []
    for row in cur.fetchall():
        samples.append({
            "call_id": row["call_id"],
            "text_sample": row["customer_text_sample"],
            "confidence": row["customer_sentiment_confidence"],
            "call_date": row["call_date"],
            "duration_minutes": row["duration_minutes"]
        })
    
    conn.close()
    
    return jsonify({"samples": samples})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)