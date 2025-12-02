import sqlite3
from analyser import analyzer

# Connect to database
conn = sqlite3.connect('call_analysis.db')
cursor = conn.cursor()

# Get sample calls
cursor.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL LIMIT 10")
calls = cursor.fetchall()

print("Analyzing sample call transcripts.. .\n")
print("="*80)

for call_id, transcript in calls:
    if transcript and transcript.strip():
        # Get VADER scores
        scores = analyzer.polarity_scores(transcript)
        compound = scores["compound"]
        
        # Determine classification
        if compound >= 0.3:
            classification = "Positive"
        elif compound <= -0.1:
            classification = "Negative"
        else:
            classification = "Neutral"
        
        # Show first 200 chars of transcript
        preview = transcript[:200]. replace('\n', ' ')
        
        print(f"Call ID: {call_id}")
        print(f"Compound Score: {compound:.3f} -> {classification}")
        print(f"Pos: {scores['pos']:.2f} | Neg: {scores['neg']:.2f} | Neu: {scores['neu']:.2f}")
        print(f"Preview: {preview}...")
        print("-"*80)

conn.close()

# Show overall statistics
print("\n" + "="*80)
print("Checking all calls for score distribution...")
print("="*80)

conn = sqlite3.connect('call_analysis.db')
cursor = conn.cursor()
cursor.execute("SELECT transcript FROM calls WHERE transcript IS NOT NULL")

scores_list = []
for (transcript,) in cursor.fetchall():
    if transcript and transcript.strip():
        compound = analyzer.polarity_scores(transcript)["compound"]
        scores_list.append(compound)

conn.close()

import statistics

print(f"\nTotal calls analyzed: {len(scores_list)}")
print(f"Average compound score: {statistics. mean(scores_list):.3f}")
print(f"Median compound score: {statistics.median(scores_list):.3f}")
print(f"Min compound score: {min(scores_list):.3f}")
print(f"Max compound score: {max(scores_list):.3f}")
print(f"Std deviation: {statistics.stdev(scores_list):.3f}")

# Count by current thresholds
positive = sum(1 for s in scores_list if s >= 0.3)
negative = sum(1 for s in scores_list if s <= -0.1)
neutral = len(scores_list) - positive - negative

print(f"\nWith current thresholds (Pos >= 0.3, Neg <= -0.1):")
print(f"  Positive: {positive} ({positive/len(scores_list)*100:. 1f}%)")
print(f"  Negative: {negative} ({negative/len(scores_list)*100:.1f}%)")
print(f"  Neutral: {neutral} ({neutral/len(scores_list)*100:. 1f}%)")

# Suggest better thresholds
print(f"\n" + "="*80)
print("SUGGESTED THRESHOLD ADJUSTMENTS:")
print("="*80)

# Try stricter thresholds
strict_pos = sum(1 for s in scores_list if s >= 0.5)
strict_neg = sum(1 for s in scores_list if s <= -0.05)
strict_neu = len(scores_list) - strict_pos - strict_neg

print(f"\nWith stricter thresholds (Pos >= 0. 5, Neg <= -0. 05):")
print(f"  Positive: {strict_pos} ({strict_pos/len(scores_list)*100:.1f}%)")
print(f"  Negative: {strict_neg} ({strict_neg/len(scores_list)*100:.1f}%)")
print(f"  Neutral: {strict_neu} ({strict_neu/len(scores_list)*100:.1f}%)")

# Try even stricter
very_strict_pos = sum(1 for s in scores_list if s >= 0.6)
very_strict_neg = sum(1 for s in scores_list if s <= 0.0)
very_strict_neu = len(scores_list) - very_strict_pos - very_strict_neg

print(f"\nWith very strict thresholds (Pos >= 0.6, Neg <= 0.0):")
print(f"  Positive: {very_strict_pos} ({very_strict_pos/len(scores_list)*100:.1f}%)")
print(f"  Negative: {very_strict_neg} ({very_strict_neg/len(scores_list)*100:.1f}%)")
print(f"  Neutral: {very_strict_neu} ({very_strict_neu/len(scores_list)*100:.1f}%)")