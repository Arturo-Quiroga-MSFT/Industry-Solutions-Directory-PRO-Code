# Deployment Checklist for Testing Phase

## 📋 Pre-Deployment Verification

### ✅ Local Testing Complete
- [ ] Customer mode tested locally
- [ ] Seller mode tested locally
- [ ] Both modes show correct badges
- [ ] Token tracking works in both modes
- [ ] Export features work (JSON and Markdown)
- [ ] No errors in backend logs

### ✅ Configuration Review
- [ ] Environment variables set correctly
- [ ] Database connection verified (READ-ONLY)
- [ ] Azure OpenAI credentials valid
- [ ] CORS configured for deployment URLs
- [ ] Mode indicators working

---

## 🚀 Deployment Options

### Option 1: Azure Container Apps (Recommended)

You have existing deployment scripts in `/deployment/`:

#### Customer Mode Deployment
```bash
cd /deployment
./deploy-aca-v2.sh customer
```

#### Seller Mode Deployment  
```bash
cd /deployment
./deploy-aca-v2.sh seller
```

**What you'll get:**
- Separate container apps for each mode
- Public URLs (HTTPS)
- Auto-scaling
- Monitoring and logs

#### Post-Deployment Steps:
1. Note the URLs from deployment output
2. Update `TESTING_GUIDE.md` with URLs
3. Test both URLs to verify correct mode
4. Share URLs with testers

### Option 2: Azure Static Web Apps + Azure Functions

If you prefer serverless:

```bash
cd /deployment
./deploy-v2.9-full.sh
```

### Option 3: Keep Local (Temporary)

If deployment takes time, you can:

1. **Share access via VPN/ngrok** (temporary):
   ```bash
   # Install ngrok: brew install ngrok
   
   # Customer Mode
   ngrok http 5174
   
   # Seller Mode (separate terminal)
   ngrok http 5173
   ```

2. **Provide local setup instructions** for testers

---

## 🔐 Security Checklist

- [ ] Database is READ-ONLY mode (verified)
- [ ] No credentials in code or logs
- [ ] HTTPS enabled for deployment
- [ ] Authentication configured (if needed)
- [ ] Rate limiting considered
- [ ] CORS properly restricted

---

## 📊 Monitoring Setup

### What to Monitor During Testing

1. **Backend Logs**
   ```bash
   # Local monitoring
   tail -f frontend-react/backend/backend.log
   tail -f frontend-react/backend/backend-customer.log
   ```

2. **Key Metrics**
   - Response times
   - Token usage patterns
   - Error rates
   - Most common queries

3. **Azure Monitoring** (if deployed)
   - Container logs
   - Application Insights
   - Request metrics

---

## 👥 Tester Access

### How to Grant Access

#### For Local Testing:
1. Ensure network accessibility
2. Share URLs: `http://localhost:5173` (seller), `http://localhost:5174` (customer)
3. Or use ngrok for remote access

#### For Deployed Version:
1. Share Azure URLs from deployment
2. Configure authentication if needed (Azure AD)
3. Add testers to access list

### Tester List

Create a spreadsheet or list:

| Name | Role | Email | Access Level | Assigned Mode |
|------|------|-------|--------------|---------------|
| | PSA | | Both | Customer + Seller |
| | ISD Team | | Both | Customer + Seller |
| | Legal Review | | Customer Only | Customer |

---

## 📧 Communication Plan

### Initial Announcement (Email/Teams)

**Subject**: 🧪 ISD Chat Application - Testing Phase Begins!

**Body**:
```
Hi Team,

We're excited to invite you to test the new ISD Chat Application! This AI-powered 
tool helps users explore Microsoft's Industry Solutions Directory using natural language.

🔗 Access:
- Customer Mode: [URL]
- Seller Mode: [URL]

📖 Documentation:
- Full Guide: TESTING_GUIDE.md
- Quick Start: QUICK_START_FOR_TESTERS.md
- Feedback Form: TESTING_FEEDBACK.md

⏰ Timeline:
- Testing Period: [Start Date] to [End Date]
- Feedback Due: [Date]
- Follow-up Session: [Date/Time]

🎯 Key Focus:
- Verify Customer Mode is vendor-neutral (NO partner rankings)
- Verify Seller Mode provides competitive intelligence
- Test query understanding and result quality
- Evaluate user experience

Please spend 30-60 minutes testing and submit your feedback using the form provided.

Questions? Reply to this email or ping me on Teams.

Thanks for helping make this tool great!

[Your Name]
```

### Follow-Up Reminders

**Week 1**: Gentle reminder + offer help session  
**Week 2**: "Last call for feedback" reminder  
**Week 3**: Share summary of feedback and next steps

---

## 🧪 Testing Phases

### Phase 1: Individual Testing (Week 1)
- **Goal**: Get broad feedback from all testers
- **Activities**: 
  - Individual exploration
  - Complete feedback forms
  - Report critical issues immediately

### Phase 2: Collaborative Testing (Week 2)
- **Goal**: Deep-dive on specific scenarios
- **Activities**:
  - Group testing session (1 hour)
  - Screen sharing and discussion
  - Compare results across testers

### Phase 3: Validation (Week 3)
- **Goal**: Confirm fixes and readiness
- **Activities**:
  - Retest critical issues
  - Verify improvements
  - Final sign-off

---

## 📊 Success Metrics

### What defines successful testing?

- [ ] **Coverage**: All major features tested
- [ ] **Participation**: >80% of invitees submit feedback
- [ ] **Critical Issues**: <5 critical bugs found
- [ ] **Mode Compliance**: Customer mode passes legal review (no partner bias)
- [ ] **User Satisfaction**: Average rating >4/5
- [ ] **Actionable Feedback**: Clear list of improvements identified

---

## 🔧 Support During Testing

### Be Ready For:

1. **Technical Issues**
   - Have deployment logs ready
   - Monitor error rates
   - Quick response to access issues

2. **Questions**
   - Dedicated Teams channel
   - Office hours for Q&A
   - Email support

3. **Hot Fixes**
   - Plan for rapid iteration
   - Test → Fix → Redeploy cycle
   - Communicate changes to testers

---

## 📝 Post-Testing Actions

### After Testing Completes:

1. **Collect & Analyze Feedback**
   - Aggregate all feedback forms
   - Categorize issues (Critical, High, Medium, Low)
   - Identify common themes

2. **Prioritize Improvements**
   - Quick wins (can fix immediately)
   - Must-fix (before production)
   - Nice-to-have (future releases)

3. **Implementation Plan**
   - Sprint planning for fixes
   - Retest critical changes
   - Document decisions

4. **Thank Testers**
   - Share summary of feedback
   - Show what will be fixed
   - Recognition for participation

---

## 🚦 Go/No-Go Criteria

### Ready for Production Deployment?

- [ ] ✅ No critical bugs
- [ ] ✅ Customer mode passes legal compliance review
- [ ] ✅ Average user satisfaction >4/5
- [ ] ✅ Performance acceptable (<15s average)
- [ ] ✅ Data accuracy verified
- [ ] ✅ Security review passed
- [ ] ✅ Documentation complete
- [ ] ✅ Training materials ready (if needed)

---

## 🎯 Next Steps

1. **Choose deployment method** (Azure Container Apps recommended)
2. **Deploy both modes** to Azure
3. **Update testing guides** with deployment URLs
4. **Send announcement** to testers
5. **Monitor feedback** and respond quickly
6. **Schedule follow-up** session after Week 1

---

**Good luck with the testing phase! 🚀**
