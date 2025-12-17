#!/usr/bin/env python3
"""
Natural Language to SQL - Database Insights Explorer
Explore the ISD database with analytical queries.
"""

import os
import sys
from dotenv import load_dotenv
import pyodbc
import json

# Load environment variables
load_dotenv()

# Color codes
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def get_connection():
    """Get database connection."""
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
        f"ApplicationIntent=ReadOnly;"  # PRODUCTION SAFETY: Read-only mode
    )
    
    return pyodbc.connect(conn_str)


def run_query(query, description):
    """Run a query and display results."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{description}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        # Print header
        header = " | ".join(f"{col:20}" for col in columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(val)[:20]:20}" for val in row)
            print(row_str)
        
        print(f"\n{GREEN}✓ {len(rows)} rows returned{RESET}\n")
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        print(f"{YELLOW}Error: {str(e)}{RESET}\n")
        cursor.close()
        conn.close()
        return []


def main():
    """Run analytical queries."""
    
    print(f"{BLUE}ISD Database Insights Explorer{RESET}")
    print(f"{BLUE}Natural Language to SQL Analysis{RESET}\n")
    
    # Query 1: Top partners by solution count
    run_query("""
        SELECT TOP 10
            o.orgName AS PartnerName,
            COUNT(ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT i.industryName) AS IndustriesServed
        FROM dbo.organization o
        INNER JOIN dbo.partnerSolution ps ON o.orgId = ps.OrganizationId
        LEFT JOIN dbo.Industry i ON ps.IndustryId = i.industryId
        WHERE ps.IsPublished = 1
        GROUP BY o.orgName
        ORDER BY SolutionCount DESC
    """, "📊 Query 1: Top 10 Partners by Solution Count")
    
    # Query 2: Solutions by industry
    run_query("""
        SELECT 
            i.industryName AS Industry,
            COUNT(ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT o.orgName) AS UniquePartners
        FROM dbo.Industry i
        LEFT JOIN dbo.partnerSolution ps ON i.industryId = ps.IndustryId
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        WHERE ps.IsPublished = 1
        GROUP BY i.industryName
        ORDER BY SolutionCount DESC
    """, "🏢 Query 2: Solutions by Industry")
    
    # Query 3: Solutions by solution area (technology)
    run_query("""
        SELECT 
            sa.solutionAreaName AS TechnologyArea,
            COUNT(DISTINCT ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT o.orgName) AS UniquePartners
        FROM dbo.solutionArea sa
        LEFT JOIN dbo.partnerSolutionByArea psba ON sa.solutionAreaId = psba.solutionAreaId
        LEFT JOIN dbo.partnerSolution ps ON psba.partnerSolutionId = ps.partnerSolutionId
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        WHERE ps.IsPublished = 1
        GROUP BY sa.solutionAreaName
        ORDER BY SolutionCount DESC
    """, "💻 Query 3: Solutions by Technology Area")
    
    # Query 4: Most active sub-industries
    run_query("""
        SELECT TOP 10
            i.industryName AS Industry,
            si.subIndustryName AS SubIndustry,
            COUNT(ps.partnerSolutionId) AS SolutionCount
        FROM dbo.SubIndustry si
        INNER JOIN dbo.Industry i ON si.industryId = i.industryId
        LEFT JOIN dbo.partnerSolution ps ON si.subIndustryId = ps.SubIndustryId
        WHERE ps.IsPublished = 1
        GROUP BY i.industryName, si.subIndustryName
        ORDER BY SolutionCount DESC
    """, "🎯 Query 4: Top 10 Sub-Industries by Solution Count")
    
    # Query 5: Recent activity (last 30 days)
    run_query("""
        SELECT 
            CONVERT(DATE, ps.rowChangedDate) AS UpdateDate,
            COUNT(ps.partnerSolutionId) AS SolutionsUpdated,
            COUNT(DISTINCT o.orgName) AS PartnersActive
        FROM dbo.partnerSolution ps
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        WHERE ps.rowChangedDate >= DATEADD(DAY, -30, GETDATE())
        GROUP BY CONVERT(DATE, ps.rowChangedDate)
        ORDER BY UpdateDate DESC
    """, "📅 Query 5: Recent Activity (Last 30 Days)")
    
    # Query 6: Cross-industry partners (fixed - removed STRING_AGG for compatibility)
    run_query("""
        SELECT TOP 10
            o.orgName AS PartnerName,
            COUNT(DISTINCT i.industryName) AS IndustryCount,
            COUNT(ps.partnerSolutionId) AS TotalSolutions
        FROM dbo.organization o
        INNER JOIN dbo.partnerSolution ps ON o.orgId = ps.OrganizationId
        LEFT JOIN dbo.Industry i ON ps.IndustryId = i.industryId
        WHERE ps.IsPublished = 1
        GROUP BY o.orgName
        HAVING COUNT(DISTINCT i.industryName) > 1
        ORDER BY IndustryCount DESC, TotalSolutions DESC
    """, "🌐 Query 6: Cross-Industry Partners (Multi-Industry Solutions)")
    
    # Query 7: Solution distribution by publish status
    run_query("""
        SELECT 
            CASE 
                WHEN IsPublished = 1 THEN 'Published'
                WHEN IsPublished = 0 THEN 'Draft'
                ELSE 'Unknown'
            END AS Status,
            COUNT(*) AS SolutionCount,
            COUNT(DISTINCT OrganizationId) AS UniquePartners
        FROM dbo.partnerSolution
        GROUP BY IsPublished
        ORDER BY SolutionCount DESC
    """, "📝 Query 7: Solutions by Publish Status")
    
    # Query 8: Partners with marketplace links
    run_query("""
        SELECT 
            CASE 
                WHEN marketplaceLink IS NOT NULL AND marketplaceLink != '' THEN 'Has Marketplace Link'
                ELSE 'No Marketplace Link'
            END AS MarketplaceStatus,
            COUNT(*) AS SolutionCount,
            COUNT(DISTINCT OrganizationId) AS UniquePartners
        FROM dbo.partnerSolution
        WHERE IsPublished = 1
        GROUP BY CASE 
                WHEN marketplaceLink IS NOT NULL AND marketplaceLink != '' THEN 'Has Marketplace Link'
                ELSE 'No Marketplace Link'
            END
    """, "🛒 Query 8: Marketplace Link Coverage")
    
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}Analysis Complete!{RESET}")
    print(f"{GREEN}{'='*80}{RESET}\n")


if __name__ == "__main__":
    main()
