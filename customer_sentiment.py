# customer_sentiment.py
import sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from typing import Dict, List, Tuple

analyzer = SentimentIntensityAnalyzer()

def identify_customer_segments(transcript: str) -> str:
    """
    Extract customer speech from call transcript using pattern recognition
    """
    if not transcript:
        return ""
    
    lines = transcript.split('\n')
    customer_segments = []
    
    # Agent language patterns
    agent_patterns = [
        r"thank you for calling",
        r"how can i help",
        r"i'll be happy to",
        r"let me check that",
        r"is there anything else",
        r"have a great day",
        r"i understand",
        r"i apologize",
        r"let me transfer",
        r"one moment please",
        r"i see that",
        r"according to our records"
    ]
    
    # Customer language patterns
    customer_patterns = [
        r"i need help with",
        r"my problem is",
        r"i'm having trouble",
        r"can you help me",
        r"i don't understand",
        r"this isn't working",
        r"i want to",
        r"why is",
        r"when will",
        r"i can't",
        r"it won't let me",
        r"i tried"
    ]
    
    for line in lines:
        if not line.strip():
            continue
            
        line_lower = line.lower()
        
        # Score for agent vs customer
        agent_score = sum(1 for pattern in agent_patterns 
                         if re.search(pattern, line_lower))
        customer_score = sum(1 for pattern in customer_patterns 
                           if re.search(pattern, line_lower))
        
        # Additional heuristics
        if any(word in line_lower for word in ['sir', 'madam', 'certainly', 'absolutely']):
            agent_score += 1
            
        if any(word in line_lower for word in ['frustrated', 'angry', 'upset', 'disappointed']):
            customer_score += 1
        
        # If more customer indicators or no clear agent indicators
        if customer_score > agent_score or (customer_score > 0 and agent_score == 0):
            customer_segments.append(line)
    
    return " ".join(customer_segments)

def analyze_customer_sentiment(customer_text: str) -> str:
    """
    Analyze sentiment specifically for customer speech
    Uses different thresholds than agent-inclusive analysis
    """
    if not customer_text.strip():
        return "unknown"
    
    scores = analyzer.polarity_scores(customer_text)
    compound = scores["compound"]
    
    # Customer-specific thresholds
    # Customers are more direct and less professionally polite
    if compound >= 0.1:  # Lower threshold for customer positive
        return "positive"
    elif compound <= -0.2:  # Customer complaints are more directly negative
        return "negative"
    else:
        return "neutral"

def get_customer_sentiment_analysis(transcript: str) -> Dict:
    """
    Complete customer sentiment analysis
    """
    customer_text = identify_customer_segments(transcript)
    
    if not customer_text.strip():
        return {
            "customer_sentiment": "unknown",
            "customer_text_found": False,
            "customer_text_sample": "",
            "confidence": 0.0,
            "raw_scores": {}
        }
    
    sentiment = analyze_customer_sentiment(customer_text)
    scores = analyzer.polarity_scores(customer_text)
    
    # Sample of customer text (first 200 chars)
    sample = customer_text[:200] + "..." if len(customer_text) > 200 else customer_text
    
    return {
        "customer_sentiment": sentiment,
        "customer_text_found": True,
        "customer_text_sample": sample,
        "confidence": abs(scores["compound"]),
        "raw_scores": {
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"],
            "compound": scores["compound"]
        }
    }

def update_customer_sentiment_db():
    """
    Add customer sentiment analysis to existing database
    """
    conn = sqlite3.connect('call_analysis.db')
    cursor = conn.cursor()
    
    # Add new column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_sentiment TEXT")
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_text_sample TEXT")
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_sentiment_confidence REAL")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Get all calls with transcripts
    cursor.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL")
    calls = cursor.fetchall()
    
    print(f"Analyzing customer sentiment for {len(calls)} calls...")
    
    updated = 0
    for call_id, transcript in calls:
        if transcript and transcript.strip():
            analysis = get_customer_sentiment_analysis(transcript)
            
            cursor.execute("""
                UPDATE calls 
                SET customer_sentiment = ?,
                    customer_text_sample = ?,
                    customer_sentiment_confidence = ?
                WHERE call_id = ?
            """, (
                analysis["customer_sentiment"],
                analysis["customer_text_sample"],
                analysis["confidence"],
                call_id
            ))
            
            updated += 1
            if updated % 50 == 0:
                print(f"Processed {updated}/{len(calls)} calls...")
                conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated customer sentiment for {updated} calls!")

if __name__ == "__main__":
    # Run the update
    update_customer_sentiment_db()