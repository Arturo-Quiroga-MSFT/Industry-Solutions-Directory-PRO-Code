"""
Test client for the ISD MCP Server
Allows testing MCP tools directly without full MCP client

Author: Arturo Quiroga
Date: December 12, 2025
"""

import asyncio
import json
from server import ISDClient


async def test_isd_client():
    """Test the ISD client functionality"""
    print("=" * 80)
    print("Testing ISD MCP Server - Client Functions")
    print("=" * 80)
    
    client = ISDClient()
    
    try:
        # Test 1: Get all industries
        print("\n[TEST 1] Listing all industries...")
        industries = await client.get_all_industries()
        print(f"✓ Found {len(industries)} industries")
        print("Sample industries:", [ind["name"] for ind in industries[:5]])
        
        # Test 2: Get all technologies
        print("\n[TEST 2] Listing all technologies...")
        technologies = await client.get_all_technologies()
        print(f"✓ Found {len(technologies)} technologies")
        print("Available technologies:", [tech["name"] for tech in technologies])
        
        # Test 3: Get solutions by industry
        print("\n[TEST 3] Getting solutions for 'Student Success'...")
        student_solutions = await client.get_solutions_by_industry("Student Success")
        print(f"✓ Found {len(student_solutions)} Student Success solutions")
        if student_solutions:
            print("\nSample solution:")
            sample = student_solutions[0]
            print(f"  - Name: {sample['name']}")
            print(f"  - Partner: {sample['partner']}")
            print(f"  - Technology: {sample['technology']}")
            desc = sample.get('description', '')
            if desc:
                # Remove HTML tags for display
                import re
                desc_clean = re.sub('<.*?>', '', desc)
                print(f"  - Description: {desc_clean[:100]}...")
        
        # Test 4: Get solutions by technology
        print("\n[TEST 4] Getting solutions for 'AI Business Solutions'...")
        ai_solutions = await client.get_solutions_by_technology("AI Business Solutions")
        print(f"✓ Found {len(ai_solutions)} AI Business Solutions")
        if ai_solutions:
            print("\nSample AI solutions:")
            for i, sample in enumerate(ai_solutions[:3], 1):
                print(f"  {i}. {sample['name']} by {sample['partner']}")
                print(f"     Industry: {sample['industry']} ({sample['parent_industry']})")
        
        # Test 5: Search solutions with query
        print("\n[TEST 5] Searching for 'copilot' solutions...")
        search_results = await client.search_all_solutions(
            query="copilot",
            limit=5
        )
        print(f"✓ Found {len(search_results)} solutions matching 'copilot'")
        for i, solution in enumerate(search_results[:3], 1):
            print(f"\n  {i}. {solution['name']} by {solution['partner']}")
        
        # Test 6: Search with industry filter
        print("\n[TEST 6] Searching 'Institutional Innovation' for 'student' solutions...")
        innovation_results = await client.search_all_solutions(
            query="student",
            industry_filter="Institutional Innovation",
            limit=5
        )
        print(f"✓ Found {len(innovation_results)} solutions with 'student'")
        for i, solution in enumerate(innovation_results[:2], 1):
            print(f"\n  {i}. {solution['name']} by {solution['partner']}")
        
        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


async def test_menu_structure():
    """Test the raw menu structure from ISD API"""
    print("\n" + "=" * 80)
    print("Testing Raw ISD API Menu Structure")
    print("=" * 80)
    
    client = ISDClient()
    
    try:
        # Get parsed industries and technologies
        industries = await client.get_all_industries()
        technologies = await client.get_all_technologies()
        
        print(f"\nParsed Industries: {len(industries)}")
        print(f"Parsed Technologies: {len(technologies)}")
        
        print("\n--- Industries ---")
        for ind in industries[:10]:  # Show first 10
            parent = ind.get('parent', '')
            parent_str = f" (under {parent})" if parent else ""
            print(f"  - {ind.get('name')}{parent_str}")
        
        print("\n--- Technologies ---")
        for tech in technologies:
            print(f"  - {tech.get('name')}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Test client functions (recommended)")
    print("2. Test raw API menu structure")
    print("3. Run both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_isd_client())
    elif choice == "2":
        asyncio.run(test_menu_structure())
    elif choice == "3":
        asyncio.run(test_menu_structure())
        print("\n")
        asyncio.run(test_isd_client())
    else:
        print("Invalid choice. Running default test...")
        asyncio.run(test_isd_client())
