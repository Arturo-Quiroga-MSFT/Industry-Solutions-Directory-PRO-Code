"""
Test the NL2SQL generation for queries that previously returned 0 results.
"""

import sys
import os
sys.path.append('/Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct')

from nl2sql_pipeline import NL2SQLPipeline
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# Initialize pipeline
pipeline = NL2SQLPipeline()

# Test queries that returned 0 results
test_queries = [
    "Supply chain visibility for retail",
    "Point of sale systems"
]

print("=" * 80)
print("Testing NL2SQL for Previously Zero-Result Queries")
print("=" * 80)

# Connect to database
conn_str = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={os.getenv('SQL_SERVER')};"
    f"Database={os.getenv('SQL_DATABASE')};"
    f"UID={os.getenv('SQL_USERNAME')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

for i, query in enumerate(test_queries, 1):
    print(f"\n{'=' * 80}")
    print(f"Test {i}: '{query}'")
    print('=' * 80)
    
    # Generate SQL
    result = pipeline.generate_sql(query)
    
    print(f"\n📊 Generated SQL:")
    print(result['sql'])
    print(f"\n💡 Explanation: {result['explanation']}")
    print(f"🎯 Confidence: {result['confidence']}")
    
    if result.get('needs_clarification'):
        print(f"\n⚠️  Needs clarification: {result['clarification_question']}")
        print(f"   Suggestions: {result['suggested_refinements']}")
    
    # Execute and count results
    if result['sql']:
        try:
            # Remove trailing semicolon if present (causes issues with subquery)
            sql_clean = result['sql'].rstrip(';').strip()
            count_sql = f"SELECT COUNT(*) FROM ({sql_clean}) AS subquery"
            cursor.execute(count_sql)
            count = cursor.fetchone()[0]
            print(f"\n✅ Results: {count} solutions found")
            
            if count == 0:
                print("   ❌ STILL RETURNING 0 RESULTS!")
            elif count > 0:
                print(f"   ✅ SUCCESS - Fixed! Now returning {count} results")
        except Exception as e:
            print(f"\n❌ Error executing SQL: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
