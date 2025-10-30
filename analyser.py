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
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    print("Warning: cryptography module not available. Security features disabled.")

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
    if not CRYPTOGRAPHY_AVAILABLE:
        print("Warning: Encryption not available (cryptography module not installed)")
        return None
        
    if _cipher_suite is None:
        config = load_config()
        key_file = config.get('security', {}).get('encryption_key_file', 'encryption.key')
        
        try:
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
        except Exception as e:
            print(f"Warning: Could not initialize encryption: {e}")
            return None
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

def count_phrase_occurrences(phrases: List[str], text: str, use_semantic: bool = False) -> Dict[str, Any]:
    """
    Count how many times phrases/concepts appear in text with semantic understanding.
    Returns frequency, matches, and distribution across the text.
    """
    config = load_config()
    fuzzy_threshold = config.get('scoring', {}).get('fuzzy_threshold', 80)
    semantic_threshold = config.get('scoring', {}).get('semantic_threshold', 0.7)
    
    text_lower = text.lower()
    total_matches = []
    match_positions = []
    text_length = len(text)
    
    for phrase in phrases:
        phrase_lower = phrase.lower()
        
        # Exact substring matches
        start_pos = 0
        while True:
            pos = text_lower.find(phrase_lower, start_pos)
            if pos == -1:
                break
            total_matches.append({
                'phrase': phrase,
                'position': pos,
                'confidence': 1.0,
                'type': 'exact'
            })
            match_positions.append(pos)
            start_pos = pos + 1
        
        # Fuzzy matches (find similar phrases)
        words = text_lower.split()
        phrase_words = phrase_lower.split()
        
        # Sliding window for multi-word phrases
        if len(phrase_words) > 1:
            for i in range(len(words) - len(phrase_words) + 1):
                window = ' '.join(words[i:i+len(phrase_words)])
                fuzzy_score = fuzz.ratio(phrase_lower, window)
                if fuzzy_score >= fuzzy_threshold:
                    # Estimate position
                    estimated_pos = text_lower.find(window)
                    if estimated_pos != -1 and estimated_pos not in [m['position'] for m in total_matches]:
                        total_matches.append({
                            'phrase': phrase,
                            'matched_text': window,
                            'position': estimated_pos,
                            'confidence': fuzzy_score / 100,
                            'type': 'fuzzy'
                        })
                        match_positions.append(estimated_pos)
        
        # Semantic similarity (if enabled)
        if use_semantic:
            try:
                semantic_score = get_semantic_similarity(phrase, text)
                if semantic_score >= semantic_threshold:
                    # Add as a general semantic match
                    total_matches.append({
                        'phrase': phrase,
                        'position': -1,  # Semantic match doesn't have specific position
                        'confidence': semantic_score,
                        'type': 'semantic'
                    })
            except Exception:
                pass
    
    # Calculate distribution (how spread out are matches?)
    distribution_score = 0.0
    if match_positions:
        # Divide text into 5 segments
        segment_size = text_length / 5
        segments_with_matches = set()
        for pos in match_positions:
            segment = int(pos / segment_size) if segment_size > 0 else 0
            segments_with_matches.add(min(segment, 4))  # Cap at segment 4
        distribution_score = len(segments_with_matches) / 5.0
    
    # Get average confidence
    avg_confidence = np.mean([m['confidence'] for m in total_matches]) if total_matches else 0.0
    
    return {
        'frequency': len(total_matches),
        'matches': total_matches,
        'distribution': distribution_score,
        'avg_confidence': avg_confidence,
        'match_positions': match_positions
    }

def score_call_rule_based(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Enhanced rule-based QA scoring with frequency thresholds.
    Now requires multiple mentions for full credit.
    """
    config = load_config()
    agent_phrases = config.get('agent_behaviour_phrases', {})
    
    # Frequency thresholds
    min_full = config.get('scoring', {}).get('min_frequency_for_full_score', 2)
    min_partial = config.get('scoring', {}).get('min_frequency_for_partial_score', 1)
    
    transcript = text.lower()
    scores = {}
    
    for category, phrases in agent_phrases.items():
        # Count occurrences with frequency tracking
        occurrence_data = count_phrase_occurrences(phrases, transcript, use_semantic=False)
        
        frequency = occurrence_data['frequency']
        matches = occurrence_data['matches']
        avg_confidence = occurrence_data['avg_confidence']
        
        # Calculate score based on frequency
        if frequency >= min_full:
            score = 1.0  # Full credit
            explanation = f"Agent demonstrated {category.lower()} {frequency} times (excellent - {', '.join(set([m['phrase'] for m in matches[:3]]))}...)"
        elif frequency >= min_partial:
            score = 0.5  # Partial credit
            matched_phrase = matches[0]['phrase'] if matches else 'unknown'
            explanation = f"Agent demonstrated {category.lower()} {frequency} time(s) (needs improvement - mentioned '{matched_phrase}')"
        else:
            score = 0.0  # No credit
            explanation = f"No evidence of agent demonstrating {category.lower()}"
        
        scores[category] = {
            "score": score,
            "frequency": frequency,
            "confidence": avg_confidence,
            "matches": [m['phrase'] for m in matches[:5]],  # Store up to 5 matches
            "explanation": explanation
        }
    
    return scores

def score_call_nlp_enhanced(text: str, call_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Enhanced NLP-based scoring using Option A: Frequency × Semantic × Distribution.
    Provides holistic 0-1.0 score based on conversation-wide analysis.
    """
    config = load_config()
    agent_phrases = config.get('agent_behaviour_phrases', {})
    nlp_concepts = config.get('nlp_concepts', {})
    
    # Get weights from config
    freq_weight = config.get('scoring', {}).get('nlp_frequency_weight', 0.4)
    semantic_weight = config.get('scoring', {}).get('nlp_semantic_weight', 0.35)
    distribution_weight = config.get('scoring', {}).get('nlp_distribution_weight', 0.25)
    
    # Estimate call length from text (rough: ~150 words per minute)
    word_count = len(text.split())
    estimated_minutes = word_count / 150
    
    # Adjust frequency expectations based on call length
    if estimated_minutes < 5:
        expected_frequency = 1  # Short call
    elif estimated_minutes < 15:
        expected_frequency = 2  # Medium call
    else:
        expected_frequency = 3  # Long call
    
    transcript_lower = text.lower()
    scores = {}
    
    try:
        nlp = load_spacy_model()
        doc = nlp(text)
        
        # Extract conversation-wide features
        entities = [ent.text.lower() for ent in doc.ents]
        noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks]
        
        for category in agent_phrases.keys():
            # 1. FREQUENCY COMPONENT: Count phrase occurrences
            phrase_data = count_phrase_occurrences(
                agent_phrases.get(category, []), 
                transcript_lower, 
                use_semantic=True
            )
            phrase_frequency = phrase_data['frequency']
            phrase_distribution = phrase_data['distribution']
            phrase_confidence = phrase_data['avg_confidence']
            
            # 2. SEMANTIC COMPONENT: Check NLP concepts
            concept_data = count_phrase_occurrences(
                nlp_concepts.get(category, []), 
                transcript_lower, 
                use_semantic=True
            )
            concept_frequency = concept_data['frequency']
            concept_confidence = concept_data['avg_confidence']
            
            # 3. ENTITY RELEVANCE: Check if relevant entities present
            entity_relevance = 0.0
            if entities:
                relevant_entities = [e for e in entities if category.lower().split()[0] in e or 
                                    any(concept.lower() in e for concept in nlp_concepts.get(category, [])[:5])]
                entity_relevance = min(len(relevant_entities) / 3, 1.0)  # Cap at 1.0
            
            # Combine frequencies
            total_frequency = phrase_frequency + concept_frequency
            
            # Calculate normalized frequency score (0-1.0)
            frequency_score = min(total_frequency / expected_frequency, 1.0)
            
            # Calculate semantic quality score (0-1.0)
            semantic_quality = max(phrase_confidence, concept_confidence, entity_relevance)
            
            # Distribution score already 0-1.0
            distribution_score = max(phrase_distribution, concept_data['distribution'])
            
            # OPTION A FORMULA: Weighted combination
            final_score = (
                (frequency_score * freq_weight) +
                (semantic_quality * semantic_weight) +
                (distribution_score * distribution_weight)
            )
            
            # Cap at 1.0
            final_score = min(final_score, 1.0)
            
            # Determine binary pass/fail (>0.6 = pass)
            binary_score = 1 if final_score >= 0.6 else 0
            
            # Create detailed explanation
            explanation_parts = []
            if phrase_frequency > 0:
                explanation_parts.append(f"phrase frequency: {phrase_frequency}")
            if concept_frequency > 0:
                explanation_parts.append(f"concept matches: {concept_frequency}")
            if entity_relevance > 0:
                explanation_parts.append(f"entity relevance: {entity_relevance:.2f}")
            explanation_parts.append(f"distribution: {distribution_score:.2f}")
            explanation_parts.append(f"quality: {semantic_quality:.2f}")
            
            explanation = (
                f"NLP holistic score: {final_score:.2f} for {category.lower()} "
                f"({', '.join(explanation_parts)})"
            )
            
            scores[category] = {
                "score": binary_score,
                "holistic_score": final_score,  # NEW: 0-1.0 quality score
                "confidence": final_score,
                "frequency": total_frequency,
                "frequency_score": frequency_score,
                "semantic_quality": semantic_quality,
                "distribution": distribution_score,
                "explanation": explanation,
                "details": {
                    "phrase_frequency": phrase_frequency,
                    "concept_frequency": concept_frequency,
                    "entity_relevance": entity_relevance,
                    "expected_frequency": expected_frequency,
                    "estimated_call_minutes": round(estimated_minutes, 1)
                }
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
