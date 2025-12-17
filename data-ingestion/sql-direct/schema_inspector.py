#!/usr/bin/env python3
"""
SQL Database Schema Inspector
Discovers and documents the structure of the ISD SQL Server database.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pyodbc
from typing import Dict, List, Tuple

# Load environment variables
load_dotenv()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class SchemaInspector:
    """Inspects SQL Server database schema."""
    
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
    
    def get_all_tables(self) -> List[Tuple]:
        """Get all tables in the database."""
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_table_columns(self, schema: str, table: str) -> List[Dict]:
        """Get all columns for a specific table."""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        self.cursor.execute(query, schema, table)
        
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'max_length': row[2],
                'nullable': row[3] == 'YES',
                'default': row[4]
            })
        return columns
    
    def get_primary_keys(self, schema: str, table: str) -> List[str]:
        """Get primary key columns for a table."""
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        self.cursor.execute(query, schema, table)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_foreign_keys(self, schema: str, table: str) -> List[Dict]:
        """Get foreign key relationships for a table."""
        query = """
        SELECT 
            fk.name AS FK_name,
            COL_NAME(fc.parent_object_id, fc.parent_column_id) AS FK_column,
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS Referenced_schema,
            OBJECT_NAME(fk.referenced_object_id) AS Referenced_table,
            COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS Referenced_column
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fc 
            ON fk.object_id = fc.constraint_object_id
        WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) = ? 
        AND OBJECT_NAME(fk.parent_object_id) = ?
        """
        self.cursor.execute(query, schema, table)
        
        foreign_keys = []
        for row in self.cursor.fetchall():
            foreign_keys.append({
                'fk_name': row[0],
                'column': row[1],
                'ref_schema': row[2],
                'ref_table': row[3],
                'ref_column': row[4]
            })
        return foreign_keys
    
    def get_row_count(self, schema: str, table: str) -> int:
        """Get row count for a table."""
        try:
            query = f"SELECT COUNT(*) FROM [{schema}].[{table}]"
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]
        except Exception as e:
            return -1
    
    def inspect_database(self) -> Dict:
        """Perform full database inspection."""
        print(f"{BLUE}Inspecting database schema...{RESET}\n")
        
        schema_info = {
            'database': os.getenv('SQL_DATABASE'),
            'server': os.getenv('SQL_SERVER'),
            'inspection_date': datetime.now().isoformat(),
            'tables': []
        }
        
        # Get all tables
        tables = self.get_all_tables()
        print(f"{GREEN}Found {len(tables)} tables{RESET}\n")
        
        # Inspect each table
        for schema, table, table_type in tables:
            print(f"📋 Inspecting {schema}.{table}...", end=' ')
            
            table_info = {
                'schema': schema,
                'name': table,
                'type': table_type,
                'columns': self.get_table_columns(schema, table),
                'primary_keys': self.get_primary_keys(schema, table),
                'foreign_keys': self.get_foreign_keys(schema, table),
                'row_count': self.get_row_count(schema, table)
            }
            
            schema_info['tables'].append(table_info)
            print(f"{GREEN}✓{RESET} ({table_info['row_count']:,} rows, {len(table_info['columns'])} columns)")
        
        return schema_info
    
    def generate_markdown_report(self, schema_info: Dict) -> str:
        """Generate a markdown report of the database schema."""
        md = []
        md.append(f"# Database Schema Report\n")
        md.append(f"**Database**: {schema_info['database']}\n")
        md.append(f"**Server**: {schema_info['server']}\n")
        md.append(f"**Inspection Date**: {schema_info['inspection_date']}\n")
        md.append(f"**Total Tables**: {len(schema_info['tables'])}\n")
        md.append("---\n\n")
        
        # Table of contents
        md.append("## Table of Contents\n\n")
        for table in schema_info['tables']:
            md.append(f"- [{table['schema']}.{table['name']}](#{table['schema']}-{table['name']})\n")
        md.append("\n---\n\n")
        
        # Detailed table information
        for table in schema_info['tables']:
            md.append(f"## {table['schema']}.{table['name']}\n\n")
            md.append(f"**Row Count**: {table['row_count']:,}\n\n")
            
            # Primary keys
            if table['primary_keys']:
                md.append(f"**Primary Keys**: {', '.join(table['primary_keys'])}\n\n")
            
            # Columns
            md.append("### Columns\n\n")
            md.append("| Column | Type | Nullable | Default |\n")
            md.append("|--------|------|----------|----------|\n")
            for col in table['columns']:
                pk_marker = "🔑 " if col['name'] in table['primary_keys'] else ""
                type_str = col['type']
                if col['max_length']:
                    type_str += f"({col['max_length']})"
                nullable = "Yes" if col['nullable'] else "No"
                default = col['default'] if col['default'] else "-"
                md.append(f"| {pk_marker}{col['name']} | {type_str} | {nullable} | {default} |\n")
            md.append("\n")
            
            # Foreign keys
            if table['foreign_keys']:
                md.append("### Foreign Keys\n\n")
                md.append("| Column | References |\n")
                md.append("|--------|------------|\n")
                for fk in table['foreign_keys']:
                    md.append(f"| {fk['column']} | {fk['ref_schema']}.{fk['ref_table']}.{fk['ref_column']} |\n")
                md.append("\n")
            
            md.append("---\n\n")
        
        return "".join(md)


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
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}ISD SQL Database Schema Inspector{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    try:
        # Get connection string
        conn_str = get_connection_string()
        
        # Create inspector
        inspector = SchemaInspector(conn_str)
        inspector.connect()
        
        # Inspect database
        schema_info = inspector.inspect_database()
        
        # Save JSON report
        json_file = 'schema_report.json'
        with open(json_file, 'w') as f:
            json.dump(schema_info, f, indent=2)
        print(f"\n{GREEN}✓ Saved JSON report: {json_file}{RESET}")
        
        # Generate markdown report
        markdown_report = inspector.generate_markdown_report(schema_info)
        md_file = 'schema_report.md'
        with open(md_file, 'w') as f:
            f.write(markdown_report)
        print(f"{GREEN}✓ Saved Markdown report: {md_file}{RESET}")
        
        # Summary
        print(f"\n{BLUE}Summary:{RESET}")
        print(f"  📋 Total tables: {len(schema_info['tables'])}")
        total_rows = sum(t['row_count'] for t in schema_info['tables'] if t['row_count'] > 0)
        print(f"  📊 Total rows: {total_rows:,}")
        
        # Disconnect
        inspector.disconnect()
        
        print(f"\n{GREEN}✓ Schema inspection completed successfully{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
    except Exception as e:
        print(f"\n{RED}✗ Error: {str(e)}{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
