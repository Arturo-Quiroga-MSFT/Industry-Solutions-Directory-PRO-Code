# ISD Website Update Monitor

**Owner:** Arturo Quiroga, Principal Industry Solutions Architect, Microsoft  
**Purpose:** Monitor Microsoft Industry Solutions Directory for new or updated partner solutions  
**Last Updated:** November 8, 2025

---

## Overview

This directory contains scripts to check if there are updates in the ISD website that need to be added to the search index.

## Scripts

### `check_for_updates.py`
Compares current ISD website content against the existing search index to identify:
- **New solutions** not yet in the index
- **Modified solutions** with content changes
- **Removed solutions** no longer on the website

**Usage:**
```bash
python check_for_updates.py
```

**Output:**
- Summary of changes detected
- List of new solution URLs
- List of modified solution IDs
- Recommendations for re-indexing

### `fetch_current_solutions.py`
Utility script to fetch all current partner solutions from the ISD website API.

**Usage:**
```bash
python fetch_current_solutions.py --output current_solutions.json
```

---

## Workflow

### 1. Check for Updates
```bash
# Run the update checker
python check_for_updates.py
```

### 2. Review Changes
The script will output:
- Number of new solutions found
- Number of modified solutions
- Number of removed solutions
- Detailed list of changes

### 3. Re-Index if Needed
If updates are found, run the integrated vectorization pipeline:
```bash
cd ../integrated-vectorization
python run_ingestion.py
```

---

## Configuration

Scripts use the same configuration as the main application:
- **Search Service:** From `AZURE_SEARCH_SERVICE` environment variable
- **Index Name:** `partner-solutions-integrated`
- **ISD API:** `https://appsource.microsoft.com/api/industries/partnersolutions`

---

## Scheduling

### Recommended Schedule
- **Weekly:** Check for updates every Monday morning
- **After announcements:** Check after Microsoft partner events
- **Before demos:** Ensure index is current

### Automation Options

**Option 1: Cron Job (local)**
```bash
# Add to crontab for weekly Monday 9 AM check
0 9 * * 1 cd /path/to/update-monitor && python check_for_updates.py
```

**Option 2: Azure Logic Apps**
Create a Logic App with:
- Recurrence trigger (weekly)
- HTTP action to call check_for_updates script via webhook
- Email notification with results

**Option 3: GitHub Actions**
Schedule via `.github/workflows/check-updates.yml` (see example in this directory)

---

## Output Files

- `last_check.json` - Timestamp and summary of last check
- `new_solutions.json` - List of newly discovered solutions
- `modified_solutions.json` - Solutions with content changes
- `removed_solutions.json` - Solutions no longer on website

---

## Related Documentation

- [Main Data Ingestion README](../README.md)
- [Integrated Vectorization](../integrated-vectorization/README.md)
- [Partner Statistics](../../docs/PARTNER_STATISTICS.md)

---

**Next Steps:**
1. Run `check_for_updates.py` to establish baseline
2. Review output and verify accuracy
3. Set up scheduled checks (weekly recommended)
4. Document update workflow in team processes
