from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

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
import re

KEYWORDS = [
    "vulnerable", "late payment", "complaint", "refund", "threaten", 
    "unable to pay", "harassment", "collection", "financial difficulties"
]

def find_keywords(text):
    text_lower = text.lower()
    found = []

    for phrase in KEYWORDS:
        # Basic fuzzy match
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            found.append(phrase)

    return found
