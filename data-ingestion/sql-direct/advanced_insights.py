#!/usr/bin/env python3
"""
Advanced Analytics - Deeper Insights
Follow-up queries for more specific insights.
"""

import os
import sys
from dotenv import load_dotenv
import pyodbc

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
        header = " | ".join(f"{col:25}" for col in columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(val)[:25]:25}" for val in row)
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
    """Run advanced analytical queries."""
    
    print(f"{BLUE}ISD Database - Advanced Analytics{RESET}")
    print(f"{BLUE}Deeper Insights and Trends{RESET}\n")
    
    # Query 1: Healthcare AI solutions
    run_query("""
        SELECT TOP 10
            ps.solutionName,
            o.orgName AS PartnerName,
            si.subIndustryName,
            sa.solutionAreaName AS Technology
        FROM dbo.partnerSolution ps
        INNER JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        INNER JOIN dbo.Industry i ON ps.IndustryId = i.industryId
        LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE i.industryName = 'Healthcare & Life Sciences'
        AND sa.solutionAreaName = 'AI Business Solutions'
        AND ps.IsPublished = 1
        ORDER BY ps.rowChangedDate DESC
    """, "🏥 Query 1: Healthcare AI Solutions (Recent)")
    
    # Query 2: Financial Services Security solutions
    run_query("""
        SELECT TOP 10
            ps.solutionName,
            o.orgName AS PartnerName,
            si.subIndustryName
        FROM dbo.partnerSolution ps
        INNER JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        INNER JOIN dbo.Industry i ON ps.IndustryId = i.industryId
        LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE i.industryName = 'Financial Services'
        AND sa.solutionAreaName = 'Security'
        AND ps.IsPublished = 1
        ORDER BY ps.rowChangedDate DESC
    """, "💰 Query 2: Financial Services Security Solutions")
    
    # Query 3: Manufacturing Cloud & AI solutions
    run_query("""
        SELECT TOP 10
            ps.solutionName,
            o.orgName AS PartnerName,
            si.subIndustryName
        FROM dbo.partnerSolution ps
        INNER JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        INNER JOIN dbo.Industry i ON ps.IndustryId = i.industryId
        LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE i.industryName = 'Manufacturing & Mobility'
        AND sa.solutionAreaName = 'Cloud and AI Platforms'
        AND ps.IsPublished = 1
        ORDER BY ps.rowChangedDate DESC
    """, "🏭 Query 3: Manufacturing Cloud & AI Solutions")
    
    # Query 4: Partners serving multiple technology areas
    run_query("""
        SELECT TOP 10
            o.orgName AS PartnerName,
            COUNT(DISTINCT sa.solutionAreaName) AS TechAreasServed,
            COUNT(DISTINCT ps.partnerSolutionId) AS TotalSolutions
        FROM dbo.organization o
        INNER JOIN dbo.partnerSolution ps ON o.orgId = ps.OrganizationId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE ps.IsPublished = 1
        GROUP BY o.orgName
        HAVING COUNT(DISTINCT sa.solutionAreaName) > 1
        ORDER BY TechAreasServed DESC, TotalSolutions DESC
    """, "🔧 Query 4: Multi-Technology Partners")
    
    # Query 5: Industry + Technology combinations
    run_query("""
        SELECT 
            i.industryName AS Industry,
            sa.solutionAreaName AS Technology,
            COUNT(DISTINCT ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT o.orgName) AS PartnerCount
        FROM dbo.Industry i
        LEFT JOIN dbo.partnerSolution ps ON i.industryId = ps.IndustryId
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE ps.IsPublished = 1
        GROUP BY i.industryName, sa.solutionAreaName
        HAVING COUNT(DISTINCT ps.partnerSolutionId) > 10
        ORDER BY SolutionCount DESC
    """, "🎯 Query 5: Industry × Technology Matrix (>10 solutions)")
    
    # Query 6: Solutions with special offers
    run_query("""
        SELECT 
            CASE 
                WHEN specialOfferLink IS NOT NULL AND specialOfferLink != '' THEN 'Has Special Offer'
                ELSE 'No Special Offer'
            END AS OfferStatus,
            COUNT(*) AS SolutionCount,
            COUNT(DISTINCT OrganizationId) AS PartnerCount
        FROM dbo.partnerSolution
        WHERE IsPublished = 1
        GROUP BY CASE 
                WHEN specialOfferLink IS NOT NULL AND specialOfferLink != '' THEN 'Has Special Offer'
                ELSE 'No Special Offer'
            END
    """, "🎁 Query 6: Special Offer Availability")
    
    # Query 7: Sub-industry distribution within top industries
    run_query("""
        SELECT TOP 15
            i.industryName AS Industry,
            si.subIndustryName AS SubIndustry,
            COUNT(ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT o.orgName) AS PartnerCount
        FROM dbo.Industry i
        INNER JOIN dbo.SubIndustry si ON i.industryId = si.industryId
        LEFT JOIN dbo.partnerSolution ps ON si.subIndustryId = ps.SubIndustryId
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        WHERE ps.IsPublished = 1
        AND i.industryName IN ('Financial Services', 'Healthcare & Life Sciences', 'Retail & Consumer Goods')
        GROUP BY i.industryName, si.subIndustryName
        ORDER BY i.industryName, SolutionCount DESC
    """, "📊 Query 7: Top Industries - Sub-Industry Breakdown")
    
    # Query 8: Solution freshness (by creation date)
    run_query("""
        SELECT 
            AgeGroup,
            COUNT(*) AS SolutionCount
        FROM (
            SELECT 
                CASE 
                    WHEN rowCreatedDate >= DATEADD(MONTH, -3, GETDATE()) THEN '< 3 months'
                    WHEN rowCreatedDate >= DATEADD(MONTH, -6, GETDATE()) THEN '3-6 months'
                    WHEN rowCreatedDate >= DATEADD(YEAR, -1, GETDATE()) THEN '6-12 months'
                    ELSE '> 1 year'
                END AS AgeGroup,
                rowCreatedDate
            FROM dbo.partnerSolution
            WHERE IsPublished = 1
        ) AS AgeData
        GROUP BY AgeGroup
        ORDER BY 
            CASE 
                WHEN AgeGroup = '< 3 months' THEN 1
                WHEN AgeGroup = '3-6 months' THEN 2
                WHEN AgeGroup = '6-12 months' THEN 3
                ELSE 4
            END
    """, "📅 Query 8: Solution Age Distribution")
    
    # Query 9: Education sector deep dive
    run_query("""
        SELECT 
            si.subIndustryName AS SubIndustry,
            sa.solutionAreaName AS Technology,
            COUNT(DISTINCT ps.partnerSolutionId) AS SolutionCount,
            COUNT(DISTINCT o.orgName) AS PartnerCount
        FROM dbo.Industry i
        INNER JOIN dbo.partnerSolution ps ON i.industryId = ps.IndustryId
        LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
        LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
        LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
        LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId
        WHERE i.industryName = 'Education'
        AND ps.IsPublished = 1
        GROUP BY si.subIndustryName, sa.solutionAreaName
        ORDER BY SolutionCount DESC
    """, "🎓 Query 9: Education Sector - Sub-Industry × Technology")
    
    # Query 10: Partner concentration (top partners' market share)
    run_query("""
        WITH PartnerCounts AS (
            SELECT 
                o.orgName,
                COUNT(ps.partnerSolutionId) AS SolutionCount
            FROM dbo.organization o
            INNER JOIN dbo.partnerSolution ps ON o.orgId = ps.OrganizationId
            WHERE ps.IsPublished = 1
            GROUP BY o.orgName
        ),
        TotalSolutions AS (
            SELECT COUNT(*) AS Total FROM dbo.partnerSolution WHERE IsPublished = 1
        )
        SELECT TOP 20
            pc.orgName AS PartnerName,
            pc.SolutionCount,
            CAST(ROUND((pc.SolutionCount * 100.0 / ts.Total), 2) AS DECIMAL(5,2)) AS MarketSharePercent
        FROM PartnerCounts pc
        CROSS JOIN TotalSolutions ts
        ORDER BY pc.SolutionCount DESC
    """, "📈 Query 10: Top 20 Partners by Market Share")
    
    print(f"\n{GREEN}{'='*80}{RESET}")
    print(f"{GREEN}Advanced Analysis Complete!{RESET}")
    print(f"{GREEN}{'='*80}{RESET}\n")


if __name__ == "__main__":
    main()
