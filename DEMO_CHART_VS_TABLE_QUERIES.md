# Chart vs Table Queries - Demo Guide

**Purpose**: Guide for demonstrating visualization capabilities in the Industry Solutions Directory chat applications

---

## 📊 **Chart Queries** (Aggregation-Based)

These queries use **COUNT, SUM, AVG, GROUP BY** and generate visualizations.

### **Distribution Questions:**
```
"How many solutions are available by industry?"
"Show me the distribution of cybersecurity solutions across different geographies"
"What is the breakdown of AI solutions by partner organization?"
"How many solutions are in each solution area?"
"Count solutions by solution play"
"Show me partner contribution statistics for healthcare solutions"
```

### **Comparison Questions:**
```
"Compare the number of cloud solutions across Canada, US, and Latin America"
"Which industries have the most AI and machine learning solutions?"
"What are the top 10 partners by solution count?"
"Compare solution availability across different solution areas"
```

### **Statistical Questions:**
```
"What is the average number of solutions per partner?"
"Show me solution counts grouped by industry and region"
"What percentage of solutions are in each geography?"
```

### **Categorical Analysis:**
```
"Break down manufacturing solutions by solution play"
"Group financial services solutions by partner and count"
"Show solution distribution across healthcare subsectors"
```

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

### **Start with Table Queries:**
1. Ask: **"Show me comprehensive cybersecurity and threat protection solutions"**
   - Shows 50 detailed results
   - Demonstrates narrative insights generation
   - Shows partner citations (seller mode) vs generic insights (customer mode)
   - Highlights mode differences

### **Then Move to Chart Queries:**
2. Ask: **"How many solutions are available by industry?"**
   - Generates bar/pie chart
   - Shows aggregated data
   - Demonstrates visualization capabilities
   - Quick at-a-glance insights

3. Ask: **"What are the top 10 partners by solution count?"**
   - Generates ranking visualization
   - Shows competitive landscape (seller mode)
   - May show generic distribution (customer mode)

### **Comparison Demo:**
4. Ask: **"Compare cloud solutions across Canada, US, and Latin America"**
   - Multi-category comparison chart
   - Geographic distribution visualization
   - Shows regional coverage

---

## 🔍 **Why the Distinction Matters**

| Query Type | Use Case | Output | Best For |
|------------|----------|--------|----------|
| **Detail Queries** | Research specific solutions | Table with all columns | Deep dive, solution exploration |
| **Aggregation Queries** | Understand market trends | Charts/visualizations | Executive summaries, quick insights |

---

## 🎬 **Recommended Demo Flow**

1. **Start with Detail Query** → Show narrative insights and partner recommendations (seller mode)
2. **Export Conversation** → Demonstrate JSON/Markdown/HTML export
3. **Switch to Aggregation** → Show chart generation with industry breakdown
4. **Compare Modes** → Open both seller and customer URLs side-by-side
5. **Show Follow-ups** → Use suggested questions to continue conversation

---

## 💡 **Key Message Shown in UI**

When a table query is detected, the UI displays:

> ⚡ **"This data is best viewed in table format. Try queries with aggregations (COUNT, SUM, AVG) for visualizations."**

This guides users to ask aggregation questions if they want charts instead of tables.
