from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

# Sentiment setup
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# Keywords for detection
KEYWORDS = [
    # Core and extended keywords
    "vulnerable", "late payment", "complaint", "refund", "threaten", 
    "unable to pay", "harassment", "collection", "financial difficulties",
    "mental health", "depression", "sectioned", "stress", "injury", "signed off",
    "struggling", "suicide", "breathing space", "death", "domestic violence",
    "diagnosis", "terminal", "cancer", "bipolar", "PTSD", "ADHD", "autism",
    "manager", "write off", "dv", "scam", "police", "bereavement", "deaf",
    "blind", "disabled", "unemployed", "homeless", "irresponsible", "illness",
    "surgery", "feeling low", "anxiety", "stressed", "terminal illness",
    "hospital", "side effects", "funeral costs", "grieving", "domestic abuse",
    "addiction", "drug", "gambling", "alcohol"
]

def find_keywords(text):
    text_lower = text.lower()
    found = []

    for phrase in KEYWORDS:
        pattern = rf"\b{re.escape(phrase.lower())}\b"
        for match in re.finditer(pattern, text_lower):
            found.append({
                "phrase": phrase,
                "start": match.start(),
                "end": match.end()
            })

    return found

# ✅ FCA QA Scoring Categories
def score_call(transcript):
    transcript = transcript.lower()
    scores = {
        "Customer Understanding": 0,
        "Fair Treatment": 0,
        "Vulnerability Handling": 0,
        "Resolution & Support": 0
    }

    # --- Category 1: Customer Understanding ---
    if any(phrase in transcript for phrase in ["do you understand", "let me explain", "does that make sense", "is that clear"]):
        scores["Customer Understanding"] = 1

    # --- Category 2: Fair Treatment ---
    if any(phrase in transcript for phrase in ["we're here to help", "take your time", "you have options", "we won’t pressure you"]):
        scores["Fair Treatment"] = 1

    # --- Category 3: Vulnerability Handling ---
    if find_keywords(transcript):
        if any(phrase in transcript for phrase in ["take a note of that", "i’ve flagged that", "we can offer support", "we'll pause things"]):
            scores["Vulnerability Handling"] = 1

    # --- Category 4: Resolution & Support ---
    if any(phrase in transcript for phrase in ["payment plan", "breathing space", "write off", "income and expenditure", "support team"]):
        scores["Resolution & Support"] = 1

    return scores
