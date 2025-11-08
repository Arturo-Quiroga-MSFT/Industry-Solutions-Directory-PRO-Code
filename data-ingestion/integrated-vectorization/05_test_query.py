#!/usr/bin/env python3
"""
Step 5: Test queries with automatic vectorization.

This demonstrates the key benefit of integrated vectorization:
- Just send a text query
- The vectorizer automatically converts it to vectors
- No manual embedding calls needed!
"""

import sys
import os
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.identity import DefaultAzureCredential

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def test_vector_query(query_text):
    """Test a vector query with automatic vectorization."""
    print("="*60)
    print("Testing Integrated Vectorization Query")
    print("="*60)
    print(f"\nQuery: {query_text}")
    print(f"Index: {config.INDEX_NAME}")
    
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint=config.SEARCH_ENDPOINT,
        index_name=config.INDEX_NAME,
        credential=credential
    )
    
    # Create a vectorizable text query
    # The vectorizer will automatically convert the text to a vector!
    vector_query = VectorizableTextQuery(
        text=query_text,
        k_nearest_neighbors=5,
        fields="content_vector"
    )
    
    print("\n🔍 Executing query...")
    print("   (Vectorizer automatically converting text to vector)")
    
    # Execute the search
    results = search_client.search(
        search_text=None,  # Pure vector search
        vector_queries=[vector_query],
        select=["solution_name", "partner_name", "description", "solution_url", "industries", "technologies"],
        top=5
    )
    
    print("\n📊 Results:")
    print("-" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('solution_name', 'N/A')}")
        print(f"   Partner: {result.get('partner_name', 'N/A')}")
        print(f"   Industries: {', '.join(result.get('industries', []))}")
        print(f"   Technologies: {', '.join(result.get('technologies', []))}")
        print(f"   Score: {result.get('@search.score', 0):.4f}")
        print(f"   URL: {result.get('solution_url', 'N/A')}")
        
        description = result.get('description', '')
        if description:
            # Clean and truncate description
            clean_desc = description.replace('<p>', '').replace('</p>', '').replace('<br>', ' ')
            if len(clean_desc) > 150:
                clean_desc = clean_desc[:150] + "..."
            print(f"   Description: {clean_desc}")
    
    print("\n" + "="*60)
    print("✅ Query Complete!")
    print("="*60)
    print("\n🎯 Key Point:")
    print("   No manual embedding API calls needed!")
    print("   The vectorizer handled text-to-vector conversion automatically.")


def test_hybrid_query(query_text):
    """Test a hybrid query (vector + text)."""
    print("\n" + "="*60)
    print("Testing Hybrid Query (Vector + Text)")
    print("="*60)
    print(f"\nQuery: {query_text}")
    
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint=config.SEARCH_ENDPOINT,
        index_name=config.INDEX_NAME,
        credential=credential
    )
    
    # Vectorizable text query for vector search
    vector_query = VectorizableTextQuery(
        text=query_text,
        k_nearest_neighbors=5,
        fields="content_vector"
    )
    
    print("\n🔍 Executing hybrid query...")
    print("   (Combining text search + vector search)")
    
    # Execute hybrid search
    results = search_client.search(
        search_text=query_text,  # Text search
        vector_queries=[vector_query],  # Vector search
        select=["solution_name", "partner_name", "industries", "solution_url"],
        top=5
    )
    
    print("\n📊 Hybrid Results:")
    print("-" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('solution_name', 'N/A')}")
        print(f"   Partner: {result.get('partner_name', 'N/A')}")
        print(f"   Industries: {', '.join(result.get('industries', []))}")
        print(f"   Score: {result.get('@search.score', 0):.4f}")
    
    print("\n✅ Hybrid search combines best of both worlds!")


def main():
    """Main execution."""
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "AI solutions for healthcare patient engagement"
    
    # Test 1: Pure vector search
    test_vector_query(query)
    
    # Test 2: Hybrid search
    test_hybrid_query(query)
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\n✅ Integrated vectorization is working!")
    print(f"\n🎯 This index ({config.INDEX_NAME}) can now be used in:")
    print("   - Your FastAPI backend (update config)")
    print("   - Microsoft Copilot Studio (fully compatible!)")
    print("   - Azure Portal Search Explorer")
    
    print("\n📝 Example queries to try:")
    print("   python 05_test_query.py 'financial risk management solutions'")
    print("   python 05_test_query.py 'IoT and AI for manufacturing'")
    print("   python 05_test_query.py 'cloud security for retail'")


if __name__ == "__main__":
    main()
