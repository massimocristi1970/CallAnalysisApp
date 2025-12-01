import sqlite3
from analyser import get_sentiment

# Connect to database
conn = sqlite3.connect('call_analysis.db')
cursor = conn.cursor()

# Get all calls with transcripts
cursor.execute("SELECT call_id, transcript FROM calls WHERE transcript IS NOT NULL")
calls = cursor. fetchall()

print(f"Found {len(calls)} calls to process...")
print(f"Recalculating sentiment with new thresholds (Positive >= 0.3, Negative <= -0.1).. .\n")

positive_count = 0
negative_count = 0
neutral_count = 0
updated = 0

for call_id, transcript in calls:
    if transcript and transcript.strip():
        # Calculate new sentiment with updated thresholds
        new_sentiment = get_sentiment(transcript)
        
        # Update the database
        cursor.execute(
            "UPDATE calls SET sentiment = ?  WHERE call_id = ?",
            (new_sentiment, call_id)
        )
        
        # Track counts
        if new_sentiment. lower() == 'positive':
            positive_count += 1
        elif new_sentiment.lower() == 'negative':
            negative_count += 1
        else:
            neutral_count += 1
        
        updated += 1
        
        if updated % 100 == 0:
            print(f"Processed {updated}/{len(calls)} calls...")
            conn.commit()  # Commit in batches

# Final commit
conn.commit()
conn. close()

print(f"\n{'='*50}")
print(f"✅ DONE! Updated sentiment for {updated} calls.")
print(f"{'='*50}")
print(f"New sentiment breakdown:")
print(f"  Positive: {positive_count} ({positive_count/updated*100:.1f}%)")
print(f"  Negative: {negative_count} ({negative_count/updated*100:.1f}%)")
print(f"  Neutral:  {neutral_count} ({neutral_count/updated*100:.1f}%)")
print(f"\nNow refresh your dashboard to see the changes.")