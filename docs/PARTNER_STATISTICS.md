# Partner Statistics - Industry Solutions Directory

**Last Updated:** November 8, 2025  
**Author:** Arturo Quiroga, Principal Industry Solutions Architect  
**Purpose:** Statistical analysis of partner solution distribution in the Microsoft Industry Solutions Directory

---

## Overview

This document provides statistical analysis of partner solutions indexed in the Industry Solutions Directory AI Chat Assistant. The data reflects the current state of the `partner-solutions-integrated` search index with Azure AI Search integrated vectorization.

## Total Solution Counts

- **Total Documents in Index:** 535 documents
- **Unique Partner Solutions:** 376 solutions
- **Solutions Ingested from ISD:** 1,486 document chunks (deduplicated to 535)

### Why the Difference?

The integrated vectorization approach with Azure AI Search automatically:
- Removes redundant content through intelligent deduplication
- Creates optimized document segments using built-in chunking
- Merges similar descriptions across multiple categories

**Result:** More efficient search with 535 documents representing 376 complete unique solutions.

---

## Top 25 Most Prolific Partners

Based on number of solutions published on the Microsoft Industry Solutions Directory:

| Rank | Partner | Solutions | Category |
|------|---------|-----------|----------|
| 1 | **RSM** | 39 | System Integrator |
| 2 | **Cognizant** | 18 | System Integrator |
| 3 | **Striim** | 15 | ISV (Data Streaming) |
| 4 | **EY** | 15 | Big 4 Consulting |
| 5 | **AspenTech** | 11 | ISV (Industrial) |
| 6 | **HCLTech** | 11 | System Integrator |
| 7 | **PwC** | 10 | Big 4 Consulting |
| 8 | **HSO** | 8 | Microsoft Partner |
| 9 | **Insight** | 8 | Microsoft Partner |
| 10 | **Wipro** | 8 | System Integrator |
| 11 | **TTEC Digital** | 7 | CX Solutions |
| 12 | **TCS** (Tata Consultancy Services) | 6 | System Integrator |
| 13 | **Honeywell** | 6 | Industrial IoT |
| 14 | **Neudesic** | 6 | Microsoft Partner |
| 15 | **DXC Technology** | 5 | System Integrator |
| 16 | **Adobe** | 5 | ISV (Marketing) |
| 17 | **Anthology** | 5 | ISV (Education) |
| 18 | **Finastra** | 5 | ISV (Financial Services) |
| 19 | **Hitachi Solutions America** | 5 | System Integrator |
| 20 | **Quisitive** | 4 | Microsoft Partner |
| 21 | **Terawe Corporation** | 4 | ISV |
| 22 | **Mobile Mentor** | 4 | Microsoft Partner |
| 23 | **CitiusTech** | 3 | Healthcare IT |
| 24 | **Amperity** | 3 | ISV (CDP) |
| 25 | **Avanade** | 3 | Microsoft Partner |

---

## Key Insights

### Partner Distribution

1. **RSM Dominates** - With 39 solutions, RSM has more than double the next partner, showing strong commitment across multiple industries (Retail, Manufacturing, Healthcare, Education, Government).

2. **Big 4 Presence** - EY (#4 with 15 solutions) and PwC (#7 with 10 solutions) demonstrate strong involvement in industry-specific Microsoft solutions.

3. **System Integrators** - Top global SIs well-represented:
   - Cognizant (18 solutions)
   - HCLTech (11 solutions)
   - Wipro (8 solutions)
   - TCS (6 solutions)
   - DXC Technology (5 solutions)

4. **Industry-Specific ISVs** - Specialized vendors focusing on their verticals:
   - Striim: Real-time data streaming (15 solutions)
   - AspenTech: Industrial process optimization (11 solutions)
   - Honeywell: Industrial IoT and building automation (6 solutions)
   - Adobe: Marketing and customer experience (5 solutions)
   - Finastra: Financial services (5 solutions)
   - Anthology: Education technology (5 solutions)

5. **Microsoft Partner Ecosystem** - Strong representation from partners specializing in Azure and M365:
   - HSO (8 solutions)
   - Insight (8 solutions)
   - TTEC Digital (7 solutions)
   - Neudesic (6 solutions)
   - Quisitive (4 solutions)
   - Mobile Mentor (4 solutions)

### Industry Coverage

The 376 unique solutions span all major industries:
- Financial Services
- Healthcare & Life Sciences
- Manufacturing & Mobility
- Retail & Consumer Goods
- Education
- Energy & Resources
- State & Local Government
- Public Sector

---

## Methodology

**Data Source:** Azure AI Search index `partner-solutions-integrated`  
**Endpoint:** https://indsolse-dev-srch-okumlm.search.windows.net  
**Analysis Date:** November 8, 2025  
**Tool:** Python script (`verify_index.py` and `partner_analysis.py`)

**Partner Name Normalization:**
- Combined variations (e.g., "RSM US LLP" + "RSM" → "RSM")
- Standardized naming (e.g., "Tata Consultancy Services" + "TCS" → "TCS")
- Merged related entities (e.g., "Cognizant Technology Solutions" + "Cognizant" → "Cognizant")

---

## Business Value

This partner distribution analysis helps:

1. **Microsoft Account Teams** - Understand which partners have the deepest solution portfolios for customer conversations
2. **Partner Managers** - Identify engagement opportunities and gaps in partner coverage
3. **Solution Architects** - Quickly find partners with expertise in specific industries or technologies
4. **Customers** - Discover partners with proven track records and multiple solution offerings

---

## Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Full deployment instructions
- [Cost Estimation](COST_ESTIMATION.md) - Azure resource costs
- [Architecture](../ARCHITECTURE.md) - System architecture overview
- [Project Summary](../PROJECT_SUMMARY.md) - Complete project documentation

---

**Solution Owner:** Arturo Quiroga  
**Role:** Principal Industry Solutions Architect, Microsoft  
**Contact:** For questions about this analysis or the Industry Solutions Directory Chat Assistant
