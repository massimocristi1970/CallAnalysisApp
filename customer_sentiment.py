import sqlite3
import re
from typing import Dict, Tuple, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Optional transformer-based sentiment (better for some cases)
try:
    from transformers import pipeline
    _TRANSFORMER_AVAILABLE = True
    _TRANSFORMER_PIPE = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
except Exception:
    _TRANSFORMER_AVAILABLE = False
    _TRANSFORMER_PIPE = None

analyzer = SentimentIntensityAnalyzer()

# Speaker label detection
CUSTOMER_LABEL_RE = re.compile(r'^\s*(?:customer|cust|c|caller|client)[:\-\]\)]\s*(.*)$', re.IGNORECASE)
AGENT_LABEL_RE = re.compile(r'^\s*(?:agent|a|rep|advisor|operator|consultant)[:\-\]\)]\s*(.*)$', re.IGNORECASE)
BRACKET_SPEAKER_RE = re.compile(r'^\s*\[(agent|customer|caller|rep|a|c)\]\s*(.*)$', re.IGNORECASE)

# Expanded phrase lists (add more phrases here as you find them)
AGENT_PATTERNS = [
    r"thank you for calling", r"how can i help", r"i'll be happy to", r"let me check that",
    r"is there anything else", r"have a great day", r"i understand", r"i apologize",
    r"let me transfer", r"one moment please", r"i see that", r"according to our records",
    r"please hold", r"for data protection", r"may i have", r"hold on", r"bear with me",
    r"let me just", r"please confirm", r"i will transfer", r"i will escalate"
]

CUSTOMER_PATTERNS = [
    r"i need help with", r"my problem is", r"i'm having trouble", r"i am having trouble",
    r"can you help me", r"i don't understand", r"this isn't working", r"this is not working",
    r"i want to", r"why is", r"when will", r"i can't", r"it won't let me", r"i tried",
    r"i am unhappy", r"i am frustrated", r"i'm frustrated", r"i am angry", r"not working",
    r"cancel my", r"i have a complaint", r"i am disappointed", r"i need to speak to (?:a|the)",
    r"you're not helping", r"i'm not happy", r"this is ridiculous", r"this is urgent",
    r"i need a refund", r"i'm calling about", r"i'm calling regarding"
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

# Thresholds you'll likely tune
SENTENCE_CONFIDENCE_THRESHOLD = 0.12   # per-sentence confidence below this is treated as low
OVERALL_CONFIDENCE_THRESHOLD = 0.15    # final confidence below this -> 'unknown'
VADER_POS_THRESH = 0.15                # per-sentence VADER pos threshold
VADER_NEG_THRESH = -0.25               # per-sentence VADER neg threshold

def extract_customer_from_labeled_transcript(transcript: str) -> str:
    """Return concatenated lines explicitly labeled as customer (if present)."""
    lines = transcript.splitlines()
    customer_lines = []
    for line in lines:
        m = CUSTOMER_LABEL_RE.match(line)
        if m:
            customer_lines.append(m.group(1).strip())
            continue
        m = BRACKET_SPEAKER_RE.match(line)
        if m and m.group(1).lower().startswith('c'):
            customer_lines.append(m.group(2).strip())
            continue
        # Also detect inline 'Customer:' later in line
        inline = re.search(r'\b(customer|cust|caller|client)[:\-\]]\s*(.*)', line, re.IGNORECASE)
        if inline:
            customer_lines.append(inline.group(2).strip())
    return " ".join(customer_lines).strip()

def identify_customer_segments(transcript: str) -> str:
    """
    Improved extraction:
    - Prefer explicit speaker labels (Customer:, C:, [C], etc.)
    - Fall back to heuristic line scoring with expanded patterns
    - Use simple cleaning to strip speaker tags
    """
    if not transcript:
        return ""

    # 1) try labeled extraction (high precision)
    labeled = extract_customer_from_labeled_transcript(transcript)
    if labeled:
        return labeled

    # 2) fallback heuristic: score each line
    lines = transcript.splitlines()
    customer_segments = []
    for line in lines:
        if not line.strip():
            continue
        l = line.strip()
        low = l.lower()

        # quick skip if it's an agent-labeled line
        if AGENT_LABEL_RE.match(l):
            continue

        agent_score = sum(1 for p in AGENT_PATTERNS if re.search(p, low))
        customer_score = sum(1 for p in CUSTOMER_PATTERNS if re.search(p, low))

        # boost if explicit "Customer:" occurs in the line
        if re.search(r'\b(customer|cust|c)[:\-\]]', l, re.IGNORECASE):
            customer_score += 2

        # heuristic: short lines 1-6 words that don't contain agent keywords are often customer short replies
        word_count = len(re.findall(r'\w+', l))
        if 1 <= word_count <= 8 and agent_score == 0:
            customer_score += 1

        # if punctuation like "?" often customer asking question
        if '?' in l:
            customer_score += 1

        if customer_score > agent_score or (customer_score > 0 and agent_score == 0):
            # strip common speaker tags at start
            cleaned = re.sub(r'^\s*(?:customer|cust|c|agent|a|rep|advisor)[:\-\]\)]\s*', '', l, flags=re.IGNORECASE)
            customer_segments.append(cleaned)

    return " ".join(customer_segments).strip()

def _vader_sentence_score(sentence: str) -> Tuple[str, float]:
    """Return (label, confidence) for a sentence using VADER."""
    scores = analyzer.polarity_scores(sentence)
    compound = scores.get("compound", 0.0)
    conf = abs(compound)
    if compound >= VADER_POS_THRESH:
        return "positive", conf
    if compound <= VADER_NEG_THRESH:
        return "negative", conf
    return "neutral", conf

def _transformer_score_batch(sentences: List[str]) -> List[Tuple[str, float]]:
    """
    Use transformer pipeline to score sentences.
    Returns list of (label, confidence) where label in {'POSITIVE','NEGATIVE'} mapped to our labels.
    If transformer not available, return empty list.
    """
    if not _TRANSFORMER_AVAILABLE or _TRANSFORMER_PIPE is None or len(sentences) == 0:
        return []
    try:
        results = _TRANSFORMER_PIPE(sentences, truncation=True)
        # results: [{'label':'POSITIVE','score':0.99}, ...]
        mapped = []
        for r in results:
            label = r.get("label", "").lower()
            score = float(r.get("score", 0.0))
            mapped_label = "positive" if "pos" in label else "negative"
            mapped.append((mapped_label, score))
        return mapped
    except Exception:
        return []

def analyze_customer_sentiment(customer_text: str) -> Tuple[str, float, Dict]:
    """
    Improve sentiment aggregation:
    - Split into sentences
    - Score each sentence with VADER and, if available, transformer
    - Aggregate with simple voting + weighted confidence
    Returns (label, confidence, raw_details)
    """
    if not customer_text or not customer_text.strip():
        return "unknown", 0.0, {}

    # Clean text a bit
    text = re.sub(r'\s+', ' ', customer_text).strip()

    sentences = re.split(SENTENCE_SPLIT_RE, text)
    sentences = [s.strip() for s in sentences if s.strip()]

    vader_results = []
    for s in sentences:
        lab, conf = _vader_sentence_score(s)
        vader_results.append((s, lab, conf))

    transformer_results = _transformer_score_batch(sentences) if _TRANSFORMER_AVAILABLE else []

    # Aggregate:
    pos_weight = 0.0
    neg_weight = 0.0
    neu_weight = 0.0
    total_weight = 0.0

    details = {"sentences": [], "use_transformer": _TRANSFORMER_AVAILABLE}

    for idx, (s, vlabel, vconf) in enumerate(vader_results):
        # transformer result if available
        tlabel, tconf = (None, 0.0)
        if transformer_results:
            tlabel, tconf = transformer_results[idx]
        # Combine confidences: give transformer more weight if present
        weight_v = vconf
        weight_t = tconf * 1.6 if tconf else 0.0

        # Per-sentence final label:
        # If transformer strongly confident (>0.7), take its label for this sentence
        if tconf >= 0.7:
            final_label = tlabel
            final_conf = max(vconf, tconf)
        else:
            # combine: sign of (weight_v * vader_sign + weight_t * transformer_sign)
            score_vote = 0.0
            if vlabel == "positive":
                score_vote += weight_v
            elif vlabel == "negative":
                score_vote -= weight_v
            if tlabel == "positive":
                score_vote += weight_t
            elif tlabel == "negative":
                score_vote -= weight_t

            if score_vote > 0.0:
                final_label = "positive"
                final_conf = abs(score_vote)
            elif score_vote < 0.0:
                final_label = "negative"
                final_conf = abs(score_vote)
            else:
                final_label = "neutral"
                final_conf = max(weight_v, weight_t)

        # accumulate
        if final_label == "positive":
            pos_weight += final_conf
        elif final_label == "negative":
            neg_weight += final_conf
        else:
            neu_weight += final_conf
        total_weight += final_conf

        details["sentences"].append({
            "text": s,
            "vader": {"label": vlabel, "conf": vconf},
            "transformer": {"label": tlabel, "conf": tconf},
            "final": {"label": final_label, "conf": final_conf}
        })

    # Decide overall label
    if total_weight <= 0:
        return "unknown", 0.0, details

    # Normalize
    pos_score = pos_weight / total_weight
    neg_score = neg_weight / total_weight
    neu_score = neu_weight / total_weight

    # Choose highest
    best_label = "neutral"
    best_score = max(pos_score, neg_score, neu_score)
    if best_score < OVERALL_CONFIDENCE_THRESHOLD:
        # low confidence overall -> unknown
        return "unknown", float(best_score), details

    if pos_score >= neg_score and pos_score >= neu_score:
        best_label = "positive"
    elif neg_score >= pos_score and neg_score >= neu_score:
        best_label = "negative"
    else:
        best_label = "neutral"

    return best_label, float(best_score), details

def get_customer_sentiment_analysis(transcript: str) -> Dict:
    """
    Complete customer sentiment analysis wrapper.
    """
    customer_text = identify_customer_segments(transcript)
    if not customer_text:
        return {
            "customer_sentiment": "unknown",
            "customer_text_found": False,
            "customer_text_sample": "",
            "confidence": 0.0,
            "raw_scores": {}
        }

    label, confidence, raw_details = analyze_customer_sentiment(customer_text)
    sample = customer_text[:200] + "..." if len(customer_text) > 200 else customer_text
    return {
        "customer_sentiment": label,
        "customer_text_found": True,
        "customer_text_sample": sample,
        "confidence": confidence,
        "raw_scores": raw_details
    }

def update_customer_sentiment_db():
    """
    Add/update customer sentiment analysis to existing database (call_analysis.db in cwd)
    """
    conn = sqlite3.connect('call_analysis.db')
    cursor = conn.cursor()

    # Ensure columns exist
    try:
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_sentiment TEXT")
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_text_sample TEXT")
        cursor.execute("ALTER TABLE calls ADD COLUMN customer_sentiment_confidence REAL")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL")
    calls = cursor.fetchall()
    print(f"Analyzing customer sentiment for {len(calls)} calls...")

    updated = 0
    for call_id, transcript in calls:
        if not transcript or not transcript.strip():
            continue
        analysis = get_customer_sentiment_analysis(transcript)
        cursor.execute("""
            UPDATE calls SET customer_sentiment = ?, customer_text_sample = ?, customer_sentiment_confidence = ?
            WHERE call_id = ?
        """, (analysis["customer_sentiment"], analysis["customer_text_sample"], analysis["confidence"], call_id))
        updated += 1
        if updated % 50 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    print(f"✅ Updated customer sentiment for {updated} calls!")

if __name__ == "__main__":
    update_customer_sentiment_db()