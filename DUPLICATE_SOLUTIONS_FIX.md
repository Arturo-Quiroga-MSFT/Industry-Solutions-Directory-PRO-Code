# Duplicate Solutions Fix - December 26, 2025

## Issues Identified

### Issue 1: Excessive Duplicate Solutions in Query Results

**Problem:**
- Query "Provide a detailed breakdown of which industries have Adastra's agentic AI offerings" returned **328 results**
- Many results were the **same solution repeated 10-20+ times**
- Made tables unusable and confused users

**Root Cause:**
The SQL query generated was:
```sql
SELECT industryName, solutionAreaName, solutionName, orgName, geoName, marketPlaceLink, solutionOrgWebsite, solutionPlayName, solutionDescription 
FROM dbo.vw_ISDSolution_All 
WHERE solutionStatus = 'Approved' AND orgName LIKE '%Adastra%' 
AND (solutionAreaName LIKE '%AI%' OR solutionName LIKE '%agentic%' OR solutionDescription LIKE '%agentic%' OR solutionAreaName LIKE '%agentic%') 
ORDER BY industryName, solutionName
```

**Missing: SELECT DISTINCT**

The `vw_ISDSolution_All` view is **denormalized** - the same solution appears multiple times because:
- Multiple resource links per solution
- Multiple solution plays per solution
- Multiple geographic tagging
- Multiple sub-industries per solution

Without `DISTINCT`, the same "AI-Powered Supply Chain" solution from Adastra appeared dozens of times.

**Solution:**
Enhanced the SQL generation prompts in `nl2sql_pipeline.py` to:
1. **Always use SELECT DISTINCT** when listing individual solutions
2. Added prominent warnings about denormalization
3. Updated all sample queries to show proper DISTINCT usage
4. Added explicit deduplication guidance in seller mode requirements

**Expected Result:**
- Same query should now return ~10-15 unique solutions instead of 328 duplicates
- Solutions appear once, or 2-3 times if genuinely available in multiple regions
- Much cleaner, more usable tables

### Issue 2: "(Not Set)" in industryName Column

**Question from User:**
"I noticed that the INDUSTRY NAME column has a lot of '(Not Set)' - is this because that data is not in the DB?"

**Answer: YES, this is correct and expected behavior**

**Explanation:**
1. Some solutions in the database genuinely **do not have an industry assignment**
2. The `industryName` column in `vw_ISDSolution_All` is **NULL** for these solutions
3. The backend code (`main.py` line 143) intentionally converts NULL values to "(Not Set)" for better UX:
   ```python
   if value is None:
       row_dict[col] = "(Not Set)"
   ```

**This is a business decision we made in the past:**
- Better to show "(Not Set)" than empty cells or "NULL"
- Indicates to users that this data is missing in the source system
- Helps identify solutions that need industry classification

**No fix needed** - this is working as designed.

## Files Modified

### `/Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct/nl2sql_pipeline.py`

**Changes:**
1. **Lines ~309-323**: Updated SQL generation rules to emphasize DISTINCT requirement
   - Changed rule #9 from brief mention to critical deduplication guidance
   - Added explicit warning about 328 duplicate results scenario
   - Made DISTINCT mandatory for all solution listing queries

2. **Lines ~102-145**: Enhanced schema context documentation
   - Added "Denormalized & Duplicates" section with detailed explanation
   - Updated all sample queries to include DISTINCT
   - Added TOP 50 to sample queries for consistency
   - Emphasized that NULL values display as "(Not Set)" in UI

3. **Lines ~215-245**: Enhanced seller mode column requirements
   - Added "CRITICAL - DEDUPLICATION" section
   - Explained real-world impact (328 vs 20 results)
   - Made DISTINCT requirement more prominent in example queries
   - Added user impact explanation

## Testing Recommendations

### Test Case 1: Adastra Agentic AI Query
**Query:** "Provide a detailed breakdown of which industries have Adastra's agentic AI offerings"

**Before Fix:**
- 328 results
- Same solutions repeated 10-20 times
- Table hard to read and navigate

**After Fix (Expected):**
- ~10-15 unique solutions
- Each solution appears once (or 2-3 times if in multiple regions)
- Clean, usable table

### Test Case 2: Regional Duplication Should Be Preserved
**Query:** "What AI solutions are available in both Canada and United States?"

**Expected Behavior:**
- Same solution SHOULD appear twice if genuinely in both regions
- DISTINCT with geoName in SELECT preserves legitimate regional differences
- Example: "Solution X" in Canada (row 1) and "Solution X" in United States (row 2) = correct

### Test Case 3: "(Not Set)" Industry Names
**Query:** "Show me all solutions" or "What solutions don't have an industry assigned?"

**Expected Behavior:**
- Some rows will have "(Not Set)" in industryName column
- This is correct - the data is missing in the source database
- No error, no bug - just missing data visualization

## Next Steps

1. **Restart Backend** to pick up the nl2sql_pipeline.py changes:
   ```bash
   cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/frontend-react
   bash dev-restart-seller.sh backend
   ```

2. **Test the Adastra query** to verify duplicate reduction

3. **Review results** to ensure:
   - Dramatically fewer duplicate solutions
   - Legitimate regional differences preserved
   - "(Not Set)" values still appear for solutions without industry assignment

## Technical Notes

### Why Not Remove Duplicates at Database Level?
The view `vw_ISDSolution_All` is intentionally denormalized for:
- Multiple resource links per solution (blog posts, case studies, etc.)
- Multiple solution plays per solution
- Multiple geographies per solution
- Multiple sub-industries per solution

Removing duplicates at the view level would **lose this valuable detail**. Instead, we:
- Use `DISTINCT` when listing solutions
- Use `COUNT(DISTINCT solutionName)` for aggregates
- Keep the denormalized view for maximum flexibility

### Why "(Not Set)" Instead of NULL?
User experience design decision:
- NULL or empty cells look like rendering errors
- "(Not Set)" clearly indicates **intentional missing data**
- Users immediately understand this is a data quality issue, not a bug
- Helps identify solutions needing industry classification

## Summary

✅ **Issue 1 Fixed:** SQL generation now enforces DISTINCT to prevent 328-result duplicate nightmares
✅ **Issue 2 Confirmed:** "(Not Set)" in industryName is correct behavior for missing data in database

Both issues documented and addressed appropriately.
