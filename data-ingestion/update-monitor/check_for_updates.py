"""
ISD Website Update Checker

Owner: Arturo Quiroga, Principal Industry Solutions Architect, Microsoft
Purpose: Check for new or updated partner solutions on the ISD website
Last Updated: November 8, 2025

This script compares current ISD website content against the existing search index
to identify new, modified, or removed partner solutions.
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Tuple
import requests
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ISDUpdateChecker:
    """Check for updates in the ISD website."""
    
    def __init__(self):
        # Get search endpoint from environment or construct from service name
        self.search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        if not self.search_endpoint:
            search_service = os.getenv('AZURE_SEARCH_SERVICE', 'indsolse-dev-search')
            self.search_endpoint = f"https://{search_service}.search.windows.net"
        
        self.index_name = "partner-solutions-integrated"
        self.isd_api_base = "https://mssoldir-app-prd.azurewebsites.net/api/Industry"
        
        # Initialize search client with Azure CLI authentication
        credential = DefaultAzureCredential()
        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=credential
        )
    
    def fetch_isd_solutions(self) -> Dict[str, Dict]:
        """Fetch all current solutions from ISD website."""
        print("📥 Fetching current solutions from ISD website...")
        
        try:
            # Fetch menu structure
            menu_url = f"{self.isd_api_base}/getMenu"
            response = requests.get(menu_url, timeout=30)
            response.raise_for_status()
            menu_data = response.json()
            
            solutions = {}
            industries = menu_data if isinstance(menu_data, list) else menu_data.get("industryMenu", [])
            
            # Extract solutions by fetching each theme
            for industry in industries:
                industry_name = industry.get("industryName", "Unknown")
                
                for theme in industry.get("subIndustries", []):
                    theme_slug = theme.get("industryThemeSlug")
                    
                    if not theme_slug:
                        continue
                    
                    # Fetch solutions for this theme
                    theme_url = f"{self.isd_api_base}/GetThemeDetalsByViewId"
                    try:
                        theme_response = requests.get(theme_url, params={"slug": theme_slug}, timeout=30)
                        theme_response.raise_for_status()
                        theme_data = theme_response.json()
                        
                        # Process solution areas
                        for area in theme_data.get("themeSolutionAreas", []):
                            for item in area.get("partnerSolutions", []):
                                solution_id = item.get("partnerSolutionId", "")
                                if not solution_id:
                                    continue
                                
                                title = item.get("solutionName", "")
                                # Extract partner from title (format: "Solution Name by Partner Name")
                                partner = item.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                                
                                # Create content hash for change detection
                                content = json.dumps(item, sort_keys=True)
                                content_hash = hashlib.md5(content.encode()).hexdigest()
                                
                                solutions[solution_id] = {
                                    "id": solution_id,
                                    "title": title,
                                    "partner": partner,
                                    "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{item.get('partnerSolutionSlug', '')}",
                                    "content_hash": content_hash,
                                    "raw_data": item
                                }
                        
                        # Process spotlight solutions
                        for item in theme_data.get("spotLightPartnerSolutions", []):
                            solution_id = item.get("partnerSolutionId", "")
                            if not solution_id:
                                continue
                            
                            title = item.get("solutionName", "")
                            # Extract partner from title (format: "Solution Name by Partner Name")
                            partner = item.get("orgName") or (title.split(" by ")[-1] if " by " in title else "Unknown")
                            
                            content = json.dumps(item, sort_keys=True)
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            
                            solutions[solution_id] = {
                                "id": solution_id,
                                "title": title,
                                "partner": partner,
                                "url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{item.get('partnerSolutionSlug', '')}",
                                "content_hash": content_hash,
                                "raw_data": item
                            }
                            
                    except Exception as e:
                        print(f"  ⚠️  Error fetching theme {theme_slug}: {e}")
                        continue
            
            print(f"✅ Found {len(solutions)} solutions on ISD website")
            return solutions
            
        except Exception as e:
            print(f"❌ Error fetching ISD solutions: {e}")
            sys.exit(1)
    
    def fetch_indexed_solutions(self) -> Dict[str, Dict]:
        """Fetch all solutions currently in the search index."""
        print("📥 Fetching solutions from search index...")
        
        try:
            indexed = {}
            
            # Search for all documents with correct field names
            results = self.search_client.search(
                search_text="*",
                select=["id", "solution_name", "partner_name", "solution_url", "description"],
                include_total_count=True,
                top=1000  # Adjust if you have more than 1000 unique solutions
            )
            
            for result in results:
                solution_id = result.get("id", "")
                if solution_id:
                    # Create content hash from indexed content
                    description = result.get("description", "")
                    content_hash = hashlib.md5(description.encode()).hexdigest()
                    
                    indexed[solution_id] = {
                        "id": solution_id,
                        "title": result.get("solution_name", ""),
                        "partner": result.get("partner_name", ""),
                        "url": result.get("solution_url", ""),
                        "content_hash": content_hash
                    }
            
            print(f"✅ Found {len(indexed)} unique solutions in index")
            return indexed
            
        except Exception as e:
            print(f"❌ Error fetching indexed solutions: {e}")
            sys.exit(1)
    
    def compare_solutions(
        self, 
        isd_solutions: Dict[str, Dict], 
        indexed_solutions: Dict[str, Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare ISD solutions with indexed solutions."""
        print("\n🔍 Comparing ISD website with search index...")
        
        isd_ids = set(isd_solutions.keys())
        indexed_ids = set(indexed_solutions.keys())
        
        # Find new solutions (in ISD but not in index)
        new_ids = isd_ids - indexed_ids
        new_solutions = [isd_solutions[sid] for sid in new_ids]
        
        # Find removed solutions (in index but not in ISD)
        removed_ids = indexed_ids - isd_ids
        removed_solutions = [indexed_solutions[sid] for sid in removed_ids]
        
        # Find modified solutions (different content hash)
        modified_solutions = []
        common_ids = isd_ids & indexed_ids
        
        for sid in common_ids:
            if isd_solutions[sid]["content_hash"] != indexed_solutions[sid]["content_hash"]:
                modified_solutions.append({
                    "id": sid,
                    "title": isd_solutions[sid]["title"],
                    "partner": isd_solutions[sid]["partner"],
                    "url": isd_solutions[sid]["url"],
                    "change_type": "content_modified"
                })
        
        return new_solutions, modified_solutions, removed_solutions
    
    def save_results(
        self, 
        new: List[Dict], 
        modified: List[Dict], 
        removed: List[Dict]
    ):
        """Save comparison results to JSON files."""
        timestamp = datetime.now().isoformat()
        
        # Save summary
        summary = {
            "timestamp": timestamp,
            "new_count": len(new),
            "modified_count": len(modified),
            "removed_count": len(removed),
            "total_changes": len(new) + len(modified) + len(removed)
        }
        
        with open("last_check.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Save detailed lists
        if new:
            with open("new_solutions.json", "w") as f:
                json.dump(new, f, indent=2)
        
        if modified:
            with open("modified_solutions.json", "w") as f:
                json.dump(modified, f, indent=2)
        
        if removed:
            with open("removed_solutions.json", "w") as f:
                json.dump(removed, f, indent=2)
    
    def print_report(
        self, 
        new: List[Dict], 
        modified: List[Dict], 
        removed: List[Dict]
    ):
        """Print summary report."""
        print("\n" + "=" * 70)
        print("📊 ISD WEBSITE UPDATE CHECK REPORT")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        total_changes = len(new) + len(modified) + len(removed)
        
        if total_changes == 0:
            print("✅ No changes detected - index is up to date!")
        else:
            print(f"⚠️  Total changes detected: {total_changes}")
            print()
            
            if new:
                print(f"🆕 NEW SOLUTIONS: {len(new)}")
                for sol in new[:5]:  # Show first 5
                    print(f"   • {sol['title']} ({sol['partner']})")
                if len(new) > 5:
                    print(f"   ... and {len(new) - 5} more (see new_solutions.json)")
                print()
            
            if modified:
                print(f"✏️  MODIFIED SOLUTIONS: {len(modified)}")
                for sol in modified[:5]:  # Show first 5
                    print(f"   • {sol['title']} ({sol['partner']})")
                if len(modified) > 5:
                    print(f"   ... and {len(modified) - 5} more (see modified_solutions.json)")
                print()
            
            if removed:
                print(f"🗑️  REMOVED SOLUTIONS: {len(removed)}")
                for sol in removed[:5]:  # Show first 5
                    print(f"   • {sol['title']} ({sol['partner']})")
                if len(removed) > 5:
                    print(f"   ... and {len(removed) - 5} more (see removed_solutions.json)")
                print()
            
            print("📝 RECOMMENDATION:")
            print("   Re-run the integrated vectorization pipeline to update the index:")
            print("   cd ../integrated-vectorization")
            print("   python run_ingestion.py")
        
        print("=" * 70)
    
    def run(self):
        """Run the update check."""
        print("🚀 Starting ISD Website Update Check")
        print()
        
        # Fetch current data
        isd_solutions = self.fetch_isd_solutions()
        indexed_solutions = self.fetch_indexed_solutions()
        
        # Compare
        new, modified, removed = self.compare_solutions(isd_solutions, indexed_solutions)
        
        # Save results
        self.save_results(new, modified, removed)
        
        # Print report
        self.print_report(new, modified, removed)
        
        print("\n✅ Update check complete!")
        print(f"Results saved to: {os.getcwd()}")


def main():
    """Main entry point."""
    checker = ISDUpdateChecker()
    checker.run()


if __name__ == "__main__":
    main()
