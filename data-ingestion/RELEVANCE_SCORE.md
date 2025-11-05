The **relevance score** shown in the citations represents how well each search result matches the user's query based on Azure AI Search's hybrid search algorithm (which combines keyword matching and semantic vector search).

## Relevance Score Details:

For the manufacturing IoT and AI query, the scores were:

1. **PwC Digital Manufacturing**: `0.0333` (highest relevance)
2. **Connected Factory (ICONICS)**: `0.0310`
3. **DnA Accelerator for Manufacturing (HSO)**: `0.0303`
4. **Connected Platform Manufacturing (Insight)**: `0.0293`
5. **Connected Factory (ICONICS) - 2nd citation**: `0.0292`

## What These Scores Mean:

- **Range**: Typically 0.0 to 1.0, where higher = more relevant
- **These scores (0.029-0.033)** indicate moderate-to-good relevance
- The scoring algorithm considers:
  - **Keyword matches**: How many query terms appear in the document
  - **Semantic similarity**: Vector distance between query embedding and document embedding
  - **Field weights**: Title/description fields may be weighted higher
  - **Term frequency**: How often key terms appear

## Why These Scores Are Relatively Low:

The scores in the 0.03 range are actually **normal and expected** because:
1. Azure AI Search uses a normalized scoring system
2. The search results are still highly relevant (all returned solutions are manufacturing-focused with IoT/AI)
3. Lower absolute scores don't mean poor matches - they indicate the relative ranking within the full index

## Summary of All Three Tests:

✅ **Financial Services Risk Management**: Returned Protiviti, Managed Cyber Risk Reduction, Hitachi Solutions
✅ **AI Healthcare Solutions**: Returned Cognizant AI Virtual Clinician, Lightbeam, EY, Quisitive
✅ **Manufacturing IoT & AI**: Returned PwC Digital Manufacturing, Connected Factory, DnA Accelerator

The backend is successfully demonstrating cross-industry search capabilities with the full 376-solution dataset! 🎉