import sqlite3
from analyser import analyzer

conn = sqlite3.connect('call_analysis.db')
cursor = conn.cursor()
cursor.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL LIMIT 20")
calls = cursor.fetchall()

print("Analyzing pos/neg ratios for sample calls:\n")
print("="*80)

for call_id, transcript in calls:
    if transcript and transcript.strip():
        scores = analyzer.polarity_scores(transcript)
        pos = scores["pos"]
        neg = scores["neg"]
        neu = scores["neu"]
        net = pos - neg
        
        preview = transcript[:150]. replace('\n', ' ')
        
        print(f"Call {call_id}:")
        print(f"  Pos: {pos:.3f} | Neg: {neg:.3f} | Net: {net:.3f}")
        print(f"  Preview: {preview}...")
        print("-"*80)

conn. close()

# Check all calls
print("\n" + "="*80)
print("Analyzing ALL calls...")
print("="*80)

conn = sqlite3.connect('call_analysis.db')
cursor = conn.cursor()
cursor.execute("SELECT transcript FROM calls WHERE transcript IS NOT NULL")

pos_list = []
neg_list = []
net_list = []

for (transcript,) in cursor.fetchall():
    if transcript and transcript.strip():
        scores = analyzer.polarity_scores(transcript)
        pos_list.append(scores["pos"])
        neg_list.append(scores["neg"])
        net_list.append(scores["pos"] - scores["neg"])

conn.close()

import statistics

print(f"\nPositive scores:")
print(f"  Average: {statistics.mean(pos_list):.3f}")
print(f"  Min: {min(pos_list):.3f}")
print(f"  Max: {max(pos_list):.3f}")

print(f"\nNegative scores:")
print(f"  Average: {statistics.mean(neg_list):.3f}")
print(f"  Min: {min(neg_list):.3f}")
print(f"  Max: {max(neg_list):.3f}")

print(f"\nNet sentiment (pos - neg):")
print(f"  Average: {statistics.mean(net_list):.3f}")
print(f"  Median: {statistics.median(net_list):.3f}")
print(f"  Min: {min(net_list):.3f}")
print(f"  Max: {max(net_list):.3f}")

# Test different thresholds
print(f"\n" + "="*80)
print("TESTING DIFFERENT THRESHOLDS:")
print("="*80)

for pos_thresh, neg_thresh in [(0.15, -0.03), (0.12, -0.02), (0.10, -0.01), (0.08, 0.00)]:
    pos_count = sum(1 for n in net_list if n >= pos_thresh)
    neg_count = sum(1 for n in net_list if n <= neg_thresh)
    neu_count = len(net_list) - pos_count - neg_count
    
    print(f"\nThreshold: Pos >= {pos_thresh}, Neg <= {neg_thresh}")
    print(f"  Positive: {pos_count} ({pos_count/len(net_list)*100:.1f}%)")
    print(f"  Negative: {neg_count} ({neg_count/len(net_list)*100:.1f}%)")
    print(f"  Neutral: {neu_count} ({neu_count/len(net_list)*100:.1f}%)")