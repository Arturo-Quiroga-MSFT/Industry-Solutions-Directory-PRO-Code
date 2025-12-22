"""
Inspect the schema of dbo.vw_ISDSolution_All to see all available columns
"""

import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

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

print("=" * 80)
print("SCHEMA INSPECTION: dbo.vw_ISDSolution_All")
print("=" * 80)

# Method 1: Get column info from INFORMATION_SCHEMA
print("\n📋 Method 1: Using INFORMATION_SCHEMA.COLUMNS")
print("-" * 80)

query = """
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'vw_ISDSolution_All'
  AND TABLE_SCHEMA = 'dbo'
ORDER BY ORDINAL_POSITION
"""

cursor.execute(query)
columns = cursor.fetchall()

print(f"\nTotal columns: {len(columns)}\n")

for col in columns:
    col_name, data_type, max_length, nullable = col
    length_str = f"({max_length})" if max_length else ""
    print(f"  {col_name:40} {data_type}{length_str:20} {'NULL' if nullable == 'YES' else 'NOT NULL'}")

# Method 2: Get sample data to see what's actually populated
print("\n" + "=" * 80)
print("📊 Method 2: Sample Data (First Row)")
print("-" * 80)

query2 = "SELECT TOP 1 * FROM dbo.vw_ISDSolution_All WHERE solutionStatus = 'Approved'"
cursor.execute(query2)
sample_row = cursor.fetchone()
column_names = [desc[0] for desc in cursor.description]

if sample_row:
    print("\nShowing column names and whether they have data in first row:\n")
    for col_name, value in zip(column_names, sample_row):
        has_data = "✓ HAS DATA" if value is not None and str(value).strip() else "✗ NULL/EMPTY"
        value_preview = str(value)[:60] if value else "(null)"
        print(f"  {col_name:40} {has_data:15} {value_preview}")

# Method 3: Look for potential seller-relevant fields
print("\n" + "=" * 80)
print("🎯 Method 3: Potential Seller-Relevant Fields")
print("-" * 80)

seller_keywords = ['contact', 'email', 'link', 'url', 'marketplace', 'offer', 'partner', 'org', 'phone', 'azure', 'cosell']
relevant_columns = [col[0] for col in columns if any(keyword in col[0].lower() for keyword in seller_keywords)]

print("\nColumns that might be relevant for sellers:\n")
for col in relevant_columns:
    print(f"  • {col}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Inspection Complete")
print("=" * 80)
