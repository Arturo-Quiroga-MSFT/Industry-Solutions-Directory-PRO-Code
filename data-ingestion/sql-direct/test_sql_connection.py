#!/usr/bin/env python3
"""
Test SQL Server Connection
Tests connectivity to the ISD SQL Server database and displays basic information.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pyodbc
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_connection_string():
    """Build SQL Server connection string based on environment variables."""
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    use_azure_ad = os.getenv('USE_AZURE_AD_AUTH', 'false').lower() == 'true'
    
    if not server or not database:
        raise ValueError("SQL_SERVER and SQL_DATABASE must be set in .env file")
    
    # Base connection string
    driver = '{ODBC Driver 18 for SQL Server}'
    encrypt = os.getenv('SQL_ENCRYPT', 'yes')
    trust_cert = os.getenv('SQL_TRUST_SERVER_CERTIFICATE', 'no')
    timeout = os.getenv('SQL_CONNECTION_TIMEOUT', '30')
    
    if use_azure_ad:
        # Azure AD authentication
        print(f"{BLUE}Using Azure AD authentication{RESET}")
        conn_str = (
            f"Driver={driver};"
            f"Server={server};"
            f"Database={database};"
            f"Authentication=ActiveDirectoryInteractive;"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust_cert};"
            f"Connection Timeout={timeout};"
        )
    else:
        # SQL Server authentication
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        
        if not username or not password:
            raise ValueError("SQL_USERNAME and SQL_PASSWORD must be set for SQL auth")
        
        print(f"{BLUE}Using SQL Server authentication{RESET}")
        conn_str = (
            f"Driver={driver};"
            f"Server={server};"
            f"Database={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust_cert};"
            f"Connection Timeout={timeout};"
        )
    
    return conn_str


def test_connection():
    """Test the SQL Server connection and display server information."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}ISD SQL Server Connection Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    try:
        # Get connection string
        conn_str = get_connection_string()
        
        # Attempt connection
        print(f"Connecting to: {os.getenv('SQL_SERVER')}")
        print(f"Database: {os.getenv('SQL_DATABASE')}\n")
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print(f"{GREEN}✓ Successfully connected to SQL Server{RESET}\n")
        
        # Get server version
        try:
            cursor.execute("SELECT @@VERSION AS version")
            version = cursor.fetchone()[0]
            print(f"{BLUE}Server Version:{RESET}")
            # Parse version more safely
            if 'Microsoft SQL Server' in version:
                # Extract just the version number
                version_parts = version.split('\n')
                print(f"  {version_parts[0].strip()}\n")
            else:
                print(f"  {version[:100]}\n")
        except Exception as e:
            print(f"{YELLOW}⚠ Could not retrieve version info{RESET}\n")
        
        # Get database name
        cursor.execute("SELECT DB_NAME() AS database_name")
        db_name = cursor.fetchone()[0]
        print(f"{GREEN}✓ Connected to database: {db_name}{RESET}\n")
        
        # List all tables
        print(f"{BLUE}Available Tables:{RESET}")
        cursor.execute("""
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        if tables:
            for schema, table, table_type in tables:
                icon = "📋" if table_type == "BASE TABLE" else "👁"
                print(f"  {icon} {schema}.{table} ({table_type})")
            print(f"\n{GREEN}✓ Found {len(tables)} tables/views{RESET}")
        else:
            print(f"{YELLOW}⚠ No tables found{RESET}")
        
        # Get row counts for main tables (if they exist)
        print(f"\n{BLUE}Table Row Counts:{RESET}")
        common_tables = [
            'Solutions', 'Partners', 'Industries', 'Technologies',
            'SolutionIndustries', 'SolutionTechnologies', 'Themes'
        ]
        
        for table in common_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM dbo.{table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count:,} rows")
            except pyodbc.Error:
                # Table doesn't exist, skip
                pass
        
        # Close connection
        cursor.close()
        conn.close()
        
        print(f"\n{GREEN}✓ Connection test completed successfully{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        return True
        
    except pyodbc.Error as e:
        print(f"\n{RED}✗ Database error:{RESET}")
        print(f"{RED}{str(e)}{RESET}\n")
        
        # Provide troubleshooting hints
        print(f"{YELLOW}Troubleshooting:{RESET}")
        print(f"  1. Verify SQL_SERVER and SQL_DATABASE in .env")
        print(f"  2. Check firewall rules allow your IP address")
        print(f"  3. Verify credentials are correct")
        print(f"  4. Ensure ODBC Driver 18 is installed:")
        print(f"     macOS: brew install mssql-tools18")
        print(f"     Linux: See README.md for instructions\n")
        
        return False
        
    except Exception as e:
        print(f"\n{RED}✗ Unexpected error:{RESET}")
        print(f"{RED}{str(e)}{RESET}\n")
        return False


def check_odbc_drivers():
    """List available ODBC drivers."""
    print(f"{BLUE}Available ODBC Drivers:{RESET}")
    drivers = [driver for driver in pyodbc.drivers()]
    if drivers:
        for driver in drivers:
            marker = "✓" if "SQL Server" in driver else " "
            print(f"  {marker} {driver}")
        
        # Check for required driver
        has_driver = any("SQL Server" in d for d in drivers)
        if has_driver:
            print(f"\n{GREEN}✓ SQL Server ODBC driver found{RESET}")
        else:
            print(f"\n{RED}✗ No SQL Server ODBC driver found{RESET}")
            print(f"{YELLOW}Install: brew install mssql-tools18 (macOS){RESET}\n")
        
        return has_driver
    else:
        print(f"{RED}  No ODBC drivers found{RESET}\n")
        return False


if __name__ == "__main__":
    print(f"\n{BLUE}Step 1: Checking ODBC drivers...{RESET}\n")
    has_driver = check_odbc_drivers()
    
    if not has_driver:
        print(f"\n{RED}Please install ODBC Driver 18 for SQL Server first.{RESET}")
        sys.exit(1)
    
    print(f"\n{BLUE}Step 2: Testing SQL Server connection...{RESET}\n")
    success = test_connection()
    
    sys.exit(0 if success else 1)
