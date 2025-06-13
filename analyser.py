from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import yaml
import os
from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import numpy as np
from typing import Dict, List, Tuple, Any
import hashlib
from cryptography.fernet import Fernet

# Global variables
_spacy_nlp = None
_config = None
_cipher_suite = None

@st.cache_resource
def load_config():
    """Load configuration from YAML file"""
    global _config
    if _config is None:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                _config = yaml.safe_load(file)
        except FileNotFoundError:
            st.error(f"Configuration file not found: {config_path}")
            _config = {}
        except yaml.YAMLError as e:
            st.error(f"Error parsing configuration file: {e}")
            _config = {}
    return _config

@st.cache_resource
def load_spacy_model():
    """Load spaCy model with caching"""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _spacy_nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            raise Exception(f"Failed to load SpaCy model: {e}. Try: python -m spacy download en_core_web_sm")
    return _spacy_nlp

def init_encryption():
    """Initialize encryption for secure file handling"""
    global _cipher_suite
    if _cipher_suite is None:
        config = load_config()
        key_file = config.get('security', {}).get('encryption_key_file', 'encryption.key')
        
        if not os.path.exists(key_file):
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
        else:
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
        
        _cipher_suite = Fernet(key)
    return _cipher_suite

# Sentiment setup
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text: str) -> str:
    """Analyze sentiment of text using VADER"""
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def redact_pii(text: str) -> str:
    """Redact personally identifiable information from text"""
    config = load_config()
    if not config.get('security', {}).get('redact_pii', False):
        return text
    
    redacted_text = text
    pii_patterns = config.get('pii_patterns', {})
    
    for category, patterns in pii_patterns.items():
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            replacement = pattern_info['replacement']
            redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)
    
    return redacted_text

def find_keywords_enhanced(text: str) -> List[Dict[str, Any]]:
    """Enhanced keyword detection with confidence scoring and fuzzy matching"""
    config = load_config()
    keywords_config = config.get('keywords', {})
    confidence_threshold = config.get('scoring', {}).get('keyword_confidence_threshold', 0.6)
    fuzzy_threshold = config.get('scoring', {}).get('fuzzy_threshold', 80)
    
    text_lower = text.lower()
    matches = []
    
    # Process keywords by priority
    for priority, keywords in keywords_config.items():
        priority_weight = {'high_priority': 1.0, 'medium_priority': 0.8, 'low_priority': 0.6}.get(priority, 0.5)
        
        for keyword in keywords:
            # Exact match
            pattern = rf"\b{re.escape(keyword.lower())}\b"
            for match in re.finditer(pattern, text_lower):
                confidence = priority_weight
                matches.append({
                    "phrase": keyword,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": confidence,
                    "match_type": "exact",
                    "priority": priority
                })
            
            # Fuzzy match for potential variations
            words = text_lower.split()
            for i, word in enumerate(words):
                ratio = fuzz.ratio(keyword.lower(), word)
                if ratio >= fuzzy_threshold:
                    confidence = (ratio / 100) * priority_weight
                    if confidence >= confidence_threshold:
                        # Find position in original text
                        word_start = text_lower.find(word)
                        matches.append({
                            "phrase": keyword,
                            "matched_text": word,
                            "start": word_start,
                            "end": word_start + len(word),
                            "confidence": confidence,
                            "match_type": "fuzzy",
                            "priority": priority,
                            "fuzzy_ratio": ratio
                        })
    
    # Remove duplicates and sort by confidence
    seen = set()
    unique_matches = []
    for match in matches:
        key = (match['start'], match['end'])
        if key not in seen:
            seen.add(key)
            unique_matches.append(match)
    
    return sorted(unique_matches, key=lambda x: x['confidence'], reverse=True)

def get_semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts using spaCy"""
    try:
        nlp = load_spacy_model()
        doc1 = nlp(text1)
        doc2 = nlp(text2)
        return doc1.similarity(doc2)
    except Exception as e:
        print(f"Warning: Could not calculate semantic similarity: {e}")
        return 0.0

def match_any_enhanced(phrases: List[str], text: str, use_semantic: bool = True) -> Tuple[bool, float, str]:
    """Enhanced matching with fuzzy and semantic similarity"""
    config = load_config()
    fuzzy_threshold = config.get('scoring', {}).get('fuzzy_threshold', 80)
    semantic_threshold = config.get('scoring', {}).get('semantic_threshold', 0.7)
    
    best_match = ""
    best_score = 0.0
    found_match = False
    
    text_lower = text.lower()
    
    for phrase in phrases:
        phrase_lower = phrase.lower()
        
        # Exact substring match
        if phrase_lower in text_lower:
            return True, 1.0, phrase
        
        # Fuzzy matching
        fuzzy_score = fuzz.partial_ratio(phrase_lower, text_lower)
        if fuzzy_score >= fuzzy_threshold:
            normalized_score = fuzzy_score / 100
            if normalized_score > best_score:
                best_score = normalized_score
                best_match = phrase
                found_match = True
        
        # Semantic similarity (if enabled and spaCy is available)
        if use_semantic:
            try:
                semantic_score = get_semantic_similarity(phrase, text)
                if semantic_score >= semantic_threshold:
                    if semantic_score > best_score:
                        best_score = semantic_score
                        best_match = phrase
                        found_match = True
            except Exception:
                pass  # Fallback to fuzzy matching only
    
    return found_match, best_score, best_match

def score_call_rule_based(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """Rule-based QA scoring using configured phrases"""
    config = load_config()
    agent_phrases = config.get('agent_behaviour_phrases', {})
    
    transcript = text.lower()
    scores = {}
    
    for category, phrases in agent_phrases.items():
        found, confidence, matched_phrase = match_any_enhanced(phrases, transcript, use_semantic=False)
        scores[category] = {
            "score": 1 if found else 0,
            "confidence": confidence,
            "matched_phrase": matched_phrase,
            "explanation": (
                f"Agent demonstrated expected behaviour: {category.lower()} (matched: '{matched_phrase}', confidence: {confidence:.2f})"
                if found else f"No evidence of agent demonstrating {category.lower()}."
            )
        }
    
    return scores

def score_call_nlp_enhanced(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """Enhanced NLP-based scoring using semantic analysis"""
    config = load_config()
    agent_phrases = config.get('agent_behaviour_phrases', {})
    nlp_concepts = config.get('nlp_concepts', {})
    
    transcript_lower = text.lower()
    scores = {}
    
    try:
        nlp = load_spacy_model()
        doc = nlp(text)
        
        # Extract entities and concepts from the transcript
        entities = [ent.text.lower() for ent in doc.ents]
        noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks]
        
        for category in agent_phrases.keys():
            # Rule-based matching
            rule_found, rule_confidence, rule_match = match_any_enhanced(
                agent_phrases.get(category, []), transcript_lower, use_semantic=True
            )
            
            # Concept-based matching
            concept_found = False
            concept_confidence = 0.0
            concept_match = ""
            
            if category in nlp_concepts:
                concept_phrases = nlp_concepts[category]
                concept_found, concept_confidence, concept_match = match_any_enhanced(
                    concept_phrases, transcript_lower, use_semantic=True
                )
            
            # Entity-based analysis
            entity_relevance = 0.0
            if entities:
                for entity in entities:
                    if category.lower() in entity or any(concept.lower() in entity for concept in nlp_concepts.get(category, [])):
                        entity_relevance = max(entity_relevance, 0.7)
            
            # Combine scores
            final_score = max(rule_confidence, concept_confidence, entity_relevance)
            found = final_score > 0.5
            
            explanation_parts = []
            if rule_found:
                explanation_parts.append(f"rule-based match: '{rule_match}' ({rule_confidence:.2f})")
            if concept_found:
                explanation_parts.append(f"concept match: '{concept_match}' ({concept_confidence:.2f})")
            if entity_relevance > 0:
                explanation_parts.append(f"entity relevance: {entity_relevance:.2f}")
            
            explanation = (
                f"NLP analysis for {category.lower()}: {', '.join(explanation_parts)}"
                if explanation_parts else f"No NLP indicators of {category.lower()} detected."
            )
            
            scores[category] = {
                "score": 1 if found else 0,
                "confidence": final_score,
                "rule_match": rule_match if rule_found else "",
                "concept_match": concept_match if concept_found else "",
                "entity_relevance": entity_relevance,
                "explanation": explanation
            }
    
    except Exception as e:
        print(f"Warning: NLP analysis failed, falling back to rule-based: {e}")
        return score_call_rule_based(text, call_type)
    
    return scores

def extract_nlp_insights(text: str) -> Dict[str, Any]:
    """Extract comprehensive NLP insights from text"""
    try:
        nlp = load_spacy_model()
        doc = nlp(text)
        
        insights = {
            "entities": [],
            "sentiment_breakdown": {},
            "key_phrases": [],
            "emotional_indicators": [],
            "complexity_score": 0.0
        }
        
        # Named entities
        for ent in doc.ents:
            insights["entities"].append({
                "text": ent.text,
                "label": ent.label_,
                "description": spacy.explain(ent.label_) if hasattr(spacy, 'explain') else ent.label_
            })
        
        # Sentence-level sentiment
        sentences = [sent.text for sent in doc.sents]
        for i, sentence in enumerate(sentences):
            sentiment = get_sentiment(sentence)
            insights["sentiment_breakdown"][f"sentence_{i+1}"] = {
                "text": sentence[:100] + "..." if len(sentence) > 100 else sentence,
                "sentiment": sentiment
            }
        
        # Key phrases (noun chunks with significance)
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:  # Multi-word phrases
                insights["key_phrases"].append(chunk.text)
        
        # Emotional indicators
        emotional_words = ["worried", "anxious", "stressed", "frustrated", "angry", "upset", "concerned", "happy", "satisfied", "pleased"]
        for token in doc:
            if token.text.lower() in emotional_words:
                insights["emotional_indicators"].append({
                    "word": token.text,
                    "lemma": token.lemma_,
                    "context": text[max(0, token.idx-50):token.idx+50]
                })
        
        # Text complexity (based on sentence length and vocabulary diversity)
        avg_sentence_length = np.mean([len(sent.text.split()) for sent in doc.sents])
        unique_words = len(set(token.text.lower() for token in doc if token.is_alpha))
        total_words = len([token for token in doc if token.is_alpha])
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        complexity_score = min(1.0, (avg_sentence_length / 20) * 0.5 + lexical_diversity * 0.5)
        insights["complexity_score"] = complexity_score
        
        return insights
        
    except Exception as e:
        print(f"Warning: Could not extract NLP insights: {e}")
        return {
            "entities": [],
            "sentiment_breakdown": {},
            "key_phrases": [],
            "emotional_indicators": [],
            "complexity_score": 0.0
        }

# Maintain backward compatibility
def find_keywords(text: str) -> List[Dict[str, Any]]:
    """Backward compatible keyword finding"""
    enhanced_matches = find_keywords_enhanced(text)
    # Convert to old format for compatibility
    return [
        {
            "phrase": match["phrase"],
            "start": match["start"],
            "end": match["end"]
        }
        for match in enhanced_matches
    ]

def score_call(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """Backward compatible rule-based scoring"""
    return score_call_rule_based(text, call_type)

def score_call_nlp(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """Backward compatible NLP scoring"""
    return score_call_nlp_enhanced(text, call_type)
