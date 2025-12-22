"""
Test the updated NL2SQL with seller-focused fields
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

# Test query
query = "What healthcare solutions help with regulatory compliance?"

print("=" * 80)
print(f"Testing Query: '{query}'")
print("=" * 80)

# Generate SQL
result = pipeline.generate_sql(query)

print("\n📊 Generated SQL:")
print(result['sql'])
print(f"\n💡 Explanation: {result['explanation']}")
print(f"🎯 Confidence: {result['confidence']}")

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
    columns = [desc[0] for desc in cursor.description]
    
    print(f"\n✅ Query executed successfully!")
    print(f"📊 Columns returned: {len(columns)}")
    print(f"📊 Rows returned: {len(rows)}")
    
    print("\n🔍 Columns in result:")
    for i, col in enumerate(columns, 1):
        seller_field = ""
        if col in ['marketPlaceLink', 'solutionOrgWebsite', 'geoName', 'solutionPlayName']:
            seller_field = " ✨ NEW SELLER FIELD"
        print(f"  {i}. {col}{seller_field}")
    
    if len(rows) > 0:
        print(f"\n🔍 First result sample:")
        for col in columns:
            value = rows[0][columns.index(col)]
            if value and col in ['marketPlaceLink', 'solutionOrgWebsite']:
                print(f"  {col}: {value}")
                
except Exception as e:
    print(f"\n❌ Error executing SQL: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
