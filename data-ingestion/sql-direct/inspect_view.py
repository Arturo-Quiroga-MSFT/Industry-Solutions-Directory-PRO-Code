#!/usr/bin/env python3
"""
Inspect the new vw_ISDSolution_All view structure
"""

import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

# Colors
GREEN = '\033[92m'
BLUE = '\033[94m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_connection():
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"ApplicationIntent=ReadOnly;"
    )
    
    return pyodbc.connect(conn_str)

print(f"\n{BLUE}{'='*80}{RESET}")
print(f"{BLUE}Inspecting View: dbo.vw_ISDSolution_All{RESET}")
print(f"{BLUE}{'='*80}{RESET}\n")

conn = get_connection()
cursor = conn.cursor()

# Get view columns
print(f"{CYAN}View Structure:{RESET}\n")
cursor.execute("""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'vw_ISDSolution_All'
        AND TABLE_SCHEMA = 'dbo'
    ORDER BY ORDINAL_POSITION
""")

columns_info = cursor.fetchall()
print(f"{'Column Name':<40} {'Type':<20} {'Max Length':<12} {'Nullable':<10}")
print("-" * 85)
for col in columns_info:
    col_name, data_type, max_len, nullable = col
    max_len_str = str(max_len) if max_len else 'N/A'
    print(f"{col_name:<40} {data_type:<20} {max_len_str:<12} {nullable:<10}")

# Get sample data
print(f"\n{CYAN}Sample Data (first 5 rows):{RESET}\n")
cursor.execute("SELECT TOP 5 * FROM dbo.vw_ISDSolution_All")

columns = [column[0] for column in cursor.description]
rows = cursor.fetchall()

# Display sample
for row in rows:
    print(f"{GREEN}Row:{RESET}")
    for col, val in zip(columns, row):
        if val is not None:
            val_str = str(val)[:100]  # Truncate long values
            print(f"  {col:<30}: {val_str}")
    print()

# Get row count
cursor.execute("SELECT COUNT(*) FROM dbo.vw_ISDSolution_All")
count = cursor.fetchone()[0]
print(f"\n{GREEN}Total rows in view: {count}{RESET}\n")

cursor.close()
conn.close()

print(f"{BLUE}{'='*80}{RESET}")
print(f"{GREEN}✓ View inspection complete!{RESET}")
print(f"{BLUE}{'='*80}{RESET}\n")
