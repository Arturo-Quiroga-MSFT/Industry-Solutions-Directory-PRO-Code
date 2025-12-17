#!/usr/bin/env python3
"""
ISD API Endpoint Discovery Script
Date: December 16, 2025
Purpose: Comprehensive discovery of all API endpoints and parameters
"""

import requests
import json
from typing import Dict, List, Tuple
import time

BASE_URL = "https://mssoldir-app-prd.azurewebsites.net"
API_BASE = f"{BASE_URL}/api"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_endpoint(path: str, params: Dict = None) -> Tuple[int, any]:
    """Test an endpoint and return status code and response"""
    url = f"{API_BASE}/{path}"
    try:
        response = requests.get(url, params=params, timeout=10)
        try:
            data = response.json()
        except:
            data = response.text[:200]
        return response.status_code, data
    except Exception as e:
        return 0, str(e)


def print_result(endpoint: str, status: int, note: str = ""):
    """Print colored result"""
    if status == 200:
        print(f"{GREEN}✓{RESET} [{status}] {endpoint} {note}")
    elif status == 404:
        print(f"{RED}✗{RESET} [{status}] {endpoint}")
    elif status in [400, 500]:
        print(f"{YELLOW}⚠{RESET} [{status}] {endpoint} {note}")
    else:
        print(f"{BLUE}?{RESET} [{status}] {endpoint} {note}")


def discover_industry_endpoints():
    """Discover all Industry controller endpoints"""
    print(f"\n{BLUE}=== INDUSTRY CONTROLLER ==={RESET}")
    
    methods = [
        "getMenu",
        "GetThemeDetalsByViewId",
        "GetPartnerSolutions",
        "GetAll",
        "GetById",
        "Search",
        "GetSolutions",
        "GetIndustries",
        "GetThemes",
        "GetSolutionAreas",
        "GetTechnologies",
        "ListAll",
        "GetDetails",
        "GetPartnerById",
        "GetSolutionById",
        "GetThemeById",
        "Filter",
        "Query"
    ]
    
    results = {}
    for method in methods:
        status, data = test_endpoint(f"Industry/{method}")
        print_result(f"Industry/{method}", status)
        results[method] = {"status": status, "requires_params": status in [400, 500]}
        time.sleep(0.1)  # Rate limiting
    
    return results


def discover_root_controllers():
    """Discover root level API controllers"""
    print(f"\n{BLUE}=== ROOT CONTROLLERS ==={RESET}")
    
    controllers = [
        "Industry",
        "Technology",
        "Partner",
        "Solution",
        "Search",
        "Theme",
        "Category",
        "SolutionArea",
        "Organization"
    ]
    
    results = {}
    for controller in controllers:
        status, data = test_endpoint(controller)
        print_result(controller, status)
        results[controller] = status
        time.sleep(0.1)
    
    return results


def test_get_partner_solutions():
    """Test GetPartnerSolutions with actual IDs"""
    print(f"\n{BLUE}=== TESTING GetPartnerSolutions ==={RESET}")
    
    # First, get some actual IDs from a theme
    print("Fetching actual solution IDs...")
    status, menu_data = test_endpoint("Industry/getMenu")
    
    if status == 200 and menu_data:
        # Get first theme slug
        theme_slug = None
        for industry in menu_data[:3]:
            if 'subIndustries' in industry and industry['subIndustries']:
                for sub in industry['subIndustries']:
                    if 'industryThemeSlug' in sub:
                        theme_slug = sub['industryThemeSlug']
                        break
                if theme_slug:
                    break
        
        if theme_slug:
            print(f"Testing with theme: {theme_slug[:50]}...")
            status, theme_data = test_endpoint(f"Industry/GetThemeDetalsByViewId", {"slug": theme_slug})
            
            if status == 200 and 'themeSolutionAreas' in theme_data:
                solution_ids = []
                for area in theme_data['themeSolutionAreas']:
                    if 'partnerSolutions' in area:
                        for sol in area['partnerSolutions'][:2]:
                            if 'id' in sol:
                                solution_ids.append(sol['id'])
                
                print(f"\nFound {len(solution_ids)} solution IDs")
                
                # Test GetPartnerSolutions with actual IDs
                if solution_ids:
                    print(f"\nTesting GetPartnerSolutions?solutionId=...")
                    status, data = test_endpoint("Industry/GetPartnerSolutions", {"solutionId": solution_ids[0]})
                    print_result(f"GetPartnerSolutions (solutionId={solution_ids[0][:8]}...)", status, 
                                f"- Response length: {len(str(data))}")
                    
                    if status == 200 and data:
                        print(f"{GREEN}Response preview:{RESET}")
                        print(json.dumps(data, indent=2)[:500])


def discover_parameter_patterns():
    """Test various parameter patterns"""
    print(f"\n{BLUE}=== PARAMETER PATTERNS ==={RESET}")
    
    test_params = [
        ("Industry/GetThemeDetalsByViewId", {"slug": "test"}),
        ("Industry/GetThemeDetalsByViewId", {"viewId": "test"}),
        ("Industry/GetThemeDetalsByViewId", {"id": "test"}),
        ("Industry/GetPartnerSolutions", {"partnerId": "test-guid"}),
        ("Industry/GetPartnerSolutions", {"solutionId": "test-guid"}),
        ("Industry/GetPartnerSolutions", {"industryId": "test-guid"}),
    ]
    
    for endpoint, params in test_params:
        status, data = test_endpoint(endpoint, params)
        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
        print_result(f"{endpoint}?{param_str}", status)
        time.sleep(0.1)


def main():
    """Run comprehensive API discovery"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}ISD API ENDPOINT DISCOVERY{RESET}")
    print(f"{BLUE}Date: December 16, 2025{RESET}")
    print(f"{BLUE}Base URL: {BASE_URL}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Run all discovery tests
    root_results = discover_root_controllers()
    industry_results = discover_industry_endpoints()
    discover_parameter_patterns()
    test_get_partner_solutions()
    
    # Summary
    print(f"\n{BLUE}=== SUMMARY ==={RESET}")
    print(f"\n{GREEN}Working Endpoints:{RESET}")
    print(f"  • Industry/getMenu - Returns navigation structure")
    print(f"  • Industry/GetThemeDetalsByViewId?slug={{slug}} - Theme details with solutions")
    print(f"  • Industry/GetPartnerSolutions?solutionId={{id}} - Solution details")
    
    print(f"\n{YELLOW}Endpoints Requiring Further Investigation:{RESET}")
    for method, result in industry_results.items():
        if result.get('requires_params'):
            print(f"  • Industry/{method} - Returns 400/500 (may need specific parameters)")
    
    print(f"\n{RED}Not Available:{RESET}")
    for controller, status in root_results.items():
        if status == 404:
            print(f"  • {controller}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print("Discovery complete! Results saved to: api_discovery_results.json")
    
    # Save results to file
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": BASE_URL,
        "root_controllers": root_results,
        "industry_methods": industry_results
    }
    
    with open("api_discovery_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
