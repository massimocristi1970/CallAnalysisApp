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

# FCA QA Scoring with extended phrases and scaled scoring
def score_call(transcript):
    transcript = transcript.lower()

    # Phrase lists (expanded)
    understanding_phrases = [
        "do you understand", "does that make sense", "is that clear", "let me explain",
        "just to clarify", "shall I go over that again", "are you with me so far", 
        "can I check you’re following", "do you follow what I’m saying", "i’ll explain that part again"
    ]

    fair_treatment_phrases = [
        "we're here to help", "take your time", "you have options", "we won’t pressure you",
        "there’s no rush", "whatever works best for you", "we’ll work with you", 
        "you’re in control", "no pressure at all", "we’ll support your decision"
    ]

    vulnerability_phrases = [
        "take a note of that", "i’ve flagged that", "we can offer support", "we'll pause things",
        "we take that seriously", "let’s get you some help", "we can give you time", 
        "you mentioned struggling", "let me make a note of that", "we’ll handle this sensitively"
    ]

    resolution_phrases = [
        "payment plan", "breathing space", "write off", "income and expenditure", 
        "support team", "we’ll review your budget", "let’s find a solution", 
        "arrangement", "hardship support", "let’s put something in place"
    ]

    # Scoring
    def score_category(phrases):
        matches = sum(1 for p in phrases if p in transcript)
        return 2 if matches > 1 else 1 if matches == 1 else 0

    return {
        "Customer Understanding": {
            "score": score_category(understanding_phrases),
            "explanation": "Evidence of checking or reinforcing understanding."
        },
        "Fair Treatment": {
            "score": score_category(fair_treatment_phrases),
            "explanation": "Evidence of treating customer fairly and with patience."
        },
        "Vulnerability Handling": {
            "score": score_category(vulnerability_phrases) if find_keywords(transcript) else 0,
            "explanation": "Recognition and appropriate handling of vulnerable disclosures."
        },
        "Resolution & Support": {
            "score": score_category(resolution_phrases),
            "explanation": "Evidence of support or effort to reach resolution."
        }
    }
