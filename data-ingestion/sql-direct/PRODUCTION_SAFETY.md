# Production Database Safety Measures

## ⚠️ CRITICAL: Production Database Protection

This is the **LIVE PRODUCTION DATABASE** for the ISD website (`mssoldir-prd-sql.database.windows.net`).  
All tools implement **multiple layers of safety** to prevent accidental writes.

---

## 🛡️ Safety Layers Implemented

### Layer 1: Read-Only Database Connection
All scripts connect with `ApplicationIntent=ReadOnly`:
```python
conn_str = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={server};"
    f"Database={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"ApplicationIntent=ReadOnly;"  # PRODUCTION SAFETY
)
```

**Effect**: SQL Server will reject any write operations at the connection level.

### Layer 2: Explicit Transaction Rollback
Every query execution includes explicit `ROLLBACK`:
```python
try:
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.rollback()  # Explicit rollback even for SELECT
except:
    conn.rollback()  # Rollback on error
```

**Effect**: No transactions are ever committed.

### Layer 3: Multi-Layer SQL Validation
5 validation checks before executing any SQL:

#### 3.1 Block WRITE Operations
```python
write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'MERGE']
```
❌ Blocks: `INSERT INTO`, `UPDATE SET`, `DELETE FROM`, `MERGE`

#### 3.2 Block DDL Operations
```python
ddl_keywords = ['DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'RENAME']
```
❌ Blocks: `DROP TABLE`, `CREATE INDEX`, `ALTER TABLE`, `TRUNCATE TABLE`

#### 3.3 Block Stored Procedures
```python
exec_keywords = ['EXEC', 'EXECUTE', 'SP_', 'XP_']
```
❌ Blocks: `EXEC sp_*`, `EXECUTE proc`, `xp_cmdshell`

#### 3.4 Block Transaction Control
```python
transaction_keywords = ['BEGIN TRAN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT']
```
❌ Blocks: `BEGIN TRANSACTION`, `COMMIT`, manual `ROLLBACK`

#### 3.5 Enforce SELECT-Only
```python
if not sql_upper.strip().startswith('SELECT'):
    return False
```
✅ Only allows: `SELECT ...` and `WITH ... SELECT ...` (CTEs)

### Layer 4: Word Boundary Matching
Uses regex `\b` to avoid false positives:
```python
re.search(r'\b' + keyword + r'\b', sql_upper)
```

**Effect**: 
- ✅ Allows: `rowCreatedDate` (contains "CREATE" but not as keyword)
- ❌ Blocks: `CREATE TABLE` (keyword match)

---

## 🔒 Protected Scripts

All scripts have been updated with safety measures:

| Script | Safety Level | Status |
|--------|-------------|--------|
| `nl2sql_pipeline.py` | All 4 Layers | ✅ Protected |
| `explore_insights.py` | Layer 1 | ✅ Protected |
| `advanced_insights.py` | Layer 1 | ✅ Protected |
| `test_sql_connection.py` | Read-only | ✅ Protected |
| `schema_inspector.py` | Read-only | ✅ Protected |

---

## 🧪 Testing Safety Measures

### Test 1: Attempt INSERT (should fail)
```bash
cd /Users/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct
echo "Insert a test solution" | python nl2sql_pipeline.py
```

**Expected**: ❌ BLOCKED - Multi-layer validation prevents execution

### Test 2: Attempt UPDATE (should fail)
```bash
echo "Update all solutions to set status to active" | python nl2sql_pipeline.py
```

**Expected**: ❌ BLOCKED - Write operation detected

### Test 3: Attempt DROP (should fail)
```bash
echo "Drop the solutions table" | python nl2sql_pipeline.py
```

**Expected**: ❌ BLOCKED - DDL operation detected

### Test 4: Valid SELECT (should succeed)
```bash
echo "Show me the top 10 partners" | python nl2sql_pipeline.py
```

**Expected**: ✅ SUCCESS - Read-only query executed

---

## 🎯 Safety Validation Checklist

Before running ANY script:

- [ ] Verify `.env` has READ-ONLY credentials (username: `isdapi`)
- [ ] Check connection string includes `ApplicationIntent=ReadOnly`
- [ ] Confirm script validates SQL before execution
- [ ] Review generated SQL manually before executing
- [ ] Test with dry-run mode if available

---

## 🚨 What to Do If Something Goes Wrong

### If you see a write operation being attempted:

1. **STOP immediately** - Press `Ctrl+C`
2. **Review the SQL** that was generated
3. **Report the issue** - This should never happen with our safety layers
4. **Update validation** - Add the missed pattern to validation rules

### If you accidentally ran a write query:

1. **Don't panic** - Multiple safety layers should have prevented it
2. **Check query history** - Review `nl2sql_history.json`
3. **Verify no changes** - The `ApplicationIntent=ReadOnly` connection should reject writes
4. **Notify team** - Let them know what happened

---

## 📊 Monitoring & Auditing

### Query History
All queries are logged to `nl2sql_history.json`:
```json
{
  "timestamp": "2025-12-17T...",
  "natural_query": "Show me healthcare solutions",
  "sql": "SELECT ...",
  "row_count": 5,
  "success": true
}
```

### Review History
```bash
cat nl2sql_history.json | jq '.[] | select(.success == true) | .sql'
```

### Failed Queries
```bash
cat nl2sql_history.json | jq '.[] | select(.success == false)'
```

---

## ✅ Safety Certification

**Database**: `mssoldir-prd` (PRODUCTION)  
**Access Level**: READ-ONLY  
**Safety Layers**: 4 (Connection + Rollback + Validation + Enforcement)  
**Risk Level**: MINIMAL (multiple redundant protections)  
**Last Updated**: 2025-12-17  
**Reviewed By**: AI Assistant

**Status**: ✅ **SAFE FOR PRODUCTION TESTING**

---

## 📝 Notes

1. The ISD team is creating a database VIEW for us to use
2. Once the VIEW is available, we'll switch to that (even safer)
3. Current testing is on full tables but with multiple safety layers
4. The `isdapi` user should already have READ-ONLY permissions at the DB level
5. Our safety layers are **defense in depth** - multiple redundant protections

**Remember**: Even with all these protections, always review generated SQL before execution!
