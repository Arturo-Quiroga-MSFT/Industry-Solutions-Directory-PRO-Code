#!/usr/bin/env python3
"""
Test ambiguous query detection and clarification
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../data-ingestion/sql-direct'))
from nl2sql_pipeline import NL2SQLPipeline

def test_ambiguous_queries():
    """Test queries that should trigger clarification"""
    
    nl2sql = NL2SQLPipeline()
    
    test_cases = [
        {
            "query": "smart solutions",
            "expected": "Should ask for clarification - too vague"
        },
        {
            "query": "AI",
            "expected": "Should ask for clarification - too broad"
        },
        {
            "query": "risk",
            "expected": "Should ask for clarification - ambiguous"
        },
        {
            "query": "smart city solutions",
            "expected": "Should NOT need clarification - specific phrase"
        }
    ]
    
    print("\n" + "="*80)
    print("AMBIGUOUS QUERY DETECTION TEST")
    print("="*80)
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected: {test['expected']}")
        print("="*80)
        
        result = nl2sql.generate_sql(test['query'])
        
        needs_clarification = result.get('needs_clarification', False)
        clarification_q = result.get('clarification_question')
        suggested = result.get('suggested_refinements', [])
        
        print(f"\n✓ Needs Clarification: {needs_clarification}")
        
        if needs_clarification:
            print(f"\n❓ Clarification Question:")
            print(f"   {clarification_q}")
            
            if suggested:
                print(f"\n💡 Suggested Refinements:")
                for s in suggested:
                    print(f"   - {s}")
        
        print(f"\n📝 Generated SQL (excerpt):")
        sql = result.get('sql', 'None')
        print(f"   {sql[:200]}...")
        
        print(f"\n💬 Explanation:")
        print(f"   {result.get('explanation', 'None')[:150]}...")

if __name__ == "__main__":
    test_ambiguous_queries()
