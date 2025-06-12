
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import spacy
from fuzzywuzzy import fuzz

# Phrase table for NLP QA Scoring
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
    },
    "Customer Understanding": {
        "Clarity / Confusion": [
            "don't understand", "explain again", "confused", "not clear", "what does that mean",
            "say that again", "repeat that", "I’m not sure", "didn’t get that"
        ],
        "Understanding Agreement": [
            "I understand", "that makes sense", "I get it now", "thank you for explaining",
            "I see what you mean"
        ]
    },
    "Resolution and Support": {
        "Help / Support Offered": [
            "we can help", "let me help", "here’s what we can do", "we will support you",
            "you have options", "we can look at a plan", "don’t worry", "we’ll sort it", "I’ll check for you"
        ],
        "Action Steps or Resolution": [
            "set up a plan", "arrange a call", "speak to someone", "send an email", "complete the form",
            "we’ll pause the interest", "we’ll hold the account", "we’ll refer this"
        ]
    }
}

try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    raise Exception(f"Failed to load SpaCy model: {str(e)}. Install it with `python -m spacy download en_core_web_sm`.")

def extract_nlp_phrases(text):
    doc = nlp(text)
    return {
        "entities": list(set(ent.text.lower() for ent in doc.ents)),
        "noun_phrases": list(set(chunk.text.lower() for chunk in doc.noun_chunks)),
        "verbs": list(set(token.lemma_ for token in doc if token.pos_ == "VERB")),
    }

def match_any(phrases, text, threshold=85):
    text = text.lower()
    for phrase in phrases:
        if fuzz.partial_ratio(phrase.lower(), text) >= threshold:
            return True
    return False

def score_call_nlp(transcript, call_type):
    transcript_lower = transcript.lower()
    scores = {}

    # Vulnerability scoring
    vuln = (
        nlp_qa_phrase_table["Vulnerability"]["Mental Health"] +
        nlp_qa_phrase_table["Vulnerability"]["Physical Health"] +
        nlp_qa_phrase_table["Vulnerability"]["Financial Distress"]
    )
    scores["Vulnerability"] = {
        "score": 1 if match_any(vuln, transcript_lower) else 0,
        "explanation": "Customer mentioned vulnerability." if match_any(vuln, transcript_lower) else "No indicators of vulnerability."
    }

    # Customer Understanding
    understand = (
        nlp_qa_phrase_table["Customer Understanding"]["Clarity / Confusion"] +
        nlp_qa_phrase_table["Customer Understanding"]["Understanding Agreement"]
    )
    scores["Customer Understanding"] = {
        "score": 1 if match_any(understand, transcript_lower) else 0,
        "explanation": "Customer expressed understanding or confusion." if match_any(understand, transcript_lower) else "No signs of confusion or understanding."
    }

    # Resolution and Support
    res = (
        nlp_qa_phrase_table["Resolution and Support"]["Help / Support Offered"] +
        nlp_qa_phrase_table["Resolution and Support"]["Action Steps or Resolution"]
    )
    scores["Resolution Support"] = {
        "score": 1 if match_any(res, transcript_lower) else 0,
        "explanation": "Customer sought or received support." if match_any(res, transcript_lower) else "No resolution/support indicators."
    }

    return scores

# Sentiment
analyzer = SentimentIntensityAnalyzer()
def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    return "Positive" if score >= 0.05 else "Negative" if score <= -0.05 else "Neutral"

# Keywords
KEYWORDS = [
    "vulnerable", "late payment", "complaint", "refund", "threaten", "unable to pay", "harassment",
    "collection", "financial difficulties", "mental health", "depression", "sectioned", "stress",
    "injury", "signed off", "struggling", "suicide", "breathing space", "death", "domestic violence",
    "diagnosis", "terminal", "cancer", "bipolar", "PTSD", "ADHD", "autism", "manager", "write off",
    "dv", "scam", "police", "bereavement", "deaf", "blind", "disabled", "unemployed", "homeless",
    "irresponsible", "illness", "surgery", "feeling low", "anxiety", "stressed", "hospital",
    "side effects", "funeral costs", "grieving", "domestic abuse", "addiction", "drug", "gambling",
    "alcohol", "trauma", "bankruptcy", "arrears", "forbearance", "repossession", "mental capacity",
    "cognitive impairment", "neurological condition", "bereaved", "emotionally distressed",
    "psychiatric", "serious illness", "mobility issues", "chronic", "terminal diagnosis",
    "emergency help", "emotional support"
]

def find_keywords(text):
    text_lower = text.lower()
    found = []
    for phrase in KEYWORDS:
        pattern = rf"\b{re.escape(phrase)}\b"
        for match in re.finditer(pattern, text_lower):
            found.append({"phrase": phrase, "start": match.start(), "end": match.end()})
    return found

# Agent-facing QA scoring
SCORE_PHRASES = {
    "Customer Understanding": [
        "do you understand", "let me explain", "does that make sense", "is that clear",
        "just to clarify", "i’ll walk you through", "happy to explain again", "take your time to understand",
        "feel free to ask questions", "would you like me to repeat", "explain it simply", "easy to understand",
        "clear explanation", "any questions so far", "let me break that down", "i can rephrase that for you"
    ],
    "Fair Treatment": [
        "we're here to help", "take your time", "you have options", "we won’t pressure you",
        "we want what's best for you", "we’ll support you", "no obligation", "your decision",
        "you’re in control", "at your pace", "help you decide", "consider your situation",
        "it's completely up to you", "we won't rush you", "you're free to choose"
    ],
    "Vulnerability Handling": [
        "take a note of that", "i’ve flagged that", "we can offer support", "we'll pause things",
        "i’m noting you’re vulnerable", "we have options to help", "thank you for sharing",
        "i’ll record that", "offer extra help", "understand your situation", "additional support available"
    ],
    "Resolution & Support": [
        "payment plan", "breathing space", "write off", "income and expenditure", "support team",
        "arrangement", "alternative solution", "we can restructure", "pause your account",
        "reschedule", "repayment assistance", "financial support", "temporary forbearance"
    ]
}

def score_call(transcript, call_type="Collections"):
    transcript_lower = transcript.lower()
    scores = {}

    # Score based on agent behaviour using fuzzy match
    for category, phrases in SCORE_PHRASES.items():
        match = match_any(phrases, transcript_lower)
        scores[category] = {
            "score": 1 if match else 0,
            "explanation": f"Agent demonstrated {category.lower()}." if match else f"No clear signs of {category.lower()}."
        }

    # Filter based on call type
    if call_type == "Customer Service":
        scores = {k: v for k, v in scores.items() if k in ["Customer Understanding", "Fair Treatment"]}

    return scores