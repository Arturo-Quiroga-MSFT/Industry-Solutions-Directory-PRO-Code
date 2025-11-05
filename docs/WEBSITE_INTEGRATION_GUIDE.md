# Website Integration Guide
## Industry Solutions Directory - AI Chat Integration

This document outlines options for integrating the Industry Solutions Directory AI chat into the Microsoft Industry Solutions website.

---

## Current Status

### Deployed Components
- **Backend API**: `https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io`
- **Streamlit UI**: `https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io`
- **Technology**: FastAPI backend + Streamlit frontend on Azure Container Apps
- **AI Services**: Azure OpenAI (GPT-4.1-mini), Azure AI Search, Cosmos DB

### Capabilities
- Natural language search across 376+ partner solutions
- 10 industries: Financial Services, Healthcare, Manufacturing, Education, Retail, Energy, Government, etc.
- RAG (Retrieval-Augmented Generation) with citations
- Session persistence and conversation history
- Real-time responses from GPT-4.1-mini

---

## Integration Options

### Option 1: Embeddable Chat Widget (Recommended for Production)

**What it is**: A floating chat button (like Intercom, Zendesk) that appears on website pages.

**User Experience**:
- Small chat icon in bottom-right corner
- Clicks to open chat window overlay
- Doesn't interrupt page content
- Works on any page of the website

**Technical Requirements**:

1. **Add CORS Configuration to Backend**
   - Allow `solutions.microsoftindustryinsights.com` domain
   - Update: `backend/app/main.py`

2. **Create JavaScript Widget**
   - Lightweight (~50KB) JavaScript file
   - Hosted on Azure CDN or Static Web Apps
   - CSS included for styling

3. **Website Integration** (by website admins):
```html
<!-- Add to website footer or header template -->
<script src="https://cdn.azurewebsites.net/industry-chat-widget.js"></script>
<script>
  window.IndustrySolutionsChat.init({
    apiEndpoint: 'https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io',
    position: 'bottom-right',
    primaryColor: '#0078d4',
    theme: 'auto'
  });
</script>
```

**Pros**:
- ✅ Professional user experience
- ✅ Non-intrusive (doesn't affect page layout)
- ✅ Works on any page with 2 lines of code
- ✅ Maintains website branding
- ✅ Mobile responsive

**Cons**:
- ⚠️ Requires JavaScript widget development (~2-3 days)
- ⚠️ Needs CORS configuration

**Timeline**: 1 week for development and testing

---

### Option 2: iFrame Embed (Quickest for Demo)

**What it is**: Embed the Streamlit UI directly in an iframe on website pages.

**User Experience**:
- Full chat interface embedded in page
- Occupies dedicated section of the page
- Scrollable within the page

**Website Integration** (by website admins):
```html
<!-- Add to any page where chat should appear -->
<div style="max-width: 1200px; margin: 2rem auto;">
  <h2>Find Solutions with AI</h2>
  <iframe 
    src="https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
    width="100%"
    height="800px"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
    title="Industry Solutions Chat"
  ></iframe>
</div>
```

**Pros**:
- ✅ Works immediately (no development needed)
- ✅ Full Streamlit UI with all features
- ✅ Easy to test and demo
- ✅ Can be added/removed quickly

**Cons**:
- ⚠️ Takes up full page section (not overlay)
- ⚠️ Not ideal for all pages
- ⚠️ Streamlit branding visible

**Timeline**: Can be implemented today

**Best for**: Dedicated "Find Solutions" page or demo

---

### Option 3: React Component (If Website is React-based)

**What it is**: Native React/TypeScript component integrated into the website's codebase.

**User Experience**:
- Seamless integration with existing website
- Fully customizable styling
- Can be chat widget or embedded component

**Technical Requirements**:

1. **Create React Package**:
```bash
npm install @microsoft/industry-solutions-chat
```

2. **Component Usage**:
```tsx
import { IndustrySolutionsChat } from '@microsoft/industry-solutions-chat';

function SolutionPage() {
  return (
    <div className="solutions-page">
      <h1>Find Solutions</h1>
      <IndustrySolutionsChat 
        apiUrl="https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io"
        theme="light"
        primaryColor="#0078d4"
        mode="widget" // or "embedded"
      />
    </div>
  );
}
```

**Pros**:
- ✅ Native integration (no iframe)
- ✅ Full control over styling
- ✅ Best performance
- ✅ TypeScript support

**Cons**:
- ⚠️ Requires website to use React
- ⚠️ More development effort (1-2 weeks)
- ⚠️ Needs coordination with dev team

**Timeline**: 2 weeks for development and testing

---

### Option 4: Dedicated Chat Page

**What it is**: Create a new page on the website specifically for the AI chat.

**URL Example**: `https://solutions.microsoftindustryinsights.com/ai-chat`

**Implementation**:
- Full-page Streamlit UI
- Linked from navigation or solution pages
- Standalone experience

**Website Integration**:
```html
<!-- Simple redirect or full-page iframe -->
<html>
<head>
  <title>AI Solutions Finder</title>
</head>
<body style="margin: 0; padding: 0; overflow: hidden;">
  <iframe 
    src="https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io"
    style="width: 100vw; height: 100vh; border: none;"
    title="Industry Solutions Chat"
  ></iframe>
</body>
</html>
```

**Pros**:
- ✅ Zero development needed
- ✅ Can be live today
- ✅ Full feature set
- ✅ Easy to maintain

**Cons**:
- ⚠️ Separate page (not integrated)
- ⚠️ Users must navigate away from current page

**Timeline**: Can be implemented immediately

---

## Recommended Approach

### Phase 1: Quick Demo (This Week)
**Use Option 2 (iFrame) or Option 4 (Dedicated Page)**

For team demo and early testing:
1. Website admins create test page: `/solutions/ai-chat` (test environment)
2. Embed Streamlit UI via iframe
3. Share link with stakeholders for feedback
4. No backend changes needed

**Action Items**:
- [ ] Website admins create test page
- [ ] Add iframe code (provided above)
- [ ] Test on staging environment
- [ ] Gather feedback from team

---

### Phase 2: Production Integration (2-3 Weeks)
**Build Option 1 (JavaScript Widget)**

For production deployment:
1. Develop JavaScript widget (~2-3 days)
2. Add CORS to backend
3. Host widget on Azure CDN
4. Website admins add script tag to site template
5. Deploy to production

**Action Items**:
- [ ] Backend team: Add CORS configuration
- [ ] Development: Create JavaScript widget
- [ ] DevOps: Set up Azure CDN hosting
- [ ] Website admins: Add script to site template
- [ ] QA: Test on production-like environment
- [ ] Deploy to production

---

### Phase 3: Long-term Enhancement (Optional)
**Consider Option 3 (React Component)**

If website uses React and wants deeper integration:
1. Convert widget to React component
2. Publish as npm package
3. Full native integration

---

## Technical Requirements for Website Admins

### For iFrame Integration (Option 2)
**What you need**:
- [ ] Ability to edit HTML on website pages
- [ ] Create new page or modify existing page
- [ ] Add iframe code (provided above)

**Time required**: 15-30 minutes

**Testing checklist**:
- [ ] Chat interface loads correctly
- [ ] Can send messages and receive responses
- [ ] Citations display properly
- [ ] Responsive on mobile devices
- [ ] Works across major browsers (Chrome, Edge, Safari, Firefox)

---

### For JavaScript Widget (Option 1)
**What you need**:
- [ ] Access to website template/footer
- [ ] Ability to add `<script>` tags
- [ ] Whitelist domains for CDN (if CSP policies exist)

**Time required**: 30 minutes (after widget is ready)

**Additional configuration**:
```html
<!-- Widget configuration options -->
<script>
  window.IndustrySolutionsChat.init({
    // Backend API endpoint
    apiEndpoint: 'https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io',
    
    // Widget position: 'bottom-right' | 'bottom-left'
    position: 'bottom-right',
    
    // Color theme: 'light' | 'dark' | 'auto'
    theme: 'auto',
    
    // Primary color (Microsoft blue)
    primaryColor: '#0078d4',
    
    // Optional: Initial greeting message
    welcomeMessage: 'Hi! I can help you find Microsoft partner solutions. What industry are you interested in?',
    
    // Optional: Hide on specific pages
    excludePages: ['/admin', '/internal'],
    
    // Optional: Analytics tracking
    analytics: {
      enabled: true,
      trackingId: 'UA-XXXXXXXXX-X'
    }
  });
</script>
```

**Testing checklist**:
- [ ] Widget button appears on pages
- [ ] Opens/closes smoothly
- [ ] Works with website's existing CSS/JavaScript
- [ ] No conflicts with other chat widgets
- [ ] Accessible (keyboard navigation, screen readers)
- [ ] Mobile responsive

---

## Backend Requirements

### CORS Configuration (Required for Options 1 & 3)

**What needs to change**:
Add allowed origins to backend to permit cross-origin requests from the website.

**File**: `backend/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

# Add after app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://solutions.microsoftindustryinsights.com",  # Production
        "https://test.solutions.microsoftindustryinsights.com",  # Staging
        "http://localhost:*",  # Local testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

**Deployment**: Requires backend container rebuild and redeploy

---

## Security Considerations

### Current Security Features
- ✅ Managed Identity for Azure services (no API keys)
- ✅ Azure Container Apps network isolation
- ✅ Cosmos DB firewall rules
- ✅ HTTPS-only communication
- ✅ Input validation on all endpoints

### Additional Security for Website Integration

1. **CORS Whitelisting**
   - Only allow specific domains
   - Production domain only (no wildcards)

2. **Rate Limiting** (Consider adding)
   - Prevent abuse
   - Limit requests per user/session
   - Protection against DoS

3. **API Authentication** (Optional for internal use)
   - API key or JWT token
   - Only if widget should be restricted

4. **Content Security Policy (CSP)**
   - Website admins may need to update CSP headers
   - Allow iframe from Container Apps domain (for Option 2)
   - Allow script from CDN domain (for Option 1)

---

## Cost Considerations

### Current Costs (Azure Container Apps)
- **Backend**: ~$10-30/month (0.5 vCPU, 1GB RAM, 1-3 replicas)
- **Frontend**: ~$10-30/month (0.5 vCPU, 1GB RAM, 1-3 replicas)
- **Azure OpenAI**: Pay-per-token (~$0.15 per 1K tokens GPT-4.1-mini)
- **Azure AI Search**: ~$250/month (Basic tier)
- **Cosmos DB**: ~$25/month (Serverless, current usage)

### Additional Costs for Widget Integration
- **Azure CDN**: ~$5-10/month (for hosting widget JavaScript)
- **Bandwidth**: Minimal (widget is small, API responses are text)

### Estimated Monthly Cost (Production)
- **Total**: ~$300-350/month for full deployment
- **Per Chat Session**: ~$0.02-0.05 (depending on conversation length)

### Scaling Considerations
- Container Apps auto-scale based on traffic
- Can handle thousands of concurrent users
- Costs scale linearly with usage

---

## Success Metrics

### Technical Metrics
- **Uptime**: 99.9% availability
- **Response Time**: < 2 seconds for chat responses
- **Error Rate**: < 0.1% of requests

### Business Metrics
- **Daily Active Users**: Track engagement
- **Queries per Session**: Average conversation length
- **Solution Discovery**: # of solutions clicked from citations
- **User Satisfaction**: Feedback ratings (can add to UI)

### Analytics Integration
Can integrate with:
- Google Analytics
- Azure Application Insights (already enabled)
- Custom tracking events

---

## Support and Maintenance

### Maintenance Tasks
- **Weekly**: Monitor logs and error rates
- **Monthly**: Review usage patterns and costs
- **Quarterly**: Update solution data in index
- **As Needed**: Update models, add features

### Support Contacts
- **Backend Issues**: [Your team contact]
- **Website Integration**: [Website admin contact]
- **Azure Resources**: [DevOps contact]

---

## Next Steps

### For Demo Preparation (This Week)

1. **Technical Team**:
   - [ ] Verify Cosmos DB firewall updated
   - [ ] Test backend health endpoint
   - [ ] Prepare demo script/talking points

2. **Website Admins** (if available):
   - [ ] Create test page on staging environment
   - [ ] Add iframe code
   - [ ] Test basic functionality

3. **Stakeholder Demo**:
   - [ ] Show Streamlit UI (ACA or local)
   - [ ] Demonstrate key features:
     - Natural language queries
     - Multi-industry search
     - Citations with relevance scores
     - Session persistence
   - [ ] Discuss integration options
   - [ ] Get feedback and requirements

### For Production Integration (After Demo)

1. **Decision**: Choose integration approach (recommend Option 1)
2. **Planning**: Create project timeline
3. **Development**: Build chosen integration
4. **Testing**: QA on staging environment
5. **Deployment**: Roll out to production
6. **Monitoring**: Set up alerts and dashboards

---

## Questions for Website Admins

Before integration, please confirm:

1. **Website Technology**:
   - What CMS or framework is used? (e.g., WordPress, React, etc.)
   - Can you add custom HTML/JavaScript?
   - Are there Content Security Policy (CSP) restrictions?

2. **Preferred Integration**:
   - Chat widget (floating button) or embedded chat?
   - Which pages should show the chat?
   - Any design/branding requirements?

3. **Timeline**:
   - When do you need this in production?
   - Is there a staging environment for testing?

4. **Access**:
   - Who can make website changes?
   - What's the approval process?

---

## Appendix: Demo URLs

### Current Deployments
- **Backend API**: https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io
- **Streamlit UI**: https://indsolse-dev-frontend.redplant-675b33da.swedencentral.azurecontainerapps.io
- **Health Check**: https://indsolse-dev-backend.redplant-675b33da.swedencentral.azurecontainerapps.io/api/health

### Example Queries to Demo
1. "What financial services solutions help with risk management?"
2. "Show me AI-powered healthcare solutions"
3. "What manufacturing solutions use IoT and AI?"
4. "Inventory management solutions for retail"
5. "Sustainability solutions for energy companies"

### Sample Use Cases
- **Financial Services VP**: Looking for compliance solutions
- **Healthcare CTO**: Needs EHR integration options
- **Manufacturing Plant Manager**: Wants predictive maintenance
- **Retail Operations**: Seeking inventory optimization
- **Education IT Director**: Looking for student engagement tools

---

## Document Version

- **Version**: 1.0
- **Date**: November 5, 2025
- **Author**: [Your Name]
- **Last Updated**: November 5, 2025

---

## Contact Information

For questions or assistance:
- **Technical Questions**: [Your email]
- **Integration Support**: [Your email]
- **Urgent Issues**: [Your phone/Slack]
