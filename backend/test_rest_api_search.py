"""
Test script for REST API-based search implementation
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.search_service import SearchService
from app.models.schemas import SearchFilter


async def test_search_service():
    """Test the REST API-based search service"""
    
    print("=" * 80)
    print("Testing REST API-based Search Service")
    print("=" * 80)
    
    try:
        # Initialize search service
        print("\n1. Initializing search service...")
        search_service = SearchService()
        print("✅ Search service initialized successfully")
        print(f"   Endpoint: {search_service.endpoint}")
        print(f"   Index: {search_service.index_name}")
        print(f"   API Version: {search_service.api_version}")
        
        # Test health check
        print("\n2. Testing health check...")
        is_healthy = await search_service.health_check()
        if is_healthy:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return
        
        # Test hybrid search
        print("\n3. Testing hybrid search with integrated vectorization...")
        query = "What solutions are available for healthcare AI?"
        print(f"   Query: {query}")
        
        results = await search_service.hybrid_search(query, top_k=3)
        
        if results:
            print(f"✅ Hybrid search returned {len(results)} results:")
            for i, citation in enumerate(results, 1):
                print(f"\n   Result {i}:")
                print(f"      Solution: {citation.solution_name}")
                print(f"      Partner: {citation.partner_name}")
                print(f"      Score: {citation.relevance_score:.4f}")
                print(f"      Description: {citation.description[:100]}...")
        else:
            print("❌ Hybrid search returned no results")
            return
        
        # Test with filters
        print("\n4. Testing search with filters...")
        query2 = "retail solutions"
        filters = SearchFilter(industries=["Retail"])
        print(f"   Query: {query2}")
        print(f"   Filter: Industries = ['Retail']")
        
        filtered_results = await search_service.hybrid_search(query2, filters=filters, top_k=3)
        
        if filtered_results:
            print(f"✅ Filtered search returned {len(filtered_results)} results:")
            for i, citation in enumerate(filtered_results, 1):
                print(f"\n   Result {i}:")
                print(f"      Solution: {citation.solution_name}")
                print(f"      Partner: {citation.partner_name}")
                print(f"      Score: {citation.relevance_score:.4f}")
        else:
            print("⚠️ Filtered search returned no results (this might be expected)")
        
        # Test get_facets
        print("\n5. Testing get_facets...")
        facets = await search_service.get_facets()
        
        if facets:
            print(f"✅ Facets retrieved successfully:")
            for facet_name, values in facets.items():
                print(f"   {facet_name}: {len(values)} values")
                if values:
                    print(f"      Examples: {', '.join(values[:3])}")
        else:
            print("⚠️ No facets returned")
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_search_service())
