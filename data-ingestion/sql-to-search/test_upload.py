#!/usr/bin/env python3
"""Quick test: upload via REST to bypass SDK serialization issues."""
import sys, os, json, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

# Get embedding
oai = AzureOpenAI(
    azure_endpoint=config.OPENAI_ENDPOINT,
    api_key=config.OPENAI_API_KEY,
    api_version=config.OPENAI_API_VERSION,
)
resp = oai.embeddings.create(
    input=["Test solution for healthcare"],
    model=config.EMBEDDING_DEPLOYMENT,
    dimensions=config.EMBEDDING_DIMENSIONS,
)
vec = resp.data[0].embedding

# Build document
doc = {
    "@search.action": "upload",
    "id": "testfull",
    "solution_name": "Test Solution Full",
    "solution_description": "A test desc",
    "partner_name": "Test Partner",
    "partner_description": "About partner",
    "industry": "Healthcare",
    "industries": ["Healthcare", "Life Sciences"],
    "sub_industry": "General",
    "solution_area": "AI",
    "solution_areas": ["AI Business Solutions"],
    "theme": "Digital",
    "marketplace_link": "",
    "partner_website": "",
    "logo_url": "",
    "geos": ["United States"],
    "solution_status": "Approved",
    "content": "Test solution for healthcare",
    "content_vector": vec,
}

# Upload via REST
cred = DefaultAzureCredential()
token = cred.get_token("https://search.azure.com/.default").token
url = f"{config.SEARCH_ENDPOINT}/indexes/{config.INDEX_NAME}/docs/index?api-version=2024-07-01"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
body = {"value": [doc]}
r = requests.post(url, headers=headers, json=body)
print(f"Status: {r.status_code}")
print(r.text[:500])
