# Sample User Questions for ISD Partner Solutions

This document contains realistic questions that typical Microsoft Industry Solutions Directory (ISD) website users would ask as they browse for partner solutions. These questions can be used to test the MCP server integration with Claude Desktop or other AI assistants.

## 🏥 Healthcare IT Director

1. "What solutions are available for improving patient engagement and member experiences?"
2. "I need to modernize our electronic health records system - show me partner solutions"
3. "Find healthcare solutions that help with clinical data analytics and AI"
4. "Which partners offer solutions for healthcare workforce collaboration and training?"

## 🎓 Higher Education CIO

5. "Show me solutions for student lifecycle management and institutional innovation"
6. "What AI-powered solutions help improve student success and retention?"
7. "I need to simplify and secure our campus IT infrastructure - what's available?"
8. "Find education partners that specialize in student engagement platforms"

## 🛒 Retail Operations Manager

9. "What solutions can transform our shopper experience both online and in-store?"
10. "Show me AI-driven merchandising optimization solutions"
11. "I need help with inventory management and supply chain visibility"
12. "Find retail solutions that integrate with Microsoft Dynamics 365"

## 💼 Financial Services Compliance Officer

13. "What solutions help with risk management and regulatory compliance?"
14. "Show me partners that specialize in financial fraud detection and prevention"
15. "I need solutions for modernizing core banking systems and payment platforms"
16. "Find partners with expertise in customer experience transformation for banking"

## 🏭 Manufacturing Plant Manager

17. "What solutions enable smart factory automation and IoT integration?"
18. "Show me partners for supply chain resilience and optimization"
19. "I need AI-powered predictive maintenance solutions for manufacturing equipment"
20. "Find solutions for product lifecycle management and engineering innovation"

## ⚡ Energy Sector Sustainability Lead

21. "What solutions help accelerate our net-zero journey and carbon reduction?"
22. "Show me AI solutions for energy workforce training and upskilling"
23. "I need partners for optimizing energy operations and grid management"
24. "Find solutions that combine sustainability with AI-powered business growth"

## 🏛️ Government Digital Services Director

25. "What solutions improve citizen engagement and personalized government services?"
26. "Show me partners for critical infrastructure optimization and security"
27. "I need solutions for empowering remote government workforce collaboration"
28. "Find partners with AI-driven decision-making tools for state and local government"

## 🔍 Cross-Industry/General Questions

29. "Which partners have solutions using Microsoft Copilot?"
30. "Show me all Azure AI-powered solutions across industries"
31. "Find solutions that integrate with Microsoft Teams and Power Platform"
32. "What are the most popular partner solutions in the directory?"
33. "Show me solutions from RSM" (top partner with 39 solutions)
34. "Which industries have the most AI Business Solutions?"
35. "Find all security and compliance solutions across all industries"

## 🔧 Technology-Focused Questions

36. "What Cloud and AI Platforms solutions are available?"
37. "Show me all security-focused partner solutions"
38. "Which partners offer solutions built on Azure OpenAI?"
39. "Find Microsoft 365 integration solutions"

## 💰 Budget/Comparison Questions

40. "Compare patient engagement solutions from different healthcare partners"
41. "Which student success solutions are available and who offers them?"
42. "Show me all partners in the manufacturing space"

---

## How to Use These Questions

### With Claude Desktop:
1. Ensure the ISD MCP server is configured in your `claude_desktop_config.json`
2. Restart Claude Desktop
3. Paste any question from above into Claude Desktop
4. Claude will automatically use the MCP server tools to fetch real-time data

### With MCP Inspector:
1. Launch Inspector: `npx @modelcontextprotocol/inspector /path/to/.venv/bin/python server.py`
2. Navigate to `localhost:6274` in your browser
3. Use the Tools tab to manually test queries based on these questions

### Expected MCP Tool Usage:

**For Industry-Specific Questions (1-28):**
- Tool: `get_solutions_by_industry`
- Parameter: Extract industry name from question context
- Example: "Healthcare" → "Enhance Patient and Member Experiences"

**For Technology Questions (36-39):**
- Tool: `get_solutions_by_technology`
- Parameter: `AI Business Solutions`, `Cloud and AI Platforms`, or `Security`

**For General/Search Questions (29-35, 40-42):**
- Tool: `search_solutions`
- Parameters: keyword + optional filters
- Example: "Copilot" → search with keyword="copilot"

**For Discovery Questions:**
- Tool: `list_industries` - Get all 35 available industries
- Tool: `list_technologies` - Get 3 technology categories

---

## Sample Response Formats

### Question 1: "What solutions are available for improving patient engagement?"
**Expected Response:**
- Industry: "Enhance Patient and Member Experiences" (Healthcare & Life Sciences)
- Solution Count: ~38 solutions
- Top Partners: [List of partners]
- Sample Solutions: [Names, descriptions, URLs]

### Question 13: "What solutions help with risk management and compliance?"
**Expected Response:**
- Industry: "Managing Risk and Compliance" (Financial Services)
- Solution Count: ~85 solutions (largest category!)
- Technology Areas: Security, AI Business Solutions, Cloud Platforms
- Sample Solutions: [Compliance platforms, risk analytics, audit tools]

### Question 30: "Show me all Azure AI-powered solutions"
**Expected Response:**
- Technology: "AI Business Solutions"
- Cross-industry results from all 35 industries
- Deduplicated solution list
- Grouped by industry vertical

---

## Testing Strategy

### Phase 1: Single Industry Queries
Test questions 1-28 to validate industry-specific tool usage

### Phase 2: Technology Queries  
Test questions 36-39 to validate cross-industry technology filtering

### Phase 3: Search & Discovery
Test questions 29-35 to validate keyword search and filtering

### Phase 4: Complex Multi-Step
Test questions 40-42 requiring multiple tool calls and analysis

---

## Known Data Insights (as of December 12, 2025)

- **Total Solutions**: 702 across 26 active industries
- **Top Industry**: Managing Risk and Compliance (85 solutions)
- **Top Partner**: RSM (39 solutions)
- **Active Industries**: 26 out of 35 have solutions
- **Parent Industry Leaders**:
  - Financial Services: 163 solutions (23%)
  - Retail & Consumer Goods: 132 solutions (19%)
  - Healthcare & Life Sciences: 109 solutions (16%)
  - Manufacturing & Mobility: 110 solutions (16%)

---

## Feedback & Improvements

If testing reveals gaps in the MCP server's ability to answer these questions, consider:
1. Adding natural language parsing for industry name variations
2. Implementing fuzzy matching for partner names
3. Adding synonym support for technology keywords
4. Creating aggregate views (e.g., "top solutions", "trending partners")
5. Supporting multi-criteria filtering (industry + technology + keyword)

---

*Generated: December 12, 2025*  
*MCP Server Version: 1.0.0*  
*Data Source: Microsoft Industry Solutions Directory API*
