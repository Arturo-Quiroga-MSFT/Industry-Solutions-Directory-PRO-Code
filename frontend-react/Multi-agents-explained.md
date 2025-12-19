

## Agent → Tab Mapping

**🧠 Agent 1: Query Planner**
- **Tab**: None (routing only)
- **Purpose**: Decides if new SQL query is needed vs analyzing cached results
- **Output**: `intent` field (not directly shown in UI)

**🔍 Agent 2: SQL Executor** 
- **Tabs**: 📊 **SQL Tab** + 📋 **Table Tab** + 📈 **Charts Tab**
- **Purpose**: Generates SQL query and executes it
- **Outputs**:
  - `sql` → shown in **SQL Tab**
  - `rows` + `columns` → shown in **Table Tab** 
  - `rows` + `columns` → visualized in **Charts Tab**

**📊 Agent 3: Insight Analyzer**
- **Tab**: 💡 **Insights Tab** (content)
- **Purpose**: Analyzes the data and extracts patterns/statistics
- **Output**: `insights` object with:
  - `key_findings`
  - `patterns`
  - `statistics`
  - `recommendations`

**✍️ Agent 4: Response Formatter**
- **Tab**: 💡 **Insights Tab** (presentation)
- **Purpose**: Formats Agent 3's insights into compelling markdown narrative
- **Output**: `narrative` string → rendered as markdown in **Insights Tab**

## Summary

| Tab | Data Source | Agents Involved |
|-----|-------------|-----------------|
| **Insights** 💡 | `narrative` field | Agent 3 + Agent 4 |
| **Table** 📋 | `rows` + `columns` | Agent 2 |
| **Charts** 📈 | `rows` + `columns` | Agent 2 |
| **SQL** 💻 | `sql` field | Agent 2 |

real patterns from the computed statistics.