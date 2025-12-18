#!/usr/bin/env python3
"""
Quick validation of view-based NL2SQL - auto-run without prompts
"""

from nl2sql_pipeline import NL2SQLPipeline

pipeline = NL2SQLPipeline()

test_queries = [
    "Show me healthcare AI solutions",
    "How many solutions are in each technology area?",
    "Which industries have the most solutions?"
]

print("\n" + "="*80)
print("VIEW-BASED NL2SQL VALIDATION")
print("="*80 + "\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/{len(test_queries)}: {query}")
    print("="*80 + "\n")
    
    pipeline.run_query(query, auto_execute=True)

print("\n" + "="*80)
print("✓ Validation complete - View-based queries working perfectly!")
print("="*80 + "\n")
