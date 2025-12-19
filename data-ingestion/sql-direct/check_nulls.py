#!/usr/bin/env python3
from nl2sql_pipeline import NL2SQLPipeline

pipeline = NL2SQLPipeline()

# Check NULL industries
result = pipeline.execute_sql("""
    SELECT 
        COUNT(DISTINCT solutionName) as solution_count,
        'NULL Industry' as category
    FROM dbo.vw_ISDSolution_All 
    WHERE industryName IS NULL
    UNION ALL
    SELECT 
        COUNT(DISTINCT solutionName),
        'With Industry'
    FROM dbo.vw_ISDSolution_All 
    WHERE industryName IS NOT NULL AND solutionStatus = 'Approved'
""")

print("\nData Quality Check:")
print("="*50)
for row in result['rows']:
    print(f"{row[1]}: {row[0]} solutions")
