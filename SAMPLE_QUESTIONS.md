# Sample Questions for Industry Solutions Directory

This document provides example questions you can ask the Industry Solutions Directory chat system, organized by industry and use case.

## Financial Services

- What financial services solutions help with risk management?
- Show me anti-money laundering solutions
- What solutions help with regulatory compliance?
- Banking solutions for customer engagement
- Fraud detection solutions
- Core banking modernization solutions

## Healthcare

- Show me AI-powered healthcare solutions
- What solutions improve patient engagement?
- Electronic health record solutions
- Remote patient monitoring solutions
- Clinical workflow optimization
- Population health management solutions

## Manufacturing

- What manufacturing solutions use IoT and AI?
- Show me predictive maintenance solutions
- Supply chain optimization for manufacturing
- Smart factory solutions
- Quality control and defect detection
- Asset performance management

## Education

- What solutions help with student engagement?
- Campus management solutions
- Fundraising solutions for higher education
- Student lifecycle management
- Learning analytics platforms
- Alumni relationship management

## Retail & Consumer Goods

- Customer experience solutions for retail
- Inventory management solutions
- Point of sale systems
- Personalized shopping experiences
- Omnichannel retail solutions
- Supply chain visibility for retail

## Energy & Resources

- Sustainability solutions for energy companies
- Asset management for oil and gas
- Smart grid solutions
- Predictive maintenance for energy infrastructure
- Emissions management solutions
- Renewable energy optimization

## Government

- Citizen engagement solutions
- Case management for government agencies
- Public safety solutions
- Smart city solutions
- Grant management systems

## Cross-Industry Questions

- Show me all cybersecurity solutions
- What AI and machine learning solutions are available?
- Cloud migration solutions
- Data analytics platforms
- Customer relationship management solutions
- Sustainability and ESG solutions

## How to Use

### Interactive Chat Script
```bash
cd backend
python interactive_chat.py
```

### Direct API Testing
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "YOUR_QUESTION_HERE",
    "session_id": "test-session"
  }'
```

## Tips for Better Results

1. **Be Specific**: Include industry context in your question
   - ✅ "What healthcare solutions help with patient engagement?"
   - ❌ "Show me solutions"

2. **Use Industry Terms**: Reference specific technologies or capabilities
   - ✅ "IoT and AI solutions for manufacturing"
   - ✅ "Anti-money laundering for financial services"

3. **Ask About Problems**: Describe the business challenge
   - ✅ "How can I reduce energy costs?"
   - ✅ "What solutions help detect fraud in real-time?"

4. **Explore Multiple Angles**: Try different phrasings
   - "Risk management solutions for banks"
   - "Compliance solutions for financial services"
   - "Regulatory solutions for banking"
