# ISD Chat Application - Testing Guide for PSAs & ISD Team

## 📋 Overview

Welcome to the testing phase of the **Industry Solutions Directory Chat Application**! This guide will help you test both modes of the application and provide valuable feedback.

---

## 🎯 What You're Testing

This is an AI-powered chatbot that lets users ask natural language questions about Microsoft's Industry Solutions Directory. The app uses a **4-agent AI pipeline** powered by Azure OpenAI to:

1. **Understand Intent** - Analyzes what you're asking
2. **Generate SQL** - Converts your question to database queries
3. **Extract Insights** - Analyzes results and identifies patterns
4. **Format Response** - Presents findings in a compelling narrative

### Key Innovation: Dual-Mode System

The app runs in **two modes** for different audiences:

#### 🛡️ **Customer Mode** (External Users)
- **Purpose**: For external customers browsing solutions
- **Behavior**: 
  - Focuses on solution **capabilities** and **categories**
  - No partner rankings or comparisons
  - Completely vendor-neutral insights
  - Legal compliance-focused (no bias toward specific partners)

#### 💾 **Seller Mode** (Internal Microsoft Use)
- **Purpose**: For Microsoft sellers and PSAs
- **Behavior**:
  - Shows partner names and rankings
  - Provides competitive intelligence
  - Helps identify top partners by solution area
  - Partner-specific recommendations

---

## 🚀 How to Access

### ⭐ Deployed Testing URLs (Recommended)

**Customer Mode (External-facing):**
- **Frontend**: https://isd-chat-customer-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io
- Backend API: https://isd-chat-customer-backend.redplant-675b33da.swedencentral.azurecontainerapps.io

**Seller Mode (Internal Microsoft use):**
- **Frontend**: https://isd-chat-seller-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io
- Backend API: https://isd-chat-seller-backend.redplant-675b33da.swedencentral.azurecontainerapps.io

### Option 2: Local Testing (If Running Locally)

**Customer Mode:**
- URL: http://localhost:5174
- Backend: http://localhost:8001

**Seller Mode:**
- URL: http://localhost:5173
- Backend: http://localhost:8000

### Option 2: Deployed Version

*[Add deployment URLs here once deployed]*

**Customer Mode:**
- URL: `[Customer Mode URL]`

**Seller Mode:**
- URL: `[Seller Mode URL]`

---

## 🧪 What to Test

### 1. Sample Questions by Category

Try these questions in **both modes** and compare the responses:

#### **Financial Services**
- "What solutions help with anti-money laundering and fraud detection?"
- "Show me risk management solutions for banks"
- "What regulatory compliance solutions are available?"
- "Compare banking solutions for customer engagement"

#### **Healthcare**
- "What AI-powered solutions help with patient engagement?"
- "Show me telehealth and remote monitoring solutions"
- "What solutions support electronic health records?"
- "Find clinical workflow optimization solutions"

#### **Manufacturing**
- "What smart factory and Industry 4.0 solutions exist?"
- "Show me predictive maintenance solutions"
- "What IoT solutions are available for manufacturing?"
- "Find supply chain optimization solutions"

#### **Cross-Industry**
- "What cybersecurity solutions protect against threats?"
- "Show me AI and machine learning solutions"
- "What cloud migration solutions are available?"
- "Find sustainability and ESG reporting solutions"

#### **Advanced Queries** (Test Intelligence)
- "How many healthcare solutions focus on AI?"
- "Compare security solutions vs data analytics solutions"
- "What are the top solution areas in financial services?"
- "Show me solutions that integrate with Microsoft 365"

### 2. Features to Test

#### ✅ Core Functionality
- [ ] **Basic search** - Simple questions return relevant results
- [ ] **Natural language understanding** - Conversational questions work
- [ ] **Result accuracy** - Results match the query intent
- [ ] **Data completeness** - All important columns are shown

#### ✅ User Experience
- [ ] **Response speed** - How fast do responses appear?
- [ ] **Insights quality** - Are insights helpful and actionable?
- [ ] **Follow-up questions** - Are suggested questions relevant?
- [ ] **Clickable follow-ups** - Can you click and execute follow-up questions?

#### ✅ Data Visualization
- [ ] **Insights tab** - Narrative insights are clear and compelling
- [ ] **Table tab** - Data is well-organized and readable
- [ ] **Charts tab** - Visualizations are meaningful
- [ ] **SQL tab** - Generated SQL is visible (optional)

#### ✅ Export Features
- [ ] **JSON export** - Download conversation as JSON
- [ ] **Markdown export** - Download conversation as Markdown with tables

#### ✅ Mode Differences (Test Both!)
- [ ] **Customer mode** - NO partner names in insights (check carefully!)
- [ ] **Seller mode** - Partner names and rankings ARE shown
- [ ] **Mode indicator** - Badge shows correct mode at top
- [ ] **Follow-up questions** - Different based on mode

#### ✅ Token & Performance Metrics
- [ ] **Token display** - Shows input/output/total tokens
- [ ] **Timing display** - Shows elapsed time per query
- [ ] **Metrics accuracy** - Numbers make sense

### 3. Edge Cases to Try

- **Ambiguous questions**: "Show me solutions" (should ask for clarification)
- **Very specific**: "What solutions does [specific partner name] have?"
- **Multi-faceted**: "Healthcare AI solutions for patient engagement in telehealth"
- **Comparisons**: "Compare cloud solutions vs on-premises solutions"
- **Follow-up context**: Ask a question, then ask "show me more details about the first one"

---

## 📊 Key Metrics to Note

While testing, pay attention to:

1. **Token Usage**
   - Input tokens: How much context is being sent
   - Output tokens: How verbose the response is
   - Total tokens: Overall consumption per query
   - *Typical range: 500-2000 tokens per query*

2. **Response Time**
   - How long from submit to response
   - *Target: Under 15 seconds for most queries*

3. **Result Quality**
   - Are results relevant?
   - Are insights actionable?
   - Is the narrative clear and helpful?

---

## 🎭 Mode Comparison Testing

**CRITICAL TEST**: Ask the SAME question in both modes and compare:

### Example Test Case: AML Query

**Question**: "What solutions help with anti-money laundering?"

**Expected Customer Mode Response**:
- ✅ Focus on AML **capabilities**
- ✅ Aggregate statistics (e.g., "18 solutions available")
- ✅ Technology approaches (AI, ML, pattern detection)
- ❌ NO specific partner names in insights
- ❌ NO partner rankings or "top partners"

**Expected Seller Mode Response**:
- ✅ Partner names and counts (e.g., "DXC Technology: 12 solutions")
- ✅ Partner rankings and comparisons
- ✅ Recommendations for specific partners to engage
- ✅ Competitive intelligence about partner portfolios

### Mode Compliance Checklist

**Customer Mode Must NEVER Show**:
- ❌ "Top partners" or partner rankings
- ❌ "Partner X leads with Y solutions"
- ❌ Direct vendor comparisons
- ❌ Phrases like "dominates", "market leader", "stands out"
- ❌ Partner names in key findings or recommendations

---

## 🐛 Known Issues & Limitations

Please note these current limitations:

1. **Read-Only Database**: Cannot modify data, only query
2. **Single Query Focus**: Each question is independent (limited conversation memory)
3. **SQL Limitations**: Complex multi-step queries may need clarification
4. **Response Time**: First query after restart may be slower (cold start)
5. **Token Limits**: Very large result sets may be summarized

---

## 📝 Feedback Template

Please use the [TESTING_FEEDBACK.md](./TESTING_FEEDBACK.md) file to provide structured feedback.

### Quick Feedback Areas

**What to comment on:**

1. **Mode Effectiveness**
   - Does Customer mode truly feel vendor-neutral?
   - Does Seller mode provide useful competitive intelligence?
   - Are the differences clear and appropriate?

2. **Query Understanding**
   - Does it understand your questions correctly?
   - Are clarification requests reasonable?
   - Do suggested refinements help?

3. **Insight Quality**
   - Are insights actionable and valuable?
   - Is the narrative compelling or just data dumps?
   - Are follow-up questions relevant?

4. **User Experience**
   - Is the interface intuitive?
   - Is response time acceptable?
   - Are visualizations helpful?

5. **Data Accuracy**
   - Do results match your expectations?
   - Are solution descriptions accurate?
   - Any obvious data quality issues?

---

## 🚨 Critical Issues to Report Immediately

If you encounter any of these, please report ASAP:

- **Legal Compliance**: Customer mode shows partner rankings or comparisons
- **Security**: Exposed credentials or sensitive data
- **System Errors**: Crashes, timeouts, or complete failures
- **Data Leakage**: Wrong mode data showing in wrong mode

---

## 💬 How to Provide Feedback

1. **Structured Feedback**: Fill out [TESTING_FEEDBACK.md](./TESTING_FEEDBACK.md)
2. **Screenshots**: Include screenshots of issues or excellent responses
3. **Export Examples**: Export conversations (JSON/Markdown) that illustrate points
4. **Questions**: Email or Teams message for clarifications

---

## 👥 Testing Timeline

**Phase 1: Initial Testing** (Week 1)
- Individual exploration and feature testing
- Complete feedback form
- Report critical issues

**Phase 2: Collaborative Testing** (Week 2)
- Group testing sessions
- Compare results across testers
- Refine feedback based on discussions

**Phase 3: Final Validation** (Week 3)
- Retest after fixes
- Sign-off for production deployment

---

## 📞 Support & Questions

**For technical issues:**
- Contact: [Your Name/Email]
- Teams: [Channel Link]

**For feedback submission:**
- Submit feedback file via: [Email/Teams/SharePoint]

---

## 🎉 Thank You!

Your testing and feedback are crucial to making this tool successful for both customers and Microsoft sellers. Thank you for your time and insights!

---

**Version**: v2.9 (Dual-Mode with Token Tracking)  
**Last Updated**: December 22, 2025  
**Testing Period**: [Add dates]
