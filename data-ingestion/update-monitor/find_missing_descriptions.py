#!/usr/bin/env python3
"""
Find solutions with missing descriptions from ISD API
to report to ISD team for data quality improvement.
"""
import requests
import json
import uuid
from collections import defaultdict

def fetch_all_solutions():
    """Fetch all solutions from ISD API using the industry menu approach"""
    base_url = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
    
    print("Fetching solutions from ISD API...")
    
    # Fetch industry menu
    menu_url = f"{base_url}/getMenu"
    print(f"Fetching menu from: {menu_url}")
    
    menu_response = requests.get(menu_url, timeout=30)
    menu_response.raise_for_status()
    menu_data = menu_response.json()
    
    solutions_by_id = {}
    total_entries = 0
    
    for industry in menu_data:
        industry_name = industry.get("industryName", "Unknown Industry")
        
        for theme in industry.get("subIndustries", []):
            theme_slug = theme.get("industryThemeSlug")
            theme_title = theme.get("subIndustryName", "Unknown Theme")
            
            if not theme_slug:
                continue
            
            # Fetch solutions for this theme
            theme_url = f"{base_url}/GetThemeDetalsByViewId"
            params = {"slug": theme_slug}
            
            try:
                theme_response = requests.get(theme_url, params=params, timeout=30)
                theme_response.raise_for_status()
                theme_data = theme_response.json()
            except Exception as e:
                print(f"  Error fetching theme {theme_slug}: {e}")
                continue
            
            # Solutions are nested in themeSolutionAreas
            theme_solution_areas = theme_data.get('themeSolutionAreas', [])
            
            for area in theme_solution_areas:
                area_name = area.get('solutionAreaName', 'Unknown Area')
                partner_solutions = area.get('partnerSolutions', [])
                
                for ps in partner_solutions:
                    total_entries += 1
                    solution_id = ps.get("partnerSolutionId", str(uuid.uuid4()))
                    
                    # If this solution already exists, aggregate data
                    if solution_id in solutions_by_id:
                        existing = solutions_by_id[solution_id]
                        # Add industry if not already present
                        if industry_name not in existing['industries']:
                            existing['industries'].add(industry_name)
                        if theme_title not in existing['industries'] and theme_title != industry_name:
                            existing['industries'].add(theme_title)
                        # Add technology if not already present
                        if area_name and area_name not in existing['technologies']:
                            existing['technologies'].add(area_name)
                        # Use longer description if available
                        new_desc = (ps.get("solutionDescription") or "").strip()
                        if len(new_desc) > len(existing['description']):
                            existing['description'] = new_desc
                    else:
                        # New solution
                        slug = ps.get('partnerSolutionSlug', '')
                        solutions_by_id[solution_id] = {
                            "id": solution_id,
                            "name": ps.get("solutionName", ""),
                            "partner": ps.get("orgName", ""),
                            "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{slug}",
                            "description": (ps.get("solutionDescription") or "").strip(),
                            "industries": {industry_name, theme_title} if theme_title != industry_name else {industry_name},
                            "technologies": {area_name} if area_name else set()
                        }
    
    print(f"Total entries processed: {total_entries}")
    print(f"Unique solutions: {len(solutions_by_id)}")
    
    return solutions_by_id

def find_missing_descriptions(solutions_by_id):
    """Identify solutions with missing or empty descriptions"""
    missing = []
    
    for solution_id, solution in solutions_by_id.items():
        description = solution.get("description", "")
        if not description or description.strip() == "":
            missing.append({
                "solution_id": solution_id,
                "solution_name": solution.get("name"),
                "partner_name": solution.get("partner"),
                "solution_url": solution.get("url"),
                "industries": sorted(solution.get("industries", [])),
                "technologies": sorted(solution.get("technologies", []))
            })
    
    return missing

def generate_report(missing_descriptions):
    """Generate a report of solutions with missing descriptions"""
    print("\n" + "="*80)
    print("SOLUTIONS WITH MISSING DESCRIPTIONS")
    print("="*80)
    print(f"\nTotal solutions with missing descriptions: {len(missing_descriptions)}")
    print("\nDETAILS:\n")
    
    for i, solution in enumerate(missing_descriptions, 1):
        print(f"{i}. Solution ID: {solution['solution_id']}")
        print(f"   Name: {solution['solution_name']}")
        print(f"   Partner: {solution['partner_name']}")
        print(f"   URL: {solution['solution_url']}")
        print(f"   Industries: {', '.join(solution['industries']) if solution['industries'] else 'None'}")
        print(f"   Technologies: {', '.join(solution['technologies']) if solution['technologies'] else 'None'}")
        print()
    
    # Save to JSON file for easy sharing with ISD team
    output_file = "solutions_missing_descriptions.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(missing_descriptions, f, indent=2, ensure_ascii=False)
    
    print(f"Report saved to: {output_file}")
    
    # Generate a simple CSV for Excel
    csv_file = "solutions_missing_descriptions.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("Solution ID,Solution Name,Partner Name,Solution URL,Industries,Technologies\n")
        for solution in missing_descriptions:
            industries_str = "; ".join(solution['industries'])
            technologies_str = "; ".join(solution['technologies'])
            f.write(f'"{solution["solution_id"]}","{solution["solution_name"]}","{solution["partner_name"]}","{solution["solution_url"]}","{industries_str}","{technologies_str}"\n')
    
    print(f"CSV report saved to: {csv_file}")

if __name__ == "__main__":
    try:
        # Fetch all solutions
        solutions_by_id = fetch_all_solutions()
        print(f"\nTotal unique solutions fetched: {len(solutions_by_id)}")
        
        # Find missing descriptions
        missing = find_missing_descriptions(solutions_by_id)
        
        # Generate report
        generate_report(missing)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
