"""
Verification script to check indexed data in Azure AI Search
"""
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
import os
from dotenv import load_dotenv
from pathlib import Path
import json

# Load environment variables
backend_env = Path(__file__).parent.parent / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
else:
    load_dotenv()

def verify_index():
    """Verify the indexed data"""
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "partner-solutions-index")
    
    # Create search client
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=credential
    )
    
    print("=" * 80)
    print(f"Verifying Index: {index_name}")
    print(f"Endpoint: {search_endpoint}")
    print("=" * 80)
    
    # 1. Get total document count
    print("\n1. DOCUMENT COUNT")
    print("-" * 80)
    results = search_client.search(
        search_text="*",
        select=["id"],
        top=1,
        include_total_count=True
    )
    total_count = results.get_count()
    print(f"Total documents in index: {total_count}")
    
    # 2. Sample documents
    print("\n2. SAMPLE DOCUMENTS (First 5)")
    print("-" * 80)
    results = search_client.search(
        search_text="*",
        select=["solution_name", "partner_name", "description", "industries", "technologies"],
        top=5
    )
    
    for i, doc in enumerate(results, 1):
        print(f"\nDocument {i}:")
        print(f"  Solution Name: {doc.get('solution_name', 'N/A')}")
        print(f"  Partner Name: {doc.get('partner_name', 'N/A')}")
        print(f"  Industries: {doc.get('industries', [])}")
        print(f"  Technologies: {doc.get('technologies', [])}")
        print(f"  Description: {doc.get('description', 'N/A')[:100]}...")
    
    # 3. Check unique solutions
    print("\n3. UNIQUE SOLUTIONS")
    print("-" * 80)
    results = search_client.search(
        search_text="*",
        select=["solution_name", "partner_name"],
        top=1000
    )
    
    unique_solutions = set()
    for doc in results:
        solution_key = (doc.get('solution_name'), doc.get('partner_name'))
        unique_solutions.add(solution_key)
    
    print(f"Total unique solutions: {len(unique_solutions)}")
    print("\nUnique solutions list:")
    for solution_name, partner_name in sorted(unique_solutions):
        print(f"  - {solution_name} (by {partner_name})")
    
    # 4. Check by industry
    print("\n4. SOLUTIONS BY INDUSTRY")
    print("-" * 80)
    results = search_client.search(
        search_text="*",
        select=["industries"],
        top=1000
    )
    
    industry_counts = {}
    for doc in results:
        industries = doc.get('industries', [])
        for industry in industries:
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    for industry, count in sorted(industry_counts.items()):
        print(f"  {industry}: {count} documents")
    
    # 5. Test search functionality
    print("\n5. TEST SEARCH - 'education'")
    print("-" * 80)
    results = search_client.search(
        search_text="education",
        select=["solution_name", "partner_name", "industries"],
        top=3
    )
    
    for i, doc in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Solution: {doc.get('solution_name', 'N/A')}")
        print(f"    Partner: {doc.get('partner_name', 'N/A')}")
        print(f"    Industries: {doc.get('industries', [])}")
    
    # 6. Test vector search
    print("\n6. TEST VECTOR SEARCH - 'AI solutions for healthcare'")
    print("-" * 80)
    
    # Generate embedding for search query
    from openai import AzureOpenAI
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")
    
    openai_client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_version="2024-02-01",
        azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
    )
    
    query_embedding = openai_client.embeddings.create(
        input="AI solutions for healthcare",
        model=embedding_deployment
    ).data[0].embedding
    
    from azure.search.documents.models import VectorizedQuery
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=3,
        fields="content_vector"
    )
    
    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["solution_name", "partner_name", "industries", "description"],
        top=3
    )
    
    for i, doc in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Solution: {doc.get('solution_name', 'N/A')}")
        print(f"    Partner: {doc.get('partner_name', 'N/A')}")
        print(f"    Industries: {doc.get('industries', [])}")
        print(f"    Description: {doc.get('description', 'N/A')[:150]}...")
    
    print("\n" + "=" * 80)
    print("Verification Complete!")
    print("=" * 80)


if __name__ == "__main__":
    verify_index()
