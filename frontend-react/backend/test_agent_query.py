"""
Test the specific query that's failing in the UI
"""

import sys
sys.path.append('/Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct')

from nl2sql_pipeline import NL2SQLPipeline
import json

# Initialize pipeline
pipeline = NL2SQLPipeline()

# Test the failing query
query = "what agent based solutions do we have in the directory, and how many are about healthcare"

print("=" * 80)
print(f"Testing Query: '{query}'")
print("=" * 80)

# Generate SQL
result = pipeline.generate_sql(query)

print("\n📊 Full Result:")
print(json.dumps(result, indent=2))

print("\n🔍 SQL Type:", type(result.get('sql')))
print("🔍 SQL Value:", repr(result.get('sql')))

if result.get('needs_clarification'):
    print("\n⚠️  Needs clarification:", result.get('clarification_question'))
    print("   Suggestions:", result.get('suggested_refinements'))
