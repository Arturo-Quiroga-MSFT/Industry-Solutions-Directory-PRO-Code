#!/usr/bin/env python3
"""
NL2SQL Quick Test - Simple one-off queries
"""

from nl2sql_pipeline import NL2SQLPipeline

# Initialize pipeline
pipeline = NL2SQLPipeline()

# Test queries
test_queries = [
    "Show me the top 5 healthcare AI solutions",
    "Which partners have the most solutions?",
    "How many solutions are there in each technology area?",
    "Find manufacturing cloud solutions"
]

print("\nNL2SQL Pipeline - Quick Test\n")
print("="*80 + "\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}/{len(test_queries)}: {query}")
    print(f"{'='*80}\n")
    
    pipeline.run_query(query, auto_execute=True)
    
    if i < len(test_queries):
        input("\nPress Enter for next query...")

print("\n" + "="*80)
print("Quick test complete!")
print("="*80 + "\n")
