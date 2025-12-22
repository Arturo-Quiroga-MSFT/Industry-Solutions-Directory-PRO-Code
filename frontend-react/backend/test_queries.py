#!/usr/bin/env python3
"""
Quick validation script to test queries directly against the database
Tests: "Smart city solutions" and "Smart grid solutions"
"""

import pyodbc
import os
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Database configuration
SERVER = os.getenv('SQL_SERVER')
DATABASE = os.getenv('SQL_DATABASE')
USERNAME = os.getenv('SQL_USERNAME')
PASSWORD = os.getenv('SQL_PASSWORD')

def get_connection():
    """Create database connection"""
    conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    return pyodbc.connect(conn_str)

def test_query(query_name, sql_query):
    """Execute a test query and display results"""
    print(f"\n{'='*80}")
    print(f"TEST: {query_name}")
    print(f"{'='*80}")
    print(f"\nSQL:\n{sql_query}\n")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        count = len(rows)
        
        print(f"✓ RESULT: Found {count} results\n")
        
        if count > 0:
            # Convert to list of dicts for better display
            results = []
            for row in rows[:5]:  # Show first 5 results
                results.append([str(value)[:50] if value else '' for value in row])
            
            print(tabulate(results, headers=columns, tablefmt='grid'))
            
            if count > 5:
                print(f"\n... and {count - 5} more results")
        else:
            print("No results found.")
        
        cursor.close()
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return 0

def main():
    """Run validation tests"""
    print("\n" + "="*80)
    print("QUERY VALIDATION TEST")
    print("="*80)
    print(f"Server: {SERVER}")
    print(f"Database: {DATABASE}")
    
    # Test 1: Smart City Solutions
    smart_city_query = """
    SELECT DISTINCT 
        solutionName,
        orgName,
        industryName,
        solutionAreaName,
        marketPlaceLink,
        solutionDescription
    FROM dbo.vw_ISDSolution_All
    WHERE solutionStatus = 'Approved'
      AND (
        theme LIKE '%Smart City%' 
        OR subIndustryName LIKE '%Smart City%'
        OR solutionName LIKE '%Smart City%'
        OR solutionDescription LIKE '%Smart City%'
      )
    ORDER BY orgName, solutionName;
    """
    
    count1 = test_query("Smart City Solutions", smart_city_query)
    
    # Test 2: Smart Grid Solutions  
    smart_grid_query = """
    SELECT DISTINCT 
        solutionName,
        orgName,
        industryName,
        solutionAreaName,
        marketPlaceLink,
        solutionDescription
    FROM dbo.vw_ISDSolution_All
    WHERE solutionStatus = 'Approved'
      AND (
        solutionName LIKE '%smart grid%' 
        OR solutionDescription LIKE '%smart grid%'
      )
    ORDER BY orgName, solutionName;
    """
    
    count2 = test_query("Smart Grid Solutions", smart_grid_query)
    
    # Test 3: Let's check what columns are available
    schema_query = """
    SELECT TOP 1 * FROM dbo.vw_ISDSolution_All WHERE solutionStatus = 'Approved';
    """
    
    print(f"\n{'='*80}")
    print("SAMPLE RECORD (to see available data)")
    print(f"{'='*80}\n")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(schema_query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        if row:
            print("Available columns and sample data:")
            for col, val in zip(columns, row):
                val_str = str(val)[:100] if val else 'NULL'
                print(f"  {col}: {val_str}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Test 4: Check for "smart" in any text field
    smart_general_query = """
    SELECT COUNT(*) as total_count
    FROM dbo.vw_ISDSolution_All
    WHERE solutionStatus = 'Approved'
      AND (
        solutionName LIKE '%smart%'
        OR solutionDescription LIKE '%smart%'
        OR theme LIKE '%smart%'
        OR subIndustryName LIKE '%smart%'
        OR solutionAreaName LIKE '%smart%'
      );
    """
    
    print(f"\n{'='*80}")
    print("GENERAL 'SMART' COUNT (any field)")
    print(f"{'='*80}\n")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(smart_general_query)
        row = cursor.fetchone()
        total = row[0] if row else 0
        print(f"Total solutions with 'smart' anywhere: {total}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Smart City Solutions: {count1}")
    print(f"Smart Grid Solutions: {count2}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
