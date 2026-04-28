#!/usr/bin/env python3
"""Quick SQL Server state check — run from sql-direct/ directory."""
import os, sys, pyodbc
from datetime import datetime

# Load .env manually (avoids dotenv frame issues)
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server={os.environ['SQL_SERVER']};"
    f"Database={os.environ['SQL_DATABASE']};"
    f"UID={os.environ['SQL_USERNAME']};"
    f"PWD={os.environ['SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=no;ApplicationIntent=ReadOnly;"
)

print(f"\n{'='*70}")
print(f"  Server:  {os.environ['SQL_SERVER']}")
print(f"  DB:      {os.environ['SQL_DATABASE']}")
print(f"  Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*70}")

conn = pyodbc.connect(conn_str)
c = conn.cursor()

# Core counts
c.execute("SELECT COUNT(*) FROM dbo.vw_ISDSolution_All")
total = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT orgName) FROM dbo.vw_ISDSolution_All WHERE orgName IS NOT NULL")
partners = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT industryName) FROM dbo.vw_ISDSolution_All WHERE industryName IS NOT NULL")
industries = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT solutionAreaName) FROM dbo.vw_ISDSolution_All WHERE solutionAreaName IS NOT NULL")
areas = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM dbo.vw_ISDSolution_All WHERE solutionName IS NULL OR solutionName = ''")
nullnames = c.fetchone()[0]

print(f"\n  Total solutions:        {total}")
print(f"  Unique partners:        {partners}")
print(f"  Unique industries:      {industries}")
print(f"  Unique solution areas:  {areas}")
print(f"  Null/empty names:       {nullnames}")

# Date columns
c.execute("""
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'vw_ISDSolution_All' AND TABLE_SCHEMA = 'dbo'
    AND (COLUMN_NAME LIKE '%date%' OR COLUMN_NAME LIKE '%update%'
         OR COLUMN_NAME LIKE '%creat%' OR COLUMN_NAME LIKE '%modif%')
""")
date_cols = [r[0] for r in c.fetchall()]
print(f"\n  Date/timestamp columns: {date_cols if date_cols else 'None found'}")
if date_cols:
    col = date_cols[0]
    c.execute(f"SELECT MIN([{col}]), MAX([{col}]) FROM dbo.vw_ISDSolution_All WHERE [{col}] IS NOT NULL")
    mn, mx = c.fetchone()
    print(f"    {col}: {mn} -> {mx}")

# View columns
print(f"\n{'─'*70}")
print("  VIEW COLUMNS")
print(f"{'─'*70}")
c.execute("""
    SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'vw_ISDSolution_All' AND TABLE_SCHEMA = 'dbo'
    ORDER BY ORDINAL_POSITION
""")
for row in c.fetchall():
    print(f"  {row[0]:<42} {row[1]}")

# Industry breakdown
print(f"\n{'─'*70}")
print("  SOLUTIONS BY INDUSTRY")
print(f"{'─'*70}")
c.execute("""
    SELECT industryName, COUNT(*) as cnt FROM dbo.vw_ISDSolution_All
    GROUP BY industryName ORDER BY cnt DESC
""")
for row in c.fetchall():
    name = str(row[0]) if row[0] else '(NULL)'
    print(f"  {name:<42} {row[1]}")

# Solution area breakdown
print(f"\n{'─'*70}")
print("  SOLUTIONS BY SOLUTION AREA")
print(f"{'─'*70}")
c.execute("""
    SELECT solutionAreaName, COUNT(*) as cnt FROM dbo.vw_ISDSolution_All
    GROUP BY solutionAreaName ORDER BY cnt DESC
""")
for row in c.fetchall():
    name = str(row[0]) if row[0] else '(NULL)'
    print(f"  {name:<42} {row[1]}")

# Top 15 partners
print(f"\n{'─'*70}")
print("  TOP 15 PARTNERS BY SOLUTION COUNT")
print(f"{'─'*70}")
c.execute("""
    SELECT TOP 15 orgName, COUNT(*) cnt FROM dbo.vw_ISDSolution_All
    WHERE orgName IS NOT NULL
    GROUP BY orgName ORDER BY cnt DESC
""")
for row in c.fetchall():
    print(f"  {str(row[0]):<42} {row[1]}")

conn.close()
print(f"\n{'='*70}\n")
