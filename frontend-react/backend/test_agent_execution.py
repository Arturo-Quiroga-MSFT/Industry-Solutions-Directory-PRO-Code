"""
Test execution of the agent-based query
"""

import sys
sys.path.append('/Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct')

from nl2sql_pipeline import NL2SQLPipeline
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize pipeline
pipeline = NL2SQLPipeline()

# Test the query
query = "what agent based solutions do we have in the directory, and how many are about healthcare"

print("=" * 80)
print(f"Testing Query: '{query}'")
print("=" * 80)

# Generate SQL
result = pipeline.generate_sql(query)

print("\n📊 Generated SQL:")
print(result['sql'])

# Connect and execute
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

try:
    cursor.execute(result['sql'])
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    
    print(f"\n✅ Query executed successfully!")
    print(f"📊 Columns: {columns}")
    print(f"📊 Rows returned: {len(rows)}")
    
    if len(rows) > 0:
        # Show first row
        print(f"\n🔍 First result:")
        for col, val in zip(columns, rows[0]):
            print(f"   {col}: {val if len(str(val)) < 100 else str(val)[:100] + '...'}")
            
        # Check the healthcare count
        if 'healthcare_agent_solution_count' in columns:
            count_idx = columns.index('healthcare_agent_solution_count')
            healthcare_count = rows[0][count_idx]
            print(f"\n🏥 Healthcare agent solutions: {healthcare_count}")
            
except Exception as e:
    print(f"\n❌ Error executing SQL: {e}")

cursor.close()
conn.close()
