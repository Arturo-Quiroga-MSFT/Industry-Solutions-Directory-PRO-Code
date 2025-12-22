#!/usr/bin/env python3
"""
Test NL2SQL Pipeline to see what SQL is generated for specific queries
Compares generated SQL with expected/working SQL
"""

import sys
import os

# Add path for nl2sql_pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '../../data-ingestion/sql-direct'))
from nl2sql_pipeline import NL2SQLPipeline
from multi_agent_pipeline import MultiAgentPipeline

def test_nl2sql_generation():
    """Test what SQL gets generated for problem queries"""
    
    print("\n" + "="*80)
    print("NL2SQL GENERATION TEST")
    print("Testing what SQL is generated for 'Smart city' and 'Smart grid' queries")
    print("="*80)
    
    # Initialize pipeline
    nl2sql = NL2SQLPipeline()
    
    test_cases = [
        {
            "name": "Smart City Solutions",
            "question": "Smart city solutions",
            "expected_result": "Should find 1 result (Parsons iNET)"
        },
        {
            "name": "Smart Grid Solutions",
            "question": "Smart grid solutions",
            "expected_result": "Should find 0 results"
        },
        {
            "name": "Smart City Solutions (explicit)",
            "question": "Show me smart city solutions",
            "expected_result": "Should find 1 result"
        },
        {
            "name": "Solutions with 'smart' in name or description",
            "question": "Find solutions with smart in the name or description",
            "expected_result": "Should find many results (610+)"
        }
    ]
    
    for idx, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {idx}: {test['name']}")
        print(f"{'='*80}")
        print(f"Question: \"{test['question']}\"")
        print(f"Expected: {test['expected_result']}")
        print()
        
        try:
            # Generate SQL
            print("🧠 Generating SQL...")
            result = nl2sql.generate_sql(test['question'])
            
            if result.get('sql'):
                print(f"\n📝 Generated SQL:\n")
                print(result['sql'])
                print()
                
                if result.get('explanation'):
                    print(f"💡 Explanation: {result['explanation']}")
                    print()
                
                if result.get('confidence'):
                    print(f"🎯 Confidence: {result['confidence']}")
                    print()
                
                # Execute the query
                print("⚙️  Executing query...")
                exec_result = nl2sql.execute_sql(result['sql'])
                
                if exec_result.get('error'):
                    print(f"❌ ERROR: {exec_result['error']}")
                else:
                    row_count = len(exec_result.get('rows', []))
                    print(f"✅ SUCCESS: Found {row_count} results")
                    
                    # Show first result if available
                    if row_count > 0:
                        rows = exec_result['rows']
                        cols = exec_result['columns']
                        print(f"\n📋 First result:")
                        for col in cols[:5]:  # Show first 5 columns
                            try:
                                if hasattr(rows[0], col):
                                    value = getattr(rows[0], col)
                                elif isinstance(rows[0], dict):
                                    value = rows[0].get(col)
                                else:
                                    idx_col = cols.index(col)
                                    value = rows[0][idx_col]
                                
                                val_str = str(value)[:100] if value else 'NULL'
                                print(f"  {col}: {val_str}")
                            except Exception as e:
                                print(f"  {col}: (error reading value)")
            else:
                print("❌ No SQL generated")
                if result.get('error'):
                    print(f"Error: {result['error']}")
        
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")
    print("""
Key things to check in the generated SQL:
1. Is it using the correct column name 'theme' (not 'themeName')?
2. Is it searching in solutionDescription field for text matches?
3. Is it using LIKE '%smart city%' for partial matches?
4. Is it using DISTINCT to avoid duplicates from denormalized view?
5. Is it filtering on solutionStatus = 'Approved'?

Common issues:
- Using wrong column names (themeName vs theme)
- Not searching in description fields
- Case sensitivity (should use LIKE for case-insensitive)
- Missing DISTINCT causing duplicate counts
    """)

def test_multi_agent_pipeline():
    """Test the full multi-agent pipeline"""
    print("\n" + "="*80)
    print("MULTI-AGENT PIPELINE TEST")
    print("Testing full pipeline with insights generation")
    print("="*80)
    
    pipeline = MultiAgentPipeline()
    
    question = "Smart city solutions"
    print(f"\nQuestion: \"{question}\"\n")
    
    try:
        result = pipeline.process_query(question)
        
        print("\n📊 RESULTS:")
        print(f"Success: {result['success']}")
        print(f"Row Count: {len(result.get('data', {}).get('rows', []))}")
        
        if result.get('sql'):
            print(f"\nGenerated SQL:\n{result['sql']}")
        
        if result.get('narrative'):
            print(f"\nNarrative:\n{result['narrative'][:500]}...")
        
        if result.get('insights'):
            print(f"\nInsights Preview:")
            insights = result['insights']
            if insights.get('overview'):
                print(f"  Overview: {insights['overview']}")
            if insights.get('key_findings'):
                print(f"  Key Findings: {len(insights['key_findings'])} items")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test NL2SQL generation
    test_nl2sql_generation()
    
    # Optionally test full multi-agent pipeline
    print("\n\n")
    response = input("Run full multi-agent pipeline test? (y/n): ")
    if response.lower() == 'y':
        test_multi_agent_pipeline()
