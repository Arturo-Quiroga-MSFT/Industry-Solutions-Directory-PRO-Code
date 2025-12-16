"""
Example: Using ISD MCP Server with Azure AI Foundry Agent
Demonstrates how to create and use an agent with the deployed MCP server
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI configuration
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# MCP Server configuration
MCP_SERVER_URL = "https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/mcp"
MCP_SERVER_LABEL = "isd-server"

# Note: Full MCP integration via SDK requires the Azure AI Foundry Agent SDK
# This is a simplified example showing the concept

def create_isd_agent():
    """
    Create an Azure AI Foundry agent with ISD MCP tools
    
    Full implementation requires:
    pip install azure-ai-agents
    """
    
    # This is pseudocode showing the pattern
    # Actual implementation requires azure-ai-agents package
    
    agent_config = {
        "name": "ISD Solutions Assistant",
        "model": "gpt-4",
        "instructions": """
        You are an expert assistant for the Microsoft Industry Solutions Directory.
        
        Use the ISD MCP tools to help users discover Microsoft partner solutions:
        - Use list_industries to show available industry categories
        - Use list_technologies to show available technology areas  
        - Use get_solutions_by_industry when users ask about specific industries
        - Use search_solutions to find solutions by keywords
        
        Always provide solution name, partner name, description, and URL.
        """,
        "tools": [
            {
                "type": "mcp",
                "server_url": MCP_SERVER_URL,
                "server_label": MCP_SERVER_LABEL
            }
        ]
    }
    
    return agent_config


def test_direct_mcp_call():
    """
    Test calling the MCP server directly via HTTP
    This works without the full Agent SDK
    """
    import requests
    
    print("Testing Direct MCP Server Calls")
    print("=" * 60)
    
    # Test 1: List industries
    print("\n1. List Industries:")
    response = requests.post(
        f"https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/tools/list_industries"
    )
    industries = response.json()["result"]
    print(f"   Found {len(industries)} industries")
    print(f"   First 3: {industries[:3]}")
    
    # Test 2: Get solutions by industry
    print("\n2. Get Solutions for 'Student Success':")
    response = requests.post(
        f"https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/tools/get_solutions_by_industry",
        json={"industry": "Student Success"}
    )
    solutions = response.json()["result"]
    print(f"   Found {len(solutions)} solutions")
    if solutions:
        print(f"   First solution: {solutions[0]['name']} by {solutions[0]['partner']}")
    
    # Test 3: List technologies
    print("\n3. List Technologies:")
    response = requests.post(
        f"https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/tools/list_technologies"
    )
    technologies = response.json()["result"]
    print(f"   Found {len(technologies)} technologies")
    print(f"   Technologies: {technologies}")
    
    print("\n" + "=" * 60)
    print("✅ MCP Server is working correctly!")


def simulate_agent_conversation():
    """
    Simulate how an agent would use the MCP tools
    Using direct API calls to demonstrate the pattern
    """
    import requests
    
    print("\nSimulated Agent Conversation")
    print("=" * 60)
    
    user_query = "What AI solutions are available for education?"
    print(f"\nUser: {user_query}")
    print("\nAgent thinking...")
    
    # Agent would use list_industries first
    print("  → Calling list_industries...")
    response = requests.post(
        f"https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/tools/list_industries"
    )
    industries = response.json()["result"]
    
    # Find education-related industry
    education_industry = next((ind for ind in industries if "Student" in ind or "Education" in ind), None)
    print(f"  → Found relevant industry: {education_industry}")
    
    # Get solutions for that industry
    print(f"  → Calling get_solutions_by_industry('{education_industry}')...")
    response = requests.post(
        f"https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/tools/get_solutions_by_industry",
        json={"industry": education_industry}
    )
    solutions = response.json()["result"]
    
    # Filter for AI solutions
    ai_solutions = [s for s in solutions if "AI" in s.get("technology", "")]
    
    print(f"\nAgent: I found {len(ai_solutions)} AI solutions for {education_industry}:")
    for i, sol in enumerate(ai_solutions[:3], 1):
        print(f"\n{i}. {sol['name']}")
        print(f"   Partner: {sol['partner']}")
        print(f"   Technology: {sol['technology']}")
        print(f"   URL: {sol['url']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("ISD MCP Server - Azure AI Foundry Integration Example")
    print("=" * 60)
    
    # Test direct MCP calls
    test_direct_mcp_call()
    
    # Simulate agent conversation
    simulate_agent_conversation()
    
    print("\n\nTo use with Azure AI Foundry Agent Service:")
    print("1. Go to https://ai.azure.com")
    print("2. Add MCP tool with URL: https://indsolse-mcp-server.icysky-1225f4aa.swedencentral.azurecontainerapps.io/mcp")
    print("3. Create an agent and select the ISD MCP tool")
    print("4. Start chatting!")
