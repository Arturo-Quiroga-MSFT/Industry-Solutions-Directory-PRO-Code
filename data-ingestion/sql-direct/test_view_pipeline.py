#!/usr/bin/env python3
"""
Test the view-based NL2SQL pipeline with comprehensive queries
"""

from nl2sql_pipeline import NL2SQLPipeline

# Initialize pipeline
pipeline = NL2SQLPipeline()

# Test queries using the new view
test_queries = [
    "Show me healthcare AI solutions",
    "How many solutions are in each technology area?",
    "Which industries have the most solutions?",
    "Find financial services security solutions",
    "Show solutions with special offers",
    "List solutions available in Canada"
]

print("\n" + "="*80)
print("Testing View-Based NL2SQL Pipeline")
print("Using: dbo.vw_ISDSolution_All")
print("="*80 + "\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'#'*80}")
    print(f"# Test {i}/{len(test_queries)}")
    print(f"{'#'*80}\n")
    
    pipeline.run_query(query, auto_execute=True)
    
    if i < len(test_queries):
        input("\nPress Enter for next test...")

# Save history
pipeline.save_history("view_test_history.json")

print("\n" + "="*80)
print("✓ All tests complete!")
print("View-based queries are simpler and faster (no JOINs needed)")
print("="*80 + "\n")
