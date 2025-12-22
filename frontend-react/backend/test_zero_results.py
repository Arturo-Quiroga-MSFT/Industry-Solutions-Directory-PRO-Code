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

# Query 8 & 9: Supply chain visibility for retail
print("=" * 80)
print("Query 8 and 9: supply chain visibility in Retail")
print("=" * 80)
query1 = """
SELECT COUNT(*) as count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
  AND industryName = 'Retail & Consumer Goods'
  AND (
        solutionName LIKE '%supply chain visibility%' OR
        solutionDescription LIKE '%supply chain visibility%' OR
        theme LIKE '%supply chain visibility%' OR
        subIndustryName LIKE '%supply chain visibility%'
      )
"""
cursor.execute(query1)
result = cursor.fetchone()
print(f"Exact phrase 'supply chain visibility': {result[0]} results")

# Try broader terms
query2 = """
SELECT COUNT(*) as count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
  AND industryName = 'Retail & Consumer Goods'
  AND solutionDescription LIKE '%supply chain%'
"""
cursor.execute(query2)
result = cursor.fetchone()
print(f"Broader 'supply chain': {result[0]} results")

# Query 10: Point of sale systems
print()
print("=" * 80)
print("Query 10: point of sale systems")
print("=" * 80)
query3 = """
SELECT COUNT(*) as count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
  AND (
        solutionName LIKE '%point of sale systems%' OR
        solutionDescription LIKE '%point of sale systems%' OR
        theme LIKE '%point of sale systems%' OR
        subIndustryName LIKE '%point of sale systems%'
      )
"""
cursor.execute(query3)
result = cursor.fetchone()
print(f"Exact phrase 'point of sale systems': {result[0]} results")

# Try variations
query4 = """
SELECT COUNT(*) as count
FROM dbo.vw_ISDSolution_All
WHERE solutionStatus = 'Approved'
  AND (
        solutionDescription LIKE '%point of sale%' OR
        solutionDescription LIKE '%POS system%'
      )
"""
cursor.execute(query4)
result = cursor.fetchone()
print(f"Broader 'point of sale' or 'POS system': {result[0]} results")

cursor.close()
conn.close()
