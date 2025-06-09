from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import spacy

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


nlp = spacy.load("en_core_web_sm")

def extract_nlp_phrases(text):
    doc = nlp(text)
    entities = [ent.text.lower() for ent in doc.ents if ent.label_ in {"ORG", "GPE", "PERSON", "NORP", "MONEY", "TIME", "DATE", "EVENT"}]
    noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks]
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    return {
        "entities": list(set(entities)),
        "noun_phrases": list(set(noun_phrases)),
        "verbs": list(set(verbs)),
    }

def score_call_nlp(transcript, call_type=None):
    from collections import defaultdict
    transcript_lower = transcript.lower()

    section_scores = {}
    section_explanations = {}

    for section, subcats in nlp_qa_phrase_table.items():
        found = []
        for subcat, phrases in subcats.items():
            matches = [p for p in transcript_lower.split() if any(phrase in transcript_lower for phrase in phrases)]
            if matches:
                found.extend(matches)

        score = 1 if found else 0
        section_scores[section] = {
            "score": score,
            "explanation": f"{len(found)} relevant phrase(s) detected: {', '.join(found[:5])}" if found else "No relevant phrases detected."
        }

    return section_scores

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
    "addiction", "drug", "gambling", "alcohol",
    # New extended keywords
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

# ✅ FCA QA Scoring Categories
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
        "i’m noting you’re vulnerable", "we have options to help", "that’s sensitive information, thank you for sharing",
        "i’ll record that", "offer extra help", "understand your situation", "noted as vulnerable",
        "additional support available", "we take this seriously", "we can log this for future support"
    ],
    "Resolution & Support": [
        "payment plan", "breathing space", "write off", "income and expenditure", "support team",
        "arrangement", "alternative solution", "we can restructure", "support options",
        "pause your account", "reschedule", "repayment assistance", "financial support",
        "temporary forbearance", "we'll work with you", "tailored repayment plan"
    ]
}

def score_call(transcript, call_type="Collections"):
    transcript = transcript.lower()
    scores = {}

    # Limit which categories are scored based on call type
    call_type_map = {
        "Customer Service": ["Customer Understanding", "Fair Treatment"],
        "Collections": ["Fair Treatment", "Resolution & Support", "Vulnerability Handling"]
    }
    relevant_categories = call_type_map.get(call_type, list(SCORE_PHRASES.keys()))

    for category, phrases in SCORE_PHRASES.items():
        if category not in relevant_categories:
            continue  # Skip categories not relevant to this call type

        count = sum(1 for phrase in phrases if phrase in transcript)

        if count == 0:
            score = 0
            explanation = "No relevant phrases found."
        elif count == 1:
            score = 1
            explanation = "One relevant phrase detected."
        elif 2 <= count <= 3:
            score = 2
            explanation = f"{count} relevant phrases detected."
        else:
            score = 3
            explanation = f"{count} relevant phrases detected. Strong evidence of best practice."

        scores[category] = {
            "score": score,
            "explanation": explanation
        }

    return scores
