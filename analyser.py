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
    results = {}

    # --- Category 1: Customer Understanding ---
    phrases = ["do you understand", "let me explain", "does that make sense", "is that clear"]
    found = any(p in transcript for p in phrases)
    results["Customer Understanding"] = {
        "score": int(found),
        "explanation": "Agent checked for understanding." if found else "No evidence of checking customer understanding."
    }

    # --- Category 2: Fair Treatment ---
    phrases = ["we're here to help", "take your time", "you have options", "we won’t pressure you"]
    found = any(p in transcript for p in phrases)
    results["Fair Treatment"] = {
        "score": int(found),
        "explanation": "Fair, non-pressured treatment offered." if found else "No clear reassurance or fair treatment wording detected."
    }

    # --- Category 3: Vulnerability Handling ---
    keywords_found = find_keywords(transcript)
    phrases = ["take a note of that", "i’ve flagged that", "we can offer support", "we'll pause things"]
    flagged = any(p in transcript for p in phrases)
    results["Vulnerability Handling"] = {
        "score": int(bool(keywords_found) and flagged),
        "explanation": "Potential vulnerability identified and acknowledged." if bool(keywords_found) and flagged
                      else "No clear handling of potential vulnerability."
    }

    # --- Category 4: Resolution & Support ---
    phrases = ["payment plan", "breathing space", "write off", "income and expenditure", "support team"]
    found = any(p in transcript for p in phrases)
    results["Resolution & Support"] = {
        "score": int(found),
        "explanation": "Practical support options were offered." if found else "No support options discussed."
    }

    return results
