from database import CallAnalysisDB

db = CallAnalysisDB()

# Fix Bianca Mcarthur misspellings
result1 = db.merge_agents("Bianca nMcarthur", "Bianca Mcarthur")
print(f"Moved {result1['calls_reassigned']} calls from '{result1['misspelled_agent']}' to '{result1['correct_agent']}'")

result2 = db. merge_agents("Biana Mcarthur", "Bianca Mcarthur")
print(f"Moved {result2['calls_reassigned']} calls from '{result2['misspelled_agent']}' to '{result2['correct_agent']}'")

# Fix Bernadette Wykes misspelling
result3 = db.merge_agents("Bernadette Wyatt", "Bernadette Wykes")
print(f"Moved {result3['calls_reassigned']} calls from '{result3['misspelled_agent']}' to '{result3['correct_agent']}'")

print("\n=== Done!  Verify the results: ===")
for agent in db.list_agents_with_call_counts():
    if 'Bianca' in agent['agent_name'] or 'Bernadette' in agent['agent_name']:
        status = "active" if agent['is_active'] else "inactive"
        print(f"  {agent['agent_name']}: {agent['call_count']} calls ({status})")