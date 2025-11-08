# Archive Directory

**Purpose:** Historical files from earlier development phases  
**Status:** Archived - not used in production

---

## Directory Structure

### `old-manual-ingestion/`
**Purpose:** Original manual ingestion scripts (replaced by integrated-vectorization approach)

Files:
- `ingest_data.py` - Original manual ingestion script with client-side vectorization
- `ingest_data_test.py` - Test version with limited data
- `inspect_document.py` - Utility to inspect indexed documents
- `check_index_schema.py` - Utility to verify index schema

**Why Archived:** Replaced by integrated-vectorization approach in v2.8 which uses Azure AI Search's built-in vectorization for better performance and simpler code.

---

### `mcs-compatibility/`
**Purpose:** Microsoft Cloud for Sustainability compatibility attempts

Files:
- `copy_to_mcs_index.py` - Script to copy data to MCS-compatible index
- `create_mcs_compatible_index.py` - Create index compatible with MCS schema
- `delete_mcs_index.py` - Cleanup script for MCS test index

**Why Archived:** MCS integration was explored but not pursued. Current solution uses standard Azure AI Search indexes.

---

### `logs-and-output/`
**Purpose:** Historical logs and test output from development

Files:
- `all-data-indexed.txt` - Complete ingestion logs from manual approach
- `FULL_INDEX_VERIFICATION.txt` - Verification output for old manual index
- `index-verification.txt` - Earlier verification output
- `re-index-of-solutions.txt` - Re-indexing logs
- `test-run.text` - Test execution logs
- `test-run2.txt` - Additional test logs
- `unknown-solutions.txt` - Parsing errors log
- `morecurls.sh` - cURL test scripts

**Why Archived:** Historical logs preserved for reference. Current verification outputs are in `/reports/` directory.

---

## Production Approach

The current production approach is in **`../integrated-vectorization/`** directory which uses:
- Azure AI Search integrated vectorization (automatic query vectorization)
- REST API calls (no Python SDK dependency issues)
- Simpler, more maintainable code
- Better performance

See `../integrated-vectorization/README.md` for current approach.

---

**Last Updated:** November 8, 2025  
**Solution Owner:** Arturo Quiroga, Principal Industry Solutions Architect
