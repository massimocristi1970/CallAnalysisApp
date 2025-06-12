import re
import spacy
from fuzzywuzzy import fuzz
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# ---------- Keyword Detection ----------
KEYWORDS = [
    "vulnerable", "late payment", "complaint", "refund", "threaten", 
    "unable to pay", "harassment", "collection", "financial difficulties",
    "mental health", "depression", "sectioned", "stress", "injury", "signed off",
    "struggling", "suicide", "breathing space", "death", "domestic violence",
    "diagnosis", "terminal", "cancer", "bipolar", "PTSD", "ADHD", "autism",
    "manager", "write off", "dv", "scam", "police", "bereavement", "deaf",
    "blind", "disabled", "unemployed", "homeless", "irresponsible", "illness",
    "surgery", "feeling low", "anxiety", "stressed", "terminal illness",
    "hospital", "side effects", "funeral costs", "grieving", "domestic abuse",
    "addiction", "drug", "gambling", "alcohol",
    "trauma", "life event", "bankruptcy", "arrears", "forbearance", "repossession",
    "mental capacity", "cognitive impairment", "neurological condition", "bereaved",
    "emotionally distressed", "psychiatric", "serious illness", "mobility issues",
    "long-term condition", "chronic", "terminal diagnosis", "emergency help",
    "medical emergency", "emotional support"
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

# ---------- Phrase Tables for QA Scoring (Agent-Focused) ----------
AGENT_PHRASES = {
    "Customer Understanding": [
        "do you understand", "let me explain", "does that make sense", "is that clear",
        "just to clarify", "i’ll walk you through", "happy to explain again",
        "take your time to understand", "feel free to ask questions",
        "would you like me to repeat", "explain it simply", "easy to understand",
        "clear explanation", "any questions so far", "let me break that down",
        "i can rephrase that for you"
    ],
    "Fair Treatment": [
        "we're here to help", "take your time", "you have options",
        "we won’t pressure you", "we want what's best for you", "we’ll support you",
        "no obligation", "your decision", "you’re in control", "at your pace",
        "help you decide", "consider your situation", "it's completely up to you",
        "we won't rush you", "you're free to choose"
    ],
    "Vulnerability Handling": [
        "take a note of that", "i’ve flagged that", "we can offer support",
        "we'll pause things", "i’m noting you’re vulnerable", "we have options to help",
        "that’s sensitive information, thank you for sharing", "i’ll record that",
        "offer extra help", "understand your situation", "noted as vulnerable",
        "additional support available", "we take this seriously",
        "we can log this for future support"
    ],
    "Resolution & Support": [
        "payment plan", "breathing space", "write off", "income and expenditure",
        "support team", "arrangement", "alternative solution", "we can restructure",
        "support options", "pause your account", "reschedule",
        "repayment assistance", "financial support", "temporary forbearance",
        "we'll work with you", "tailored repayment plan"
    ]
}

# ---------- Rule-Based Scoring ----------
def score_call(transcript, call_type="Collections"):
    transcript = transcript.lower()
    scores = {}

    # Define which categories apply per call type
    call_type_map = {
        "Customer Service": ["Customer Understanding", "Fair Treatment"],
        "Collections": ["Customer Understanding", "Fair Treatment", "Resolution & Support", "Vulnerability Handling"]
    }
    relevant_categories = call_type_map.get(call_type, list(AGENT_PHRASES.keys()))

    for category, phrases in AGENT_PHRASES.items():
        if category not in relevant_categories:
            continue
        count = sum(1 for p in phrases if fuzz.partial_ratio(p, transcript) >= 85)

        if count == 0:
            score = 0
            explanation = "No relevant agent behaviour detected."
        elif count == 1:
            score = 1
            explanation = "One appropriate agent phrase detected."
        elif 2 <= count <= 3:
            score = 2
            explanation = f"{count} relevant phrases detected."
        else:
            score = 3
            explanation = f"{count} relevant phrases detected. Strong evidence of good agent behaviour."

        scores[category] = {"score": score, "explanation": explanation}

    return scores

# ---------- NLP-Based Scoring ----------
def score_call_nlp(transcript, call_type="Collections"):
    transcript_lower = transcript.lower()
    doc = nlp(transcript_lower)
    scores = {}

    def match_any(phrases, text, threshold=85):
        for phrase in phrases:
            if fuzz.partial_ratio(phrase, text) >= threshold:
                return True
        return False

    # Define which categories apply per call type
    call_type_map = {
        "Customer Service": ["Customer Understanding", "Fair Treatment"],
        "Collections": ["Customer Understanding", "Fair Treatment", "Resolution & Support", "Vulnerability Handling"]
    }
    relevant_categories = call_type_map.get(call_type, list(AGENT_PHRASES.keys()))

    for category, phrases in AGENT_PHRASES.items():
        if category not in relevant_categories:
            continue
        matched = match_any(phrases, transcript_lower)
        scores[category] = {
            "score": 1 if matched else 0,
            "explanation": "Agent demonstrated appropriate behaviour." if matched else "No matching agent behaviour found."
        }

    return scores

# ---------- Sentiment ----------
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
