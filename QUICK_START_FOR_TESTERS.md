# Quick Start Guide for Testers

## 🚀 Get Testing in 5 Minutes!

### Step 1: Access the Application

**Customer Mode** (External-facing):
- Open: http://localhost:5174
- Or deployed URL: `[ADD DEPLOYED URL]`

**Seller Mode** (Internal Microsoft use):
- Open: http://localhost:5173
- Or deployed URL: `[ADD DEPLOYED URL]`

### Step 2: Verify the Mode

Look at the **top-right corner** of the app:
- 🛡️ **CUSTOMER MODE** = External, vendor-neutral
- 💾 **SELLER MODE** = Internal, partner intelligence

### Step 3: Try These 3 Quick Tests

#### Test 1: Basic Query
**Type**: "What healthcare solutions help with patient engagement?"
- ✅ Should return results
- ✅ Should show insights narrative
- ✅ Should suggest follow-up questions

#### Test 2: Mode Difference (CRITICAL)
**In Customer Mode, type**: "What AML solutions are available?"
- ✅ Should focus on capabilities, NOT partner names

**In Seller Mode, type the same**: "What AML solutions are available?"
- ✅ Should show partner names and rankings

#### Test 3: Follow-Up
- **Click** one of the suggested follow-up questions
- ✅ Should execute automatically
- ✅ Should build on previous context

### Step 4: Provide Feedback

Fill out [TESTING_FEEDBACK.md](./TESTING_FEEDBACK.md) and send to:
- **Email**: [Your Email]
- **Teams**: [Channel]

---

## 🎯 Key Things to Check

### ✅ Customer Mode Must NEVER Show:
- Partner rankings ("Top 3 partners are...")
- Partner comparisons ("Partner X vs Partner Y")
- Vendor bias ("Leading provider", "Dominates market")

### ✅ Seller Mode Should Show:
- Partner names everywhere
- Rankings and competitive intel
- Recommendations for specific partners

### ✅ Both Modes Should:
- Understand natural language questions
- Return relevant results
- Show token usage and timing at bottom
- Allow export of conversations

---

## 💡 Sample Questions to Try

**Quick Tests**:
- "What cybersecurity solutions are available?"
- "Show me AI-powered healthcare solutions"
- "Find manufacturing IoT solutions"

**Advanced Tests**:
- "Compare cloud solutions vs on-premises"
- "How many financial services solutions focus on fraud?"
- "What are the top solution areas in healthcare?"

**Edge Cases**:
- "Show me solutions" (should ask for clarification)
- "What does [SpecificPartner] offer?" (tests partner search)
- Ask a follow-up like "tell me more about the first one"

---

## 🐛 Found an Issue?

**Critical Issues** (report immediately):
- Customer mode shows partner names in insights
- App crashes or errors out
- Data looks wrong or corrupted

**Normal Feedback**:
- Use the [TESTING_FEEDBACK.md](./TESTING_FEEDBACK.md) form

---

## 📊 What Those Numbers Mean

At the bottom of each response:
```
📊 1,025 in | 📤 668 out | ∑ 1,693 tokens | ⏱️ 28.64s
```

- **In**: Tokens sent to AI (your question + context)
- **Out**: Tokens in AI's response
- **Total**: Sum of both
- **Time**: How long the query took

*These metrics help us optimize performance and costs.*

---

## ❓ Questions?

Contact: [Your Name/Email]

---

**Happy Testing! Your feedback will make this tool amazing! 🎉**
