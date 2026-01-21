"""
Fix Agent Name Misspellings
Merges misspelled agent names into the correct canonical name
"""

from database import CallAnalysisDB

db = CallAnalysisDB()

# Define all misspellings and their correct names
# Format: "Correct Name":  ["misspelling1", "misspelling2", ...]
AGENT_CORRECTIONS = {
    "Bianca Mcarthur": [
        "Bianca nMcarthur",
        "Biana Mcarthur"
    ],
    "Bernadette Wykes": [
        "Bernadette Wyatt"
    ],
"Bernadette Wykes": [
        "Bernadette Wykes "
    ],
    "David Pipe": [
        "David Piupe"
    ]
}

# Process all corrections
print("=" * 60)
print("  Agent Name Correction Tool")
print("=" * 60)

total_moved = 0

for correct_name, misspellings in AGENT_CORRECTIONS.items():
    print(f"\n📝 Processing: {correct_name}")

    for misspelled in misspellings:
        try:
            result = db.merge_agents(misspelled, correct_name)
            calls_moved = result['calls_reassigned']

            if calls_moved > 0:
                print(f"   ✅ Moved {calls_moved} calls from '{misspelled}'")
                total_moved += calls_moved
            else:
                print(f"   ℹ️  No calls found for '{misspelled}'")

        except ValueError:
            print(f"   ⚠️  '{misspelled}' not found (skipped)")

print("\n" + "=" * 60)
print(f"🎉 Complete! Total calls reassigned: {total_moved}")
print("=" * 60)

# Show current state of corrected agents
print("\n📊 Verification - Agent Call Counts:")
print("-" * 60)

for agent in db.list_agents_with_call_counts():
    if any(agent['agent_name'] == correct_name for correct_name in AGENT_CORRECTIONS.keys()):
        status = "✓ active" if agent['is_active'] else "✗ inactive"
        print(f"  {agent['agent_name']}:  {agent['call_count']} calls ({status})")

print()