#!/usr/bin/env python3
"""
SQL Data Fetcher
Fetches solution data from the ISD SQL Server database.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pyodbc
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SQLDataFetcher:
    """Fetches solution data from SQL Server database."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = pyodbc.connect(self.connection_string)
        self.cursor = self.conn.cursor()
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def fetch_all_solutions(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch all solutions with related data using a comprehensive JOIN query.
        
        Args:
            limit: Maximum number of solutions to fetch (None = all)
        
        Returns:
            List of solution dictionaries
        """
        print(f"{BLUE}Fetching solutions from SQL database...{RESET}\n")
        
        # Build query with string aggregation for industries and technologies
        query = """
        SELECT 
            s.id AS SolutionId,
            s.name AS SolutionName,
            s.description AS Description,
            s.detailedDescription AS DetailedDescription,
            s.url AS SolutionUrl,
            s.partnerName AS PartnerName,
            s.partnerWebsite AS PartnerWebsite,
            s.createdDate AS CreatedDate,
            s.modifiedDate AS ModifiedDate,
            -- Aggregate industries (may need adjustment based on actual schema)
            STRING_AGG(DISTINCT i.name, ', ') WITHIN GROUP (ORDER BY i.name) AS Industries,
            -- Aggregate technologies
            STRING_AGG(DISTINCT t.name, ', ') WITHIN GROUP (ORDER BY t.name) AS Technologies
        FROM dbo.partnerSolutions s
        LEFT JOIN dbo.partnerSolutionIndustry si ON s.id = si.partnerSolutionId
        LEFT JOIN dbo.industry i ON si.industryId = i.id
        LEFT JOIN dbo.partnerSolutionTechnology st ON s.id = st.partnerSolutionId
        LEFT JOIN dbo.technology t ON st.technologyId = t.id
        GROUP BY 
            s.id, s.name, s.description, s.detailedDescription, 
            s.url, s.partnerName, s.partnerWebsite, 
            s.createdDate, s.modifiedDate
        ORDER BY s.modifiedDate DESC
        """
        
        if limit:
            query = f"SELECT TOP {limit} * FROM ({query}) AS limited_results"
        
        try:
            self.cursor.execute(query)
            columns = [column[0] for column in self.cursor.description]
            
            solutions = []
            for row in self.cursor.fetchall():
                solution = dict(zip(columns, row))
                
                # Convert dates to ISO format
                if solution.get('CreatedDate'):
                    solution['CreatedDate'] = solution['CreatedDate'].isoformat()
                if solution.get('ModifiedDate'):
                    solution['ModifiedDate'] = solution['ModifiedDate'].isoformat()
                
                # Convert comma-separated strings to lists
                if solution.get('Industries'):
                    solution['Industries'] = [i.strip() for i in solution['Industries'].split(',')]
                else:
                    solution['Industries'] = []
                
                if solution.get('Technologies'):
                    solution['Technologies'] = [t.strip() for t in solution['Technologies'].split(',')]
                else:
                    solution['Technologies'] = []
                
                solutions.append(solution)
            
            print(f"{GREEN}✓ Fetched {len(solutions)} solutions{RESET}\n")
            return solutions
            
        except pyodbc.Error as e:
            print(f"{RED}✗ SQL Error: {str(e)}{RESET}")
            print(f"\n{YELLOW}Note: The query assumes standard table/column names.{RESET}")
            print(f"{YELLOW}Run schema_inspector.py first to see actual schema.{RESET}\n")
            raise
    
    def fetch_solutions_since(self, since_date: str) -> List[Dict]:
        """
        Fetch solutions modified since a specific date.
        
        Args:
            since_date: ISO format date string (e.g., "2024-01-01")
        
        Returns:
            List of solution dictionaries
        """
        print(f"{BLUE}Fetching solutions modified since {since_date}...{RESET}\n")
        
        query = """
        SELECT 
            s.id AS SolutionId,
            s.name AS SolutionName,
            s.description AS Description,
            s.detailedDescription AS DetailedDescription,
            s.url AS SolutionUrl,
            s.partnerName AS PartnerName,
            s.modifiedDate AS ModifiedDate
        FROM dbo.partnerSolutions s
        WHERE s.modifiedDate > ?
        ORDER BY s.modifiedDate DESC
        """
        
        try:
            self.cursor.execute(query, since_date)
            columns = [column[0] for column in self.cursor.description]
            
            solutions = []
            for row in self.cursor.fetchall():
                solution = dict(zip(columns, row))
                if solution.get('ModifiedDate'):
                    solution['ModifiedDate'] = solution['ModifiedDate'].isoformat()
                solutions.append(solution)
            
            print(f"{GREEN}✓ Fetched {len(solutions)} modified solutions{RESET}\n")
            return solutions
            
        except pyodbc.Error as e:
            print(f"{RED}✗ SQL Error: {str(e)}{RESET}\n")
            raise
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        stats = {}
        
        # Count solutions
        try:
            self.cursor.execute("SELECT COUNT(*) FROM dbo.partnerSolutions")
            stats['total_solutions'] = self.cursor.fetchone()[0]
        except:
            stats['total_solutions'] = 0
        
        # Count industries
        try:
            self.cursor.execute("SELECT COUNT(*) FROM dbo.industry")
            stats['total_industries'] = self.cursor.fetchone()[0]
        except:
            stats['total_industries'] = 0
        
        # Count technologies
        try:
            self.cursor.execute("SELECT COUNT(*) FROM dbo.technology")
            stats['total_technologies'] = self.cursor.fetchone()[0]
        except:
            stats['total_technologies'] = 0
        
        # Count unique partners
        try:
            self.cursor.execute("SELECT COUNT(DISTINCT partnerName) FROM dbo.partnerSolutions WHERE partnerName IS NOT NULL")
            stats['unique_partners'] = self.cursor.fetchone()[0]
        except:
            stats['unique_partners'] = 0
        
        return stats


def get_connection_string():
    """Build connection string from environment variables."""
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    use_azure_ad = os.getenv('USE_AZURE_AD_AUTH', 'false').lower() == 'true'
    
    if not server or not database:
        raise ValueError("SQL_SERVER and SQL_DATABASE must be set in .env file")
    
    driver = '{ODBC Driver 18 for SQL Server}'
    
    if use_azure_ad:
        return (
            f"Driver={driver};"
            f"Server={server};"
            f"Database={database};"
            f"Authentication=ActiveDirectoryInteractive;"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
    else:
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        
        if not username or not password:
            raise ValueError("SQL_USERNAME and SQL_PASSWORD required for SQL auth")
        
        return (
            f"Driver={driver};"
            f"Server={server};"
            f"Database={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Fetch solution data from ISD SQL database')
    parser.add_argument('--output', default='solutions_from_sql.json', help='Output JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of solutions to fetch')
    parser.add_argument('--since', help='Fetch only solutions modified since this date (ISO format)')
    parser.add_argument('--stats-only', action='store_true', help='Only display statistics')
    
    args = parser.parse_args()
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}ISD SQL Data Fetcher{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    try:
        # Get connection string
        conn_str = get_connection_string()
        
        # Create fetcher
        fetcher = SQLDataFetcher(conn_str)
        fetcher.connect()
        
        # Get statistics
        stats = fetcher.get_statistics()
        print(f"{BLUE}Database Statistics:{RESET}")
        print(f"  📊 Total solutions: {stats.get('total_solutions', 0):,}")
        print(f"  🏭 Unique partners: {stats.get('unique_partners', 0):,}")
        print(f"  🏢 Industries: {stats.get('total_industries', 0):,}")
        print(f"  💻 Technologies: {stats.get('total_technologies', 0):,}\n")
        
        if args.stats_only:
            fetcher.disconnect()
            return
        
        # Fetch solutions
        if args.since:
            solutions = fetcher.fetch_solutions_since(args.since)
        else:
            solutions = fetcher.fetch_all_solutions(limit=args.limit)
        
        # Save to file
        output_data = {
            'metadata': {
                'fetch_date': datetime.now().isoformat(),
                'source': 'sql_direct',
                'database': os.getenv('SQL_DATABASE'),
                'total_solutions': len(solutions),
                'statistics': stats
            },
            'solutions': solutions
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"{GREEN}✓ Saved solutions to: {args.output}{RESET}")
        print(f"{GREEN}✓ Total solutions: {len(solutions)}{RESET}")
        
        # Sample preview
        if solutions:
            print(f"\n{BLUE}Sample Solution:{RESET}")
            sample = solutions[0]
            print(f"  Name: {sample.get('SolutionName', 'N/A')}")
            print(f"  Partner: {sample.get('PartnerName', 'N/A')}")
            print(f"  Industries: {', '.join(sample.get('Industries', []))[:60]}...")
            print(f"  Technologies: {', '.join(sample.get('Technologies', []))[:60]}...")
        
        # Disconnect
        fetcher.disconnect()
        
        print(f"\n{GREEN}✓ Data fetch completed successfully{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
    except Exception as e:
        print(f"\n{RED}✗ Error: {str(e)}{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
