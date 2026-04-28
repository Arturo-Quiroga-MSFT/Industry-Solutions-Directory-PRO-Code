# Chart vs Table Queries - Demo Guide

**Purpose**: Guide for demonstrating visualization capabilities in the Industry Solutions Directory chat applications

> **Important**: In seller mode, the NL2SQL agent prefers returning individual solution rows over aggregates. To reliably trigger chart-generating queries, use phrases like **"counts only"**, **"just the totals"**, or **"summary counts"** in your question.

---

## 📊 **Chart Queries** (Proven Aggregation Queries)

These queries have been tested and confirmed to produce GROUP BY aggregation results that generate charts.

### **Distribution Questions:**
```
"How many total solutions are there in each industry? Just give me the counts."
"Count solutions by solution area — just the totals"
"Show me a count of solutions by geography — totals only"
"How many partners contribute solutions to each industry? Just partner counts per industry."
"How many Healthcare solutions are there by solution area? Counts only."
```

### **Ranking Questions:**
```
"What are the top 10 partners by total number of solutions? Summary counts only."
"Which 5 industries have the most Security solutions? Counts only."
```

### **Comparison Questions:**
```
"Compare solution counts across industries for AI Business Solutions vs Cloud and AI Platforms vs Security — totals only"
"Compare the number of solutions across Canada, US, and Latin America — just counts"
```

### **Verified Results Reference:**

| Query | Rows | Example Data |
|-------|------|-------------|
| Solutions by industry (counts) | 11 | Financial Services: 94, Healthcare: 85 |
| Solutions by solution area | 3 | Cloud & AI: 319, AI Business: 145, Security: 124 |
| Solutions by geography | 3 | US: 447, Canada: 334, Latin America: 204 |
| Top 10 partners | 10 | RSM US LLP: 24, Neudesic: 16, EY: 15 |
| Partners per industry | 11 | Financial Services: 66 partners, Healthcare: 60 |
| Healthcare by solution area | 3 | Cloud & AI: 57, Security: 24, AI Business: 14 |
| Industry × solution area cross-tab | 11 | Multi-column comparison |

---

## 📋 **Table Queries** (Detail-Based)

These queries return **raw detailed data** about specific solutions.

### **List Questions:**
```
"Show me comprehensive cybersecurity and threat protection solutions"
"List all AI and machine learning solutions for healthcare"
"What cloud migration solutions are available?"
"Show me data analytics platforms"
"Find solutions for customer relationship management"
```

### **Search Questions:**
```
"Show me solutions from Microsoft partners in Canada"
"What sustainability reporting solutions are available?"
"Find all Azure-integrated solutions"
"List solutions with marketplace links"
```

### **Detail Questions:**
```
"Show me details about Accenture's solutions"
"What solutions does DXC Technology offer?"
"Find solutions with HIPAA compliance"
"Show me solutions in the financial services sector"
```

---

## 🎯 **Demo Tips**

### **Start with a Chart Query:**
1. Ask: **"How many total solutions are there in each industry? Just give me the counts."**
   - Generates bar/pie chart with 11 industry categories
   - Shows Financial Services leading with 94 solutions
   - Quick at-a-glance market overview

### **Then Show a Table Query:**
2. Ask: **"Show me comprehensive cybersecurity and threat protection solutions"**
   - Shows 50 detailed results with full solution descriptions
   - Demonstrates narrative insights with citations
   - Web Sources section appears (seller mode) with real-time partner news

### **Ranking Visualization:**
3. Ask: **"What are the top 10 partners by total number of solutions? Summary counts only."**
   - Generates partner ranking chart
   - Shows RSM US LLP, Neudesic, EY as top contributors

### **Multi-Category Comparison:**
4. Ask: **"Compare solution counts across industries for AI Business Solutions vs Cloud and AI Platforms vs Security — totals only"**
   - Generates grouped/stacked chart with 3 categories × 11 industries
   - Great for showing technology distribution patterns

---

## 🔍 **Why the Distinction Matters**

| Query Type | Use Case | Output | Best For |
|------------|----------|--------|----------|
| **Detail Queries** | Research specific solutions | Table with all columns | Deep dive, solution exploration |
| **Aggregation Queries** | Understand market trends | Charts/visualizations | Executive summaries, quick insights |

---

## 🎬 **Recommended Demo Flow**

1. **Chart Query** → `"How many total solutions are there in each industry? Just give me the counts."` — shows chart generation
2. **Table Query** → `"Show me AI-powered solutions in Retail — any recent partnerships or product launches?"` — shows detailed table + web search sources
3. **Ranking Chart** → `"What are the top 10 partners by total number of solutions? Summary counts only."` — shows partner landscape
4. **Export** → Demonstrate JSON/Markdown/HTML export of conversation
5. **Follow-ups** → Click suggested follow-up questions to continue the conversation
6. **Compare Modes** → Open seller and customer URLs side-by-side to show different perspectives

---

## 💡 **Key Message Shown in UI**

When a table query is detected, the UI displays:

> ⚡ **"This data is best viewed in table format. Try queries with aggregations (COUNT, SUM, AVG) for visualizations."**

This guides users to ask aggregation questions if they want charts instead of tables.
