#!/usr/bin/env python3
"""
Step 1: Export Industry Solutions Directory data to Azure Blob Storage.

This script fetches data from the ISD API and uploads it to Blob Storage
in a format that Azure AI Search indexers can consume.
"""

import os
import sys
import json
import uuid
import requests
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
from tqdm import tqdm

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import STORAGE_ACCOUNT_URL, STORAGE_CONTAINER_NAME, ISD_API_BASE

def fetch_industry_menu():
    """Fetch the industry menu from ISD API."""
    url = f"{ISD_API_BASE}/getMenu"
    print(f"Fetching industry menu from: {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_theme_solutions(theme_slug):
    """Fetch solutions for a specific theme."""
    url = f"{ISD_API_BASE}/GetThemeDetalsByViewId"
    params = {"slug": theme_slug}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ⚠️  Error fetching theme {theme_slug}: {e}")
        return None


def prepare_blob_documents(menu_data):
    """
    Convert ISD API data to blob-friendly JSON documents.
    De-duplicates solutions and aggregates industries/technologies.
    Each unique solution becomes ONE document with all its industries and technologies.
    """
    # Dictionary to collect all appearances of each solution
    solutions_by_id = {}
    industry_count = 0
    theme_count = 0
    total_entries = 0
    
    print("\n📥 Fetching solutions from ISD API...")
    
    for industry in tqdm(menu_data, desc="Processing industries"):
        industry_count += 1
        industry_name = industry.get("industryName", "Unknown Industry")
        
        for theme in industry.get("subIndustries", []):
            theme_count += 1
            theme_slug = theme.get("industryThemeSlug")
            theme_title = theme.get("subIndustryName", "Unknown Theme")
            
            if not theme_slug:
                continue
            
            # Fetch solutions for this theme
            theme_data = fetch_theme_solutions(theme_slug)
            
            if not theme_data:
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
                            existing['industries'].append(industry_name)
                        if theme_title not in existing['industries'] and theme_title != industry_name:
                            existing['industries'].append(theme_title)
                        # Add technology if not already present
                        if area_name and area_name not in existing['technologies']:
                            existing['technologies'].append(area_name)
                        # Use longer description if available
                        new_desc = ps.get("solutionDescription", "")
                        if len(new_desc) > len(existing['description']):
                            existing['description'] = new_desc
                            existing['content'] = f"{existing['solution_name']}\n\n{new_desc}"
                    else:
                        # First time seeing this solution
                        solutions_by_id[solution_id] = {
                            "id": solution_id,
                            "solution_name": ps.get("solutionName", ""),
                            "partner_name": ps.get("orgName", ""),
                            "description": ps.get("solutionDescription", ""),
                            "solution_url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{ps.get('partnerSolutionSlug', '')}",
                            "industries": [industry_name, theme_title],
                            "technologies": [area_name] if area_name else [],
                            # Combined text for chunking and vectorization
                            "content": f"{ps.get('solutionName', '')}\n\n{ps.get('solutionDescription', '')}",
                        }
            
            # Also get spotlight solutions
            spotlight_solutions = theme_data.get('spotLightPartnerSolutions', [])
            for ps in spotlight_solutions:
                total_entries += 1
                solution_id = ps.get("partnerSolutionId", str(uuid.uuid4()))
                
                # If this solution already exists, aggregate data
                if solution_id in solutions_by_id:
                    existing = solutions_by_id[solution_id]
                    if industry_name not in existing['industries']:
                        existing['industries'].append(industry_name)
                    if theme_title not in existing['industries'] and theme_title != industry_name:
                        existing['industries'].append(theme_title)
                    if "Spotlight" not in existing['technologies']:
                        existing['technologies'].append("Spotlight")
                    # Use longer description if available
                    new_desc = ps.get("solutionDescription", "")
                    if len(new_desc) > len(existing['description']):
                        existing['description'] = new_desc
                        existing['content'] = f"{existing['solution_name']}\n\n{new_desc}"
                else:
                    # First time seeing this solution
                    solutions_by_id[solution_id] = {
                        "id": solution_id,
                        "solution_name": ps.get("solutionName", ""),
                        "partner_name": ps.get("orgName", ""),
                        "description": ps.get("solutionDescription", ""),
                        "solution_url": f"https://solutions.microsoftindustryinsights.com/solutiondetails/{ps.get('partnerSolutionSlug', '')}",
                        "industries": [industry_name, theme_title],
                        "technologies": ["Spotlight"],
                        # Combined text for chunking and vectorization
                        "content": f"{ps.get('solutionName', '')}\n\n{ps.get('solutionDescription', '')}",
                    }
    
    # Convert dictionary to list
    documents = list(solutions_by_id.values())
    
    # Convert industries and technologies lists to comma-separated strings for search
    for doc in documents:
        # Remove duplicates and join
        doc['industries'] = ', '.join(sorted(set(doc['industries'])))
        doc['technologies'] = ', '.join(sorted(set(doc['technologies'])))
    
    print(f"\n✅ De-duplication complete!")
    print(f"   Total entries fetched: {total_entries}")
    print(f"   Unique solutions: {len(documents)}")
    print(f"   Duplicates removed: {total_entries - len(documents)}")
    print(f"   Industries processed: {industry_count}")
    print(f"   Themes processed: {theme_count}")
    
    return documents


def upload_to_blob(documents):
    """Upload documents to Azure Blob Storage."""
    print(f"\n📤 Uploading {len(documents)} documents to Blob Storage...")
    
    try:
        # Create blob service client with Azure AD
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
        
        # Create container if it doesn't exist
        container_client = blob_service_client.get_container_client(STORAGE_CONTAINER_NAME)
        try:
            container_client.create_container()
            print(f"✅ Created container: {STORAGE_CONTAINER_NAME}")
        except Exception:
            print(f"✅ Container already exists: {STORAGE_CONTAINER_NAME}")
        
        # Upload each document as a separate JSON blob
        uploaded_count = 0
        for doc in tqdm(documents, desc="Uploading blobs"):
            blob_name = f"solutions/{doc['id']}.json"
            blob_client = blob_service_client.get_blob_client(
                container=STORAGE_CONTAINER_NAME,
                blob=blob_name
            )
            
            # Upload the document
            blob_client.upload_blob(
                json.dumps(doc, indent=2),
                overwrite=True
            )
            uploaded_count += 1
        
        print(f"\n✅ Uploaded {uploaded_count} documents to blob storage")
        print(f"   Container: {STORAGE_CONTAINER_NAME}")
        print(f"   Blobs: solutions/*.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to blob storage: {e}")
        return False


def main():
    """Main execution."""
    print("="*60)
    print("Export ISD Data to Azure Blob Storage")
    print("="*60)
    
    # Step 1: Fetch data from ISD API
    menu_data = fetch_industry_menu()
    
    # Step 2: Prepare documents
    documents = prepare_blob_documents(menu_data)
    
    if not documents:
        print("❌ No documents to upload!")
        return
    
    # Step 3: Upload to Blob Storage
    success = upload_to_blob(documents)
    
    if success:
        print("\n" + "="*60)
        print("✅ Export Complete!")
        print("="*60)
        print("\nNext Steps:")
        print("  1. Run 02_create_index.py to create the search index")
        print("  2. Run 03_create_skillset.py to set up chunking and embedding")
        print("  3. Run 04_create_indexer.py to start the indexing pipeline")
    else:
        print("\n❌ Export failed. Please check the errors above.")


if __name__ == "__main__":
    main()
