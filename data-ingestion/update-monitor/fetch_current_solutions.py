"""
Fetch Current ISD Solutions

Owner: Arturo Quiroga, Principal Industry Solutions Architect, Microsoft
Purpose: Utility to fetch and save current partner solutions from ISD website
Last Updated: November 8, 2025

Simple utility script to fetch all current solutions from the ISD API
and save to a JSON file for analysis or comparison.
"""

import json
import argparse
from datetime import datetime
import requests


def fetch_solutions(output_file: str = "current_solutions.json"):
    """Fetch all current solutions from ISD website API."""
    
    # ISD API Base
    api_base = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
    menu_url = f"{api_base}/getMenu"
    
    print("📥 Fetching industry menu from ISD website...")
    print(f"API: {menu_url}")
    
    try:
        # Fetch menu structure
        response = requests.get(menu_url, timeout=30)
        response.raise_for_status()
        menu_data = response.json()
        
        # Extract all solutions by fetching each theme
        items = []
        industries = menu_data if isinstance(menu_data, list) else menu_data.get("industryMenu", [])
        
        print(f"📥 Fetching solutions from themes...")
        
        for industry in industries:
            industry_name = industry.get("industryName", "Unknown")
            
            for theme in industry.get("subIndustries", []):
                theme_slug = theme.get("industryThemeSlug")
                theme_name = theme.get("subIndustryName", "Unknown")
                
                if not theme_slug:
                    continue
                
                # Fetch solutions for this theme
                theme_url = f"{api_base}/GetThemeDetalsByViewId"
                try:
                    theme_response = requests.get(theme_url, params={"slug": theme_slug}, timeout=30)
                    theme_response.raise_for_status()
                    theme_data = theme_response.json()
                    
                    # Extract solutions from solution areas
                    for area in theme_data.get("themeSolutionAreas", []):
                        for solution in area.get("partnerSolutions", []):
                            title = solution.get("solutionName", "")
                            # Extract partner from title (format: "Solution Name by Partner Name")
                            partner = solution.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                            
                            items.append({
                                "id": solution.get("partnerSolutionId"),
                                "title": title,
                                "description": solution.get("solutionDescription", ""),
                                "industry": industry_name,
                                "theme": theme_name,
                                "partner": partner,
                                "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{solution.get('partnerSolutionSlug', '')}"
                            })
                    
                    # Also get spotlight solutions
                    for solution in theme_data.get("spotLightPartnerSolutions", []):
                        title = solution.get("solutionName", "")
                        # Extract partner from title (format: "Solution Name by Partner Name")
                        partner = solution.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                        
                        items.append({
                            "id": solution.get("partnerSolutionId"),
                            "title": title,
                            "description": solution.get("solutionDescription", ""),
                            "industry": industry_name,
                            "theme": theme_name,
                            "partner": partner,
                            "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{solution.get('partnerSolutionSlug', '')}",
                            "spotlight": True
                        })
                        
                except Exception as e:
                    print(f"  ⚠️  Error fetching theme {theme_slug}: {e}")
                    continue
        
        print(f"✅ Found {len(items)} solutions")
        
        # Add metadata
        result = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "api_url": menu_url,
                "total_count": len(items)
            },
            "solutions": items
        }
        
        # Save to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved to: {output_file}")
        
        # Print summary
        print("\n📊 Summary:")
        partners = {}
        for item in items:
            partner = item.get("partner", "Unknown")
            partners[partner] = partners.get(partner, 0) + 1
        
        print(f"Total solutions: {len(items)}")
        print(f"Unique partners: {len(partners)}")
        print(f"\nTop 5 partners:")
        for partner, count in sorted(partners.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {partner}: {count} solutions")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching solutions: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch current partner solutions from ISD website"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="current_solutions.json",
        help="Output JSON file (default: current_solutions.json)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Fetching Current ISD Solutions")
    print("=" * 60)
    
    success = fetch_solutions(args.output)
    
    if success:
        print("\n✅ Fetch complete!")
    else:
        print("\n❌ Fetch failed")
        exit(1)


if __name__ == "__main__":
    main()
