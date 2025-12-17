#!/usr/bin/env python3
"""
NL2SQL Pipeline - Batch Mode
Run predefined natural language queries for testing.
"""

import sys
from nl2sql_pipeline import NL2SQLPipeline

# Test queries covering different scenarios
TEST_QUERIES = [
    # Basic queries
    "Show me the top 10 partners by number of solutions",
    "How many solutions are in each industry?",
    "What are the 3 technology areas available?",
    
    # Industry-specific queries
    "Find all healthcare AI solutions",
    "What partners offer financial services security solutions?",
    "Show manufacturing cloud solutions",
    
    # Technology queries
    "Which solutions have AI capabilities?",
    "List solutions with security features",
    "What are the cloud platform solutions for retail?",
    
    # Partner queries
    "Which partners serve multiple industries?",
    "Show me RSM's solutions",
    "What solutions does Elastic offer?",
    
    # Analytics queries
    "What's the distribution of solutions by technology area?",
    "Which sub-industries have the most solutions?",
    "Show recent solution updates in the last 30 days",
    
    # Complex queries
    "Find cross-industry partners with more than 5 solutions",
    "What percentage of solutions have marketplace links?",
    "Show education sector solutions grouped by technology",
    
    # Specific use cases
    "I need a compliance solution for financial services",
    "What AI solutions help with patient experience in healthcare?",
    "Show me smart factory solutions for manufacturing"
]


def main():
    """Run batch test queries."""
    print("\n" + "="*80)
    print("NL2SQL Pipeline - Batch Test Mode")
    print("Running predefined test queries")
    print("="*80 + "\n")
    
    pipeline = NL2SQLPipeline()
    
    success_count = 0
    total_count = len(TEST_QUERIES)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*80}")
        print(f"Test Query {i}/{total_count}")
        print(f"{'='*80}")
        
        try:
            pipeline.run_query(query, auto_execute=True)
            success_count += 1
        except Exception as e:
            print(f"\033[91m✗ Error: {str(e)}\033[0m\n")
        
        # Pause between queries for readability
        if i < total_count:
            input("\033[93mPress Enter to continue to next query...\033[0m")
    
    # Summary
    print("\n" + "="*80)
    print("Batch Test Summary")
    print("="*80)
    print(f"Total queries: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")
    print("="*80 + "\n")
    
    # Save history
    pipeline.save_history("nl2sql_batch_test_history.json")


if __name__ == "__main__":
    main()
