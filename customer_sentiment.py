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
    # Greetings and openings
    r"thank you for calling", r"thanks for calling", r"good morning", r"good afternoon",
    r"good evening", r"how can i help", r"how may i help", r"how can i assist",
    r"what can i do for you", r"welcome to", r"you're through to", r"my name is",
    r"speaking with", r"who am i speaking with",
    
    # Empathy and acknowledgment
    r"i understand", r"i apologize", r"i'm sorry to hear", r"i'm really sorry",
    r"i completely understand", r"i totally understand", r"that must be frustrating",
    r"that must be annoying", r"that must be difficult", r"i can see why",
    r"i appreciate your patience", r"thank you for your patience", r"i do apologize",
    r"apologies for", r"sorry about that", r"i can imagine", r"that's not ideal",
    r"i understand how frustrating", r"i know this is frustrating", r"i hear you",
    r"i can see how", r"that sounds frustrating", r"i'm sorry you've had to",
    
    # Action phrases
    r"i'll be happy to", r"i'd be happy to", r"i'll gladly", r"let me check that",
    r"let me look into", r"let me see", r"let me have a look", r"i'll just",
    r"let me just", r"bear with me", r"one moment please", r"just a moment",
    r"please hold", r"hold on", r"give me a second", r"give me a moment",
    r"i will transfer", r"let me transfer", r"i'll put you through",
    r"i will escalate", r"i'll raise this", r"i'll pass this on", r"let me get",
    r"i'll arrange", r"i'll organise", r"i'll organize", r"i'll set that up",
    r"i'll sort that", r"leave it with me", r"let me take care of",
    r"i can certainly", r"i can definitely", r"absolutely i can", r"of course i can",
    r"no problem at all", r"not a problem", r"i'll make a note", r"i've made a note",
    r"i'll update", r"i've updated", r"i'll process", r"i've processed",
    
    # Verification and compliance
    r"for data protection", r"for security purposes", r"to verify your", r"to confirm your",
    r"may i have", r"can i take", r"please confirm", r"can you confirm",
    r"could you confirm", r"just to confirm", r"just to verify", r"for verification",
    r"i just need to", r"before i can", r"i'll need to ask", r"security question",
    r"password", r"date of birth", r"postcode", r"zip code", r"address on file",
    r"account number", r"reference number", r"last four digits",
    
    # Information delivery
    r"i see that", r"i can see that", r"i can see here", r"according to our records",
    r"what i can see is", r"looking at your account", r"on your account",
    r"i can confirm", r"i can tell you", r"what's happened is", r"the reason is",
    r"this is because", r"the issue is", r"what i'll do is", r"the next step",
    r"what happens now", r"going forward", r"from now on",
    
    # Resolution confirmations
    r"i've now", r"that's all sorted", r"that's been done", r"that's gone through",
    r"you should see that", r"that's been processed", r"that's complete",
    r"that's been actioned", r"i've actioned", r"that's resolved", r"all done",
    r"you're all set", r"that should now", r"that will now", r"i've removed",
    r"i've added", r"i've changed", r"i've cancelled", r"i've canceled",
    r"i've refunded", r"i've credited", r"i've applied", r"i've waived",
    
    # Setting expectations
    r"this can take", r"this usually takes", r"you should receive", r"expect to see",
    r"within .* days", r"within .* hours", r"by the end of", r"allow up to",
    r"please allow", r"it may take", r"typically takes", r"normally takes",
    
    # Closing
    r"is there anything else", r"anything else i can help", r"is there anything more",
    r"what else can i", r"before you go", r"have a great day", r"have a lovely day",
    r"have a good day", r"have a nice day", r"take care", r"thank you for your patience",
    r"thanks for bearing with me", r"pleasure speaking", r"glad i could help",
    r"happy to help", r"if you have any other questions", r"don't hesitate to call",
    r"feel free to call back", r"we're here if you need", r"enjoy the rest of your day"
]

CUSTOMER_PATTERNS = [
    # Inquiry openers
    r"i'm calling about", r"i'm calling regarding", r"i'm calling to", r"i'm ringing about",
    r"i'm phoning about", r"i need help with", r"can you help me", r"can you tell me",
    r"could you tell me", r"i just wanted to know", r"i'm calling to check",
    r"i want to", r"i need to", r"i'd like to", r"i was wondering", r"i wanted to ask",
    r"i have a question", r"quick question", r"just a quick", r"i'm just checking",
    r"can i ask", r"could i ask", r"do you know", r"would you be able to",
    r"is it possible to", r"am i able to", r"can i", r"how do i", r"where do i",
    r"what do i need to", r"i'm trying to", r"i'm looking to", r"i'm hoping to",
    r"i received a letter", r"i got an email", r"i got a text", r"i got a message",
    r"someone called me", r"i missed a call", r"following up on", r"getting back to you",
    
    # Providing context
    r"so basically", r"so what happened", r"the thing is", r"the issue is",
    r"what's happened is", r"long story short", r"to cut a long story",
    
    # Confusion and problems
    r"my problem is", r"i'm having trouble", r"i am having trouble", r"i'm having issues",
    r"i'm having difficulty", r"i don't understand", r"i can't understand",
    r"i'm confused", r"i'm a bit confused", r"i'm not sure", r"i don't know why",
    r"this isn't working", r"this is not working", r"it's not working", r"it doesn't work",
    r"it won't let me", r"i can't", r"i couldn't", r"i tried", r"i've tried",
    r"not working", r"stopped working", r"it keeps", r"every time i",
    r"why is", r"why does", r"why can't i", r"why won't", r"when will",
    r"how come", r"how long", r"what's going on", r"what's happening",
    r"something's wrong", r"there's a problem", r"there's an issue", r"there's an error",
    r"i'm getting an error", r"it says", r"it's saying", r"it's telling me",
    r"i keep getting", r"i got an error", r"error message",
    
    # Frustration and complaints (negative)
    r"i am unhappy", r"i'm unhappy", r"i am frustrated", r"i'm frustrated",
    r"i am angry", r"i'm angry", r"i'm furious", r"i'm livid", r"i'm fuming",
    r"i'm not happy", r"i'm not pleased", r"i'm not impressed", r"i'm not satisfied",
    r"i have a complaint", r"i want to complain", r"i wish to complain",
    r"i am disappointed", r"i'm disappointed", r"i'm really disappointed",
    r"you're not helping", r"you're not listening", r"no one is helping",
    r"nobody is helping", r"nobody seems to", r"no one seems to",
    r"this is ridiculous", r"this is unacceptable", r"this is a joke",
    r"this is outrageous", r"this is disgraceful", r"this is shocking",
    r"absolutely useless", r"completely useless", r"waste of time", r"joke of a company",
    r"worst service", r"terrible service", r"appalling service", r"dreadful",
    r"i've called multiple times", r"i've called before", r"i've rung before",
    r"i've been waiting", r"i've been on hold", r"nobody has helped",
    r"no one has helped", r"this has been going on", r"i've already explained",
    r"i've told you", r"i've said this", r"how many times", r"i keep having to",
    r"i shouldn't have to", r"this should have been", r"this was supposed to",
    r"you promised", r"i was promised", r"i was told", r"i was assured",
    r"nothing has been done", r"still not resolved", r"still not fixed",
    r"still waiting", r"yet again", r"once again", r"here we go again",
    r"sick of this", r"sick and tired", r"had enough", r"fed up",
    r"at my wit's end", r"at the end of my tether", r"losing patience",
    r"lost patience", r"beyond frustrated", r"extremely disappointed",
    
    # Escalation requests
    r"i need to speak to (?:a|the)", r"can i speak to (?:a|your)", r"put me through to",
    r"i want to escalate", r"i want to make a complaint", r"i need a manager",
    r"i want a manager", r"i demand to speak", r"get me a supervisor",
    r"let me speak to someone else", r"someone more senior", r"your supervisor",
    r"your manager", r"complaints department", r"i want to take this further",
    r"i'll be taking this further", r"i'll go to the ombudsman", r"trading standards",
    r"i'll contact", r"i'll be contacting", r"hear from my solicitor", r"hear from my lawyer",
    
    # Urgency
    r"this is urgent", r"i need this sorted", r"i need this resolved", r"i need this fixed",
    r"as soon as possible", r"asap", r"right away", r"immediately", r"straight away",
    r"today", r"by the end of", r"i can't wait", r"time sensitive", r"critical",
    
    # Transactional requests
    r"cancel my", r"i need a refund", r"i want a refund", r"i'd like a refund",
    r"i want to close", r"i want to cancel", r"i'd like to cancel",
    r"i want my money back", r"refund me", r"credit my account",
    r"i want to return", r"i want compensation", r"i expect compensation",
    r"goodwill gesture", r"what are you going to do", r"how will you fix this",
    
    # Skepticism and doubt
    r"are you sure", r"is that right", r"that doesn't sound right", r"that can't be right",
    r"i don't think that's", r"i was told something different", r"that's not what i was told",
    r"i don't believe", r"really\?", r"seriously\?", r"you're joking",
    
    # Acceptance and understanding (neutral)
    r"okay", r"i see", r"right", r"i understand", r"fair enough", r"alright",
    r"got it", r"that makes sense", r"i understand now", r"oh i see",
    r"ah right", r"oh okay", r"that explains it", r"i didn't realise",
    r"i didn't realize", r"i wasn't aware", r"no one told me",
    
    # Positive and resolution
    r"perfect", r"that's perfect", r"that's great", r"that's brilliant", r"that's wonderful",
    r"that's fantastic", r"that's amazing", r"that's excellent", r"that's fab",
    r"thanks so much", r"thank you so much", r"thank you very much", r"really appreciate",
    r"much appreciated", r"i appreciate that", r"i appreciate your help",
    r"you've been (?:really |very |so )?helpful", r"you've been great",
    r"you've been brilliant", r"you've been amazing", r"you've been fantastic",
    r"that works", r"that's fine", r"that'll do", r"that's sorted then",
    r"brilliant", r"lovely", r"great stuff", r"wonderful", r"smashing", r"brill",
    r"okay great", r"excellent", r"superb", r"spot on",
    r"that's exactly what i needed", r"just what i needed", r"exactly what i was looking for",
    r"glad that's sorted", r"happy with that", r"i'm pleased", r"i'm satisfied",
    r"very happy", r"really pleased", r"so pleased", r"over the moon",
    r"thank goodness", r"what a relief", r"that's a relief", r"finally",
    r"at last", r"about time", r"you've made my day", r"really helpful",
    r"couldn't ask for more", r"above and beyond", r"excellent service",
    r"great service", r"fantastic service", r"best service", r"highly recommend",
    r"i'll be sure to", r"i'll definitely", r"will do thank", r"cheers",
    r"thanks a lot", r"thanks ever so much", r"ta", r"thanks a bunch"
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

# Thresholds
SENTENCE_CONFIDENCE_THRESHOLD = 0.12   # per-sentence confidence below this is treated as low
OVERALL_CONFIDENCE_THRESHOLD = 0.10    # final confidence below this -> 'unknown'
# Note: VADER thresholds now use same logic as analyser.py (net_sentiment = pos - neg)

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
    - FINAL FALLBACK: if nothing found, use all non-agent lines
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
    non_agent_lines = []  # Track all lines that aren't clearly agent
    
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
        if re.search(r'\b(customer|cust|c)[:\-\]]', l, re. IGNORECASE):
            customer_score += 2

        # heuristic: short lines 1-6 words that don't contain agent keywords are often customer short replies
        word_count = len(re.findall(r'\w+', l))
        if 1 <= word_count <= 8 and agent_score == 0:
            customer_score += 1

        # if punctuation like "?" often customer asking question
        if '?' in l:
            customer_score += 1

        # strip common speaker tags at start
        cleaned = re.sub(r'^\s*(?:customer|cust|c|agent|a|rep|advisor)[:\-\]\)]\s*', '', l, flags=re.IGNORECASE)
        
        # Track non-agent lines for final fallback
        if agent_score == 0:
            non_agent_lines.append(cleaned)

        if customer_score > agent_score or (customer_score > 0 and agent_score == 0):
            customer_segments.append(cleaned)

    # If we found customer segments, return them
    if customer_segments:
        return " ".join(customer_segments).strip()
    
    # 3) FINAL FALLBACK: If no customer segments found but we have non-agent lines,
    # use those (better than returning nothing)
    if non_agent_lines:
        return " ".join(non_agent_lines).strip()
    
    # 4) LAST RESORT: If transcript has content but no structure detected,
    # return the whole transcript for sentiment analysis (something is better than nothing)
    cleaned_transcript = transcript.strip()
    if len(cleaned_transcript) > 50:  # Only if there's meaningful content
        return cleaned_transcript
    
    return ""

def _vader_sentence_score(sentence: str) -> Tuple[str, float]:
    """
    Return (label, confidence) for a sentence using VADER. 
    Uses the same logic as analyser.py get_sentiment() for consistency.
    """
    scores = analyzer.polarity_scores(sentence)
    pos_score = scores. get("pos", 0.0)
    neg_score = scores.get("neg", 0.0)
    net_sentiment = pos_score - neg_score
    
    # Calculate confidence based on how far from neutral the score is
    # Net sentiment typically ranges from -0.3 to +0.3
    conf = min(abs(net_sentiment) * 3, 1.0)  # Scale to 0-1 range
    
    # Use same thresholds as analyser.py for consistency
    if net_sentiment >= 0.17:  # Top 33% - most positive
        return "positive", max(conf, 0.5)
    elif net_sentiment <= 0.12:  # Bottom 33% - least positive
        return "negative", max(conf, 0.5)
    else:  # Middle 33%
        return "neutral", max(conf, 0.4)

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

            # Add a neutral zone - if score_vote is very small, call it neutral
            if score_vote > 0.15:
                final_label = "positive"
                final_conf = abs(score_vote)
            elif score_vote < -0.15:
                final_label = "negative"
                final_conf = abs(score_vote)
            else:
                final_label = "neutral"
                final_conf = max(0.3, max(weight_v, weight_t))

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

        # Choose highest and remap neutral -> positive/negative
    best_score = max(pos_score, neg_score, neu_score)
    if best_score < OVERALL_CONFIDENCE_THRESHOLD:
        # low confidence overall -> unknown
        return "unknown", float(best_score), details

    if pos_score >= neg_score and pos_score >= neu_score:
        best_label = "positive"
    elif neg_score >= pos_score and neg_score >= neu_score:
        best_label = "negative"
    else:
        # neutral case -> remap to nearest of positive or negative based on pos vs neg weight
        best_label = "positive" if pos_score >= neg_score else "negative"

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