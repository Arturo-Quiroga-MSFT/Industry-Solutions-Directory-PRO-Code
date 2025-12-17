# SQL Direct Access - ISD Database

**Purpose**: Direct SQL Server access to the Industry Solutions Directory database as an alternative to API-based data ingestion.

**Status**: 🔬 Experimental - Testing alternative data retrieval approach

**Created**: December 17, 2025

---

## Overview

This module provides **direct database access** to the SQL Server database used by the ISD website (https://mssoldir-app-prd.azurewebsites.net). This approach offers:

✅ **Advantages**:
- Direct access to source data (no API rate limits)
- Real-time data retrieval
- Access to all database fields (not limited by API endpoints)
- Better performance for bulk operations
- Potential access to additional metadata not exposed via API

⚠️ **Considerations**:
- Requires database credentials and network access
- Must maintain security best practices
- Need to understand database schema
- Separate from current production API-based approach

---

## Architecture

```
┌─────────────────────────────────────┐
│   ISD SQL Server Database           │
│   (Azure SQL Database)              │
│                                     │
│   Tables:                           │
│   - Solutions                       │
│   - Partners                        │
│   - Industries                      │
│   - Technologies                    │
│   - Themes                          │
│   - SolutionAreas                   │
└──────────────┬──────────────────────┘
               │ SQL Connection
               │ (Managed Identity or SQL Auth)
               ▼
┌─────────────────────────────────────┐
│   Python SQL Client                 │
│   - pyodbc or pymssql               │
│   - Azure SQL connection            │
│   - Query builder                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Data Transformation               │
│   - Map to common schema            │
│   - Extract partner names           │
│   - Build search documents          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Azure AI Search Index             │
│   (Same as API approach)            │
└─────────────────────────────────────┘
```

---

## Prerequisites

### 1. Database Connection Information

You'll need:
- **Server**: SQL Server hostname (e.g., `isd-sql-server.database.windows.net`)
- **Database**: Database name (e.g., `isd-production-db`)
- **Authentication**: Either:
  - SQL Server authentication (username + password)
  - Azure AD authentication (Managed Identity or Service Principal)

### 2. Required Python Packages

```bash
# Install ODBC driver for SQL Server (macOS)
brew install unixodbc
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install mssql-tools18

# Install Python packages
pip install pyodbc
pip install azure-identity
pip install python-dotenv
```

### 3. Environment Variables

Create `.env` file in this directory:

```bash
# SQL Server Connection
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=your-database-name
SQL_USERNAME=your-username  # If using SQL auth
SQL_PASSWORD=your-password  # If using SQL auth

# Or use Azure AD authentication
USE_AZURE_AD_AUTH=true

# Azure AI Search (same as current setup)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_INDEX_NAME=partner-solutions-sql
```

---

## Files in this Module

```
sql-direct/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── sql_connector.py             # SQL connection manager
├── schema_inspector.py          # Inspect database schema
├── sql_data_fetcher.py          # Fetch data from SQL
├── sql_to_search_index.py       # Transform and index data
└── test_sql_connection.py       # Test SQL connectivity
```

---

## Quick Start

### Step 1: Set Up Environment

```bash
cd data-ingestion/sql-direct

# Copy environment template
cp .env.example .env

# Edit .env with your SQL Server credentials
nano .env

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Test SQL Connection

```bash
# Verify you can connect to the database
python test_sql_connection.py
```

Expected output:
```
✓ Successfully connected to SQL Server
✓ Database: isd-production-db
✓ Server version: 15.0.2000.5
✓ Available tables: Solutions, Partners, Industries, Technologies, ...
```

### Step 3: Inspect Database Schema

```bash
# Discover table structure and relationships
python schema_inspector.py

# This will generate:
# - schema_report.json (full schema details)
# - schema_diagram.md (ERD in markdown)
```

### Step 4: Fetch Data from SQL

```bash
# Fetch all solutions with related data
python sql_data_fetcher.py --output solutions_from_sql.json

# Options:
#   --limit N         # Fetch only N solutions (for testing)
#   --industry NAME   # Filter by industry
#   --modified-since DATE  # Only fetch recent updates
```

### Step 5: Index to Azure AI Search

```bash
# Transform SQL data and upload to search index
python sql_to_search_index.py --input solutions_from_sql.json

# This creates a NEW index: partner-solutions-sql
# (Keeps existing API-based index separate)
```

---

## Database Schema Discovery

Before fetching data, you need to understand the database structure. Run the schema inspector:

```bash
python schema_inspector.py
```

This will:
1. Connect to the SQL database
2. Discover all tables and columns
3. Identify primary keys and foreign keys
4. Find relationships between tables
5. Generate documentation

Example output:

```
Tables Found:
- dbo.Solutions (SolutionId, Name, Description, PartnerId, ...)
- dbo.Partners (PartnerId, PartnerName, Website, ...)
- dbo.Industries (IndustryId, IndustryName, ...)
- dbo.Technologies (TechnologyId, TechnologyName, ...)
- dbo.SolutionIndustries (SolutionId, IndustryId)
- dbo.SolutionTechnologies (SolutionId, TechnologyId)

Relationships:
- Solutions.PartnerId → Partners.PartnerId
- SolutionIndustries.SolutionId → Solutions.SolutionId
- SolutionIndustries.IndustryId → Industries.IndustryId
```

---

## Data Fetching Strategy

### Option 1: Simple JOIN Query

```sql
SELECT 
    s.SolutionId,
    s.Name AS SolutionName,
    s.Description,
    s.DetailedDescription,
    p.PartnerName,
    p.Website AS PartnerWebsite,
    STRING_AGG(i.IndustryName, ', ') AS Industries,
    STRING_AGG(t.TechnologyName, ', ') AS Technologies
FROM Solutions s
LEFT JOIN Partners p ON s.PartnerId = p.PartnerId
LEFT JOIN SolutionIndustries si ON s.SolutionId = si.SolutionId
LEFT JOIN Industries i ON si.IndustryId = i.IndustryId
LEFT JOIN SolutionTechnologies st ON s.SolutionId = st.SolutionId
LEFT JOIN Technologies t ON st.TechnologyId = t.TechnologyId
GROUP BY s.SolutionId, s.Name, s.Description, s.DetailedDescription, p.PartnerName, p.Website
```

### Option 2: Incremental Updates

```sql
-- Only fetch solutions modified since last run
SELECT * FROM Solutions
WHERE LastModifiedDate > @LastSyncDate
```

### Option 3: Hierarchical Fetching

```python
# 1. Fetch all solutions
solutions = fetch_all_solutions()

# 2. For each solution, fetch related data
for solution in solutions:
    industries = fetch_solution_industries(solution.id)
    technologies = fetch_solution_technologies(solution.id)
    partner = fetch_partner(solution.partner_id)
```

---

## Comparison: SQL vs API Approach

| Aspect | API Approach (Current) | SQL Direct Approach |
|--------|------------------------|---------------------|
| **Data Source** | REST API endpoints | Direct database |
| **Access** | Public API | Requires credentials |
| **Performance** | API rate limits | Direct query (faster) |
| **Data Freshness** | As returned by API | Real-time |
| **Fields Available** | API-exposed only | All database fields |
| **Network** | Internet accessible | May need VPN/firewall rules |
| **Maintenance** | No DB schema changes | Must adapt to schema changes |
| **Security** | API key | DB credentials (more sensitive) |

---

## Security Best Practices

### 1. Credential Management

✅ **DO**:
- Use Azure Key Vault for credentials
- Use Managed Identity when possible
- Rotate credentials regularly
- Use read-only database user
- Enable connection encryption (TLS 1.2+)

❌ **DON'T**:
- Commit credentials to Git
- Use admin/owner accounts
- Share credentials across environments
- Store passwords in plain text

### 2. Network Security

```bash
# Check if firewall rules allow your IP
# You may need to:
# 1. Add your IP to Azure SQL firewall rules
# 2. Use Azure VPN or Private Endpoint
# 3. Connect from Azure service (VM, Container App)
```

### 3. Connection String Best Practices

```python
# Use Azure AD authentication (preferred)
connection_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={server};"
    f"Database={database};"
    f"Authentication=ActiveDirectoryInteractive;"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)

# Or use SQL auth with encrypted connection
connection_string = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={server};"
    f"Database={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)
```

---

## Testing & Validation

### 1. Connection Test

```bash
python test_sql_connection.py
```

### 2. Data Comparison

Compare SQL data vs API data to ensure consistency:

```bash
python compare_sql_vs_api.py
```

This will:
- Fetch data from both sources
- Compare solution counts
- Identify differences
- Report any discrepancies

### 3. Performance Testing

```bash
# Measure query performance
python benchmark_sql_queries.py
```

---

## Migration Path

If SQL approach proves better than API:

### Phase 1: Parallel Testing (Current)
- ✅ Keep API-based ingestion running (production)
- 🔬 Test SQL-based ingestion separately
- 📊 Compare results and performance

### Phase 2: Validation
- Verify data completeness
- Test incremental updates
- Validate search quality
- Performance benchmarking

### Phase 3: Gradual Migration
- Run both approaches in parallel
- Route small % of traffic to SQL-based index
- Monitor and compare results

### Phase 4: Full Cutover (If successful)
- Switch production to SQL-based approach
- Deprecate API-based ingestion
- Update documentation

---

## Troubleshooting

### Connection Failed

```
Error: Unable to connect to SQL Server
```

**Possible causes**:
1. Firewall blocking connection → Add your IP to Azure SQL firewall
2. Wrong credentials → Verify username/password
3. Server name incorrect → Check Azure portal for exact server name
4. Database doesn't exist → Verify database name

### ODBC Driver Not Found

```
Error: [01000] [unixODBC][Driver Manager]Can't open lib 'ODBC Driver 18 for SQL Server'
```

**Solution** (macOS):
```bash
brew tap microsoft/mssql-release
brew update
brew install mssql-tools18
```

**Solution** (Ubuntu):
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Schema Differences

If database schema changes:
1. Re-run `schema_inspector.py` to discover new structure
2. Update SQL queries in `sql_data_fetcher.py`
3. Adjust transformation logic in `sql_to_search_index.py`

---

## Next Steps

1. ✅ **Get SQL credentials** from ISD team
2. ✅ **Test connection** using `test_sql_connection.py`
3. 📊 **Inspect schema** using `schema_inspector.py`
4. 🔍 **Fetch sample data** to understand structure
5. 🔄 **Transform data** to match search index schema
6. 🧪 **Compare** SQL vs API results
7. 📈 **Benchmark** performance
8. 🎯 **Decide** whether to migrate or keep API approach

---

## Support

For questions or issues:
- **Technical Lead**: Arturo Quiroga
- **Database Access**: Contact ISD team
- **Documentation**: See main [ARCHITECTURE.md](../../ARCHITECTURE.md)
