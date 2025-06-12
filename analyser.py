from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import spacy
from fuzzywuzzy import fuzz

# ✅ PHRASE TABLES FOR AGENT BEHAVIOUR SCORING
AGENT_BEHAVIOUR_PHRASES = {
    "Customer Understanding": [
        "do you understand", "let me explain", "does that make sense", "is that clear",
        "just to clarify", "i’ll walk you through", "happy to explain again", "take your time to understand",
        "feel free to ask questions", "would you like me to repeat", "explain it simply", "easy to understand",
        "clear explanation", "any questions so far", "let me break that down", "i can rephrase that for you"
    ],
    "Fair Treatment": [
        "we're here to help", "take your time", "you have options", "we won’t pressure you",
        "we want what's best for you", "we’ll support you", "no obligation", "your decision",
        "you’re in control", "we’ll do our best", "treat you fairly", "understand your situation"
    ],
    "Vulnerability Handling": [
        "can I ask if you’re okay", "do you need any support", "we support mental health",
        "are you getting help", "do you have a medical condition", "we can pause the account",
        "we can send a breathing space form", "you don’t have to explain", "we understand vulnerability"
    ],
    "Financial Difficulty": [
        "we can set up a plan", "we can work something out", "affordable repayment",
        "can pause payments", "need income and expenditure", "repayment flexibility",
        "let's look at options", "freeze interest", "we’ll be fair"
    ],
    "Resolution & Support": [
        "we’ll investigate", "we’ll raise a complaint", "we can escalate this",
        "here’s what we’ll do", "next steps", "i’ve raised that for you", "we’ll send confirmation"
    ]
}

# ✅ NLP Phrase Table (for customer-expressed content)
nlp_qa_phrase_table = {
    "Vulnerability": {
        "Mental Health": [
            "mental health", "anxiety", "depression", "panic attack", "stress", "mental breakdown",
            "sectioned", "PTSD", "trauma", "bipolar", "OCD", "ADHD", "autism", "autistic"
        ],
        "Physical Health": [
            "surgery", "operation", "hospital", "in recovery", "terminal illness", "diagnosed with cancer",
            "chronic pain", "disability", "wheelchair", "seizure", "paralysed", "chemotherapy", "diabetes"
        ],
        "Financial Distress": [
            "lost my job", "redundant", "benefits", "on universal credit", "income dropped", "reduced hours",
            "can't afford", "financial difficulty", "money problems", "no savings", "rent arrears",
            "council tax debt", "struggling financially"
        ]
    }
}

# ✅ Sentiment setup
analyzer = SentimentIntensityAnalyzer()

try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise Exception(f"Failed to load SpaCy model: {e}. Try: python -m spacy download en_core_web_sm")

# ✅ Text sentiment analysis
def get_sentiment(text):
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# ✅ Keyword detection (static list)
KEYWORDS = [
    "vulnerable", "late payment", "complaint", "refund", "threaten",
    "unable to pay", "harassment", "collection", "financial difficulties",
    "mental health", "depression", "sectioned", "stress", "injury", "signed off",
    "struggling", "suicide", "breathing space", "death", "domestic violence",
    "diagnosis", "terminal", "cancer", "bipolar", "PTSD", "ADHD", "autism",
    "manager", "write off", "dv", "scam", "police", "bereavement", "deaf",
    "blind", "disabled", "unemployed", "homeless", "irresponsible", "illness",
    "surgery", "feeling low", "anxiety", "stressed", "side effects", "grieving",
    "drug", "addiction", "alcohol", "repossession", "arrears", "forbearance"
]

def find_keywords(text):
    text_lower = text.lower()
    matches = []
    for phrase in KEYWORDS:
        pattern = rf"\b{re.escape(phrase)}\b"
        for match in re.finditer(pattern, text_lower):
            matches.append({"phrase": phrase, "start": match.start(), "end": match.end()})
    return matches

# ✅ Helper for fuzzy matching
def match_any(phrases, text, threshold=85):
    for phrase in phrases:
        if fuzz.partial_ratio(phrase.lower(), text) >= threshold:
            return True
    return False

# ✅ Rule-Based QA scoring (agent-focused)
def score_call(text, call_type):
    transcript = text.lower()
    scores = {}
    for category, phrases in AGENT_BEHAVIOUR_PHRASES.items():
        hit = match_any(phrases, transcript)
        scores[category] = {
            "score": 1 if hit else 0,
            "explanation": (
                f"Agent demonstrated expected behaviour: {category.lower()}."
                if hit else f"No evidence of agent demonstrating {category.lower()}."
            )
        }
    return scores

# ✅ NLP-Based QA scoring (agent-focused)
def score_call_nlp(transcript, call_type):
    transcript_lower = transcript.lower()
    scores = {}

    for category, phrases in AGENT_BEHAVIOUR_PHRASES.items():
        hit = match_any(phrases, transcript_lower)
        scores[category] = {
            "score": 1 if hit else 0,
            "explanation": (
                f"Agent behaviour detected relating to: {category.lower()}."
                if hit else f"No NLP indicators of {category.lower()} from agent."
            )
        }

    return scores

# ✅ Optional NLP extraction (not currently used in scoring but retained for future use)
def extract_nlp_phrases(text):
    doc = nlp(text)
    return {
        "entities": list(set(ent.text.lower() for ent in doc.ents)),
        "noun_phrases": list(set(chunk.text.lower() for chunk in doc.noun_chunks)),
        "verbs": list(set(token.lemma_ for token in doc if token.pos_ == "VERB"))
    }
