# ISD SQL Database Discovery Results

**Date**: December 17, 2025  
**Database**: mssoldir-prd  
**Server**: mssoldir-prd-sql.database.windows.net  
**Connection**: ✅ Successful

---

## Executive Summary

Successfully connected to the ISD production SQL Server database and discovered the complete schema structure. The database contains **540 partner solutions** from **336 organizations** across **10 industries** and **40 sub-industries**.

### Key Findings

✅ **Direct SQL access provides:**
- Real-time access to all 540 solutions (vs 535 from API)
- Complete field access including HTML-formatted descriptions
- Organization names directly (vs parsing from titles in API)
- Detailed relationship data (industries, sub-industries, solution areas)
- Change tracking (rowChangedDate for incremental updates)

---

## Database Statistics

| Entity | Count |
|--------|-------|
| **Partner Solutions** | 540 |
| **Organizations** | 336 |
| **Industries** | 10 |
| **Sub-Industries** | 40 |
| **Industry Themes** | 35 |
| **Solution Areas** | 3 |

---

## Database Schema Overview

### Primary Tables

#### 1. `dbo.partnerSolution` (540 rows)
Main table containing all partner solutions.

**Key Columns:**
- `partnerSolutionId` (uniqueidentifier, PK)
- `solutionName` (varchar(8000))
- `solutionDescription` (varchar(MAX)) - HTML formatted
- `OrganizationId` (uniqueidentifier, FK)
- `IndustryId` (uniqueidentifier, FK)
- `SubIndustryId` (uniqueidentifier, FK)
- `solutionOrgWebsite` (nvarchar(500))
- `marketplaceLink` (varchar(1000))
- `specialOfferLink` (varchar(1000))
- `logoFileLink` (varchar(MAX))
- `IsPublished` (int) - 1 = published, 0 = draft
- `rowChangedDate` (datetime) - for incremental updates
- `rowCreatedDate` (datetime)
- `partnerSolutionSlug` (varchar(500)) - URL slug
- `IndustryDesignation` (int)

#### 2. `dbo.organization` (336 rows)
Partner/organization information.

**Key Columns:**
- `orgId` (uniqueidentifier, PK)
- `orgName` (varchar(500)) - **This is the partner name!**
- `orgDescription` (varchar)
- `orgWebsite` (varchar)
- `logoFileLink` (varchar)
- `status` (varchar)
- `UserType` (varchar)
- `rowChangedDate` (datetime)

#### 3. `dbo.Industry` (10 rows)
Top-level industries (e.g., Financial Services, Healthcare, Manufacturing).

**Key Columns:**
- `industryId` (uniqueidentifier, PK)
- `industryName` (varchar(100))
- `industryDescription` (varchar)
- `industryDesignation` (int)

#### 4. `dbo.SubIndustry` (40 rows)
Sub-industries within each industry.

**Key Columns:**
- `subIndustryId` (uniqueidentifier, PK)
- `subIndustryName` (varchar(100))
- `industryId` (uniqueidentifier, FK)

#### 5. `dbo.solutionArea` (3 rows)
Solution area categories (technologies/capabilities).

**Key Columns:**
- `solutionAreaId` (uniqueidentifier, PK)
- `solutionAreaName` (varchar(100))

**Observed Values:**
- AI Business Solutions
- Cloud and AI Platforms
- Security (likely third value)

#### 6. `dbo.IndustryTheme` (35 rows)
Industry themes that group solutions.

**Key Columns:**
- `industryThemeId` (uniqueidentifier, PK)
- `themeName` (varchar)
- `industryId` (uniqueidentifier, FK)

#### 7. `dbo.partnerSolutionByArea`
Junction table linking solutions to solution areas (M:N relationship).

**Key Columns:**
- `partnerSolutionId` (uniqueidentifier, FK)
- `solutionAreaId` (uniqueidentifier, FK)

### Additional Tables

- `dbo.IndustryShowcasePartnerSolution` - Featured/showcase solutions
- `dbo.IndustryThemeBySolutionArea` - Theme to solution area relationships
- `dbo.partnerSolutionResourceLink` - Resource links for solutions
- `dbo.PartnerSolutionAvailableGeo` - Geographic availability
- `dbo.geo` - Geographic regions
- `dbo.partnerSolutionPlay` - Solution plays/offerings
- `dbo.resourceLink` - General resource links
- `dbo.Spotlight` - Spotlight featured items
- `stage.*` - Staging tables (33 tables) for data import/updates

---

## Sample Data

### Recent Solutions

1. **Seismic Enablement Cloud for Manufacturing**
   - Partner: Seismic
   - Industry: Manufacturing & Mobility
   - Sub-Industry: Connected Customer Experiences
   - Solution Area: AI Business Solutions
   - Last Modified: 2025-12-12

2. **Seismic Enablement Cloud for Financial Services**
   - Partner: Seismic
   - Industry: Financial Services
   - Sub-Industry: Empowering Employees and Agents
   - Solution Area: AI Business Solutions
   - Last Modified: 2025-12-12

3. **Epic and EHR Services by UST**
   - Partner: UST Global Inc
   - Industry: Healthcare & Life Sciences
   - Sub-Industry: Electronic Health Records
   - Solution Area: Cloud and AI Platforms
   - Last Modified: 2025-12-12

4. **OpenText™ Content Management**
   - Partner: OpenText
   - Last Modified: 2025-12-10

---

## Relationships & Data Model

```
organization (336)
    ↓ 1:N
partnerSolution (540)
    ↓ N:1          ↓ N:1              ↓ N:M
Industry (10)  SubIndustry (40)  solutionArea (3)
                                      ↑
                            partnerSolutionByArea
```

### Key Relationships

1. **Solution → Organization**: Each solution belongs to ONE organization
   - `partnerSolution.OrganizationId → organization.orgId`

2. **Solution → Industry**: Each solution has ONE primary industry
   - `partnerSolution.IndustryId → Industry.industryId`

3. **Solution → SubIndustry**: Each solution has ONE primary sub-industry
   - `partnerSolution.SubIndustryId → SubIndustry.subIndustryId`

4. **Solution → SolutionArea**: Each solution can have MULTIPLE solution areas (M:N)
   - Through `partnerSolutionByArea` junction table

---

## Key Advantages vs API Approach

### ✅ Data Completeness
- **SQL**: 540 solutions
- **API**: 535 solutions (5 missing!)

### ✅ Partner Names
- **SQL**: Direct `orgName` field from organization table
- **API**: Must parse from solution title (error-prone)

### ✅ HTML Descriptions
- **SQL**: Full HTML content in `solutionDescription`
- **API**: May return cleaned/truncated text

### ✅ Relationships
- **SQL**: Native FK relationships, easy JOINs
- **API**: Nested JSON, requires parsing

### ✅ Incremental Updates
- **SQL**: Use `rowChangedDate` to fetch only modified solutions
- **API**: Must compare MD5 hashes of all solutions

### ✅ Additional Fields
- **SQL**: Access to:
  - `marketplaceLink`
  - `specialOfferLink`
  - `logoFileLink`
  - `partnerSolutionSlug`
  - `IndustryDesignation`
  - `rowCreatedDate`, `rowChangedDate`
- **API**: Limited field exposure

---

## Recommended SQL Query for Data Extraction

```sql
-- Comprehensive solution extraction with all relationships
SELECT 
    ps.partnerSolutionId,
    ps.solutionName,
    ps.solutionDescription,
    ps.solutionOrgWebsite,
    ps.marketplaceLink,
    ps.specialOfferLink,
    ps.partnerSolutionSlug,
    
    -- Organization/Partner
    o.orgName AS partnerName,
    o.orgWebsite AS partnerWebsite,
    o.orgDescription AS partnerDescription,
    
    -- Industry
    i.industryName,
    si.subIndustryName,
    
    -- Solution Areas (will need aggregation or separate query for M:N)
    sa.solutionAreaName,
    
    -- Metadata
    ps.IsPublished,
    ps.rowCreatedDate,
    ps.rowChangedDate
    
FROM dbo.partnerSolution ps
LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
LEFT JOIN dbo.Industry i ON ps.IndustryId = i.industryId
LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId

WHERE ps.IsPublished = 1

ORDER BY ps.rowChangedDate DESC
```

**Note**: This query will return multiple rows per solution if it has multiple solution areas. Consider aggregating solution areas with `STRING_AGG()` or handling in application code.

### Optimized Query with Solution Area Aggregation

```sql
SELECT 
    ps.partnerSolutionId,
    ps.solutionName,
    ps.solutionDescription,
    ps.solutionOrgWebsite,
    
    o.orgName AS partnerName,
    i.industryName,
    si.subIndustryName,
    
    -- Aggregate multiple solution areas into comma-separated list
    STRING_AGG(sa.solutionAreaName, ', ') AS solutionAreas,
    
    ps.rowChangedDate
    
FROM dbo.partnerSolution ps
LEFT JOIN dbo.organization o ON ps.OrganizationId = o.orgId
LEFT JOIN dbo.Industry i ON ps.IndustryId = i.industryId
LEFT JOIN dbo.SubIndustry si ON ps.SubIndustryId = si.subIndustryId
LEFT JOIN dbo.partnerSolutionByArea psba ON ps.partnerSolutionId = psba.partnerSolutionId
LEFT JOIN dbo.solutionArea sa ON psba.solutionAreaId = sa.solutionAreaId

WHERE ps.IsPublished = 1

GROUP BY 
    ps.partnerSolutionId, ps.solutionName, ps.solutionDescription,
    ps.solutionOrgWebsite, o.orgName, i.industryName, si.subIndustryName,
    ps.rowChangedDate

ORDER BY ps.rowChangedDate DESC
```

---

## Incremental Update Strategy

### SQL-Based Approach (Recommended)

```sql
-- Fetch only solutions modified since last sync
DECLARE @LastSyncDate DATETIME = '2025-12-01 00:00:00'

SELECT *
FROM dbo.partnerSolution
WHERE rowChangedDate > @LastSyncDate
ORDER BY rowChangedDate DESC
```

**Benefits:**
- Server-side filtering (fast)
- Only transfer modified records
- Simple implementation

### API-Based Approach (Current)

```python
# Must fetch ALL solutions and compare MD5 hashes
current_solutions = fetch_from_api()
previous_solutions = load_from_cache()

for solution in current_solutions:
    if md5(solution) != cached_md5:
        # Update needed
```

**Drawbacks:**
- Must download all 540 solutions
- Client-side hashing overhead
- Network bandwidth waste

---

## Next Steps

### 1. Update Python Data Fetcher
Modify `sql_data_fetcher.py` to use discovered schema:
- Use correct column names (`orgName`, not `organizationName`)
- Add solution area aggregation
- Include additional fields (marketplace links, logos, etc.)

### 2. Create Transformation Pipeline
Build script to transform SQL data to Azure AI Search index format:
- Strip HTML from descriptions
- Chunk long content
- Map SQL columns to search index fields
- Handle M:N relationships

### 3. Performance Testing
Compare SQL vs API approach:
- Query performance
- Data completeness
- Incremental update efficiency
- Network overhead

### 4. Production Deployment
If SQL proves superior:
- Implement secure credential management
- Set up scheduled data sync (Azure Functions)
- Add monitoring and error handling
- Create fallback to API if SQL unavailable

---

## Security Considerations

### ✅ Implemented
- SQL Server authentication working
- Encrypted connection (TLS 1.2+)
- Read-only access (using `isdapi` user)
- Credentials in `.env` (not committed)

### 🔒 Recommended
- Migrate to Azure Managed Identity
- Use Azure Key Vault for credentials
- Implement connection pooling
- Add query timeout limits
- Monitor for unusual query patterns
- Regular credential rotation

---

## Comparison Summary

| Aspect | API Approach | SQL Approach |
|--------|--------------|--------------|
| **Solutions Found** | 535 | 540 ✅ |
| **Partner Names** | Parsed from title | Direct field ✅ |
| **Data Freshness** | API cache | Real-time ✅ |
| **Incremental Updates** | MD5 comparison | rowChangedDate ✅ |
| **Field Access** | Limited | Complete ✅ |
| **Complexity** | Medium | Medium |
| **Dependencies** | Public API | DB credentials |
| **Performance** | API rate limits | Direct query ✅ |
| **Reliability** | API availability | DB availability |

**Recommendation**: SQL approach provides **more complete data** and **better update efficiency**. Consider migrating to SQL-based ingestion for production use.

---

## Connection Details

**Server**: `mssoldir-prd-sql.database.windows.net`  
**Database**: `mssoldir-prd`  
**Port**: 1433  
**Authentication**: SQL Server (username/password)  
**Username**: `isdapi`  
**Encryption**: TLS 1.2+ (required)  

**Connection String**:
```
Server=tcp:mssoldir-prd-sql.database.windows.net,1433;
Database=mssoldir-prd;
User ID=isdapi;
Password=***;
Encrypt=yes;
TrustServerCertificate=no;
Connection Timeout=30;
```

---

## Files Updated

1. ✅ `test_sql_connection.py` - Fixed version parsing
2. ✅ `SQL_DATABASE_DISCOVERY.md` - This file (comprehensive findings)

## Files to Update Next

1. 📝 `sql_data_fetcher.py` - Update column names and relationships
2. 📝 `sql_to_search_index.py` - Create transformation pipeline
3. 📝 `compare_sql_vs_api.py` - Create comparison script

---

**Discovery completed successfully! 🎉**

The SQL database provides richer data than the API approach. Next step: Update the data fetcher with correct column names and test full data extraction.
