"""
MCP Server for Industry Solutions Directory (ISD)
Wraps the Microsoft Industry Solutions Directory API as MCP tools

Author: Arturo Quiroga, Principal Industry Solutions Architect
Date: December 12, 2025
"""

import asyncio
import httpx
from typing import Any, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
import json


# ISD API Configuration
ISD_API_BASE_URL = "https://mssoldir-app-prd.azurewebsites.net/api"
ISD_INDUSTRY_ENDPOINT = f"{ISD_API_BASE_URL}/Industry"


class ISDClient:
    """Client for interacting with the Industry Solutions Directory API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._industries_cache = None
        self._technologies_cache = None
        self._solutions_cache = None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_menu(self) -> dict:
        """Get the industry menu structure from ISD API"""
        response = await self.client.get(f"{ISD_INDUSTRY_ENDPOINT}/getMenu")
        response.raise_for_status()
        return response.json()
    
    async def get_theme_details(self, slug: str) -> dict:
        """Get detailed theme information including solutions"""
        response = await self.client.get(
            f"{ISD_INDUSTRY_ENDPOINT}/GetThemeDetalsByViewId",
            params={"slug": slug}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_all_industries(self) -> list[dict]:
        """Get all available industries (use cases) from the menu"""
        if self._industries_cache is None:
            menu = await self.get_menu()
            industries = []
            
            for item in menu:
                industry_name = item.get("industryName")
                
                if item.get("subIndustries"):
                    for sub in item["subIndustries"]:
                        slug = sub.get("industryThemeSlug")
                        sub_name = sub.get("subIndustryName")
                        
                        if slug and sub_name:
                            industries.append({
                                "name": sub_name,
                                "slug": slug,
                                "parent_industry": industry_name
                            })
            
            self._industries_cache = industries
        return self._industries_cache
    
    async def get_all_technologies(self) -> list[dict]:
        """Get all available technologies (solution areas) from the menu"""
        if self._technologies_cache is None:
            menu = await self.get_menu()
            technologies_set = set()
            
            for item in menu:
                if item.get("subIndustries"):
                    for sub in item["subIndustries"]:
                        if sub.get("solutionAreas"):
                            for area in sub["solutionAreas"]:
                                area_name = area.get("solutionAreaName")
                                if area_name:
                                    technologies_set.add(area_name)
            
            self._technologies_cache = [{"name": tech} for tech in sorted(technologies_set)]
        return self._technologies_cache
    
    async def get_solutions_by_industry(self, industry_name: str) -> list[dict]:
        """Get solutions for a specific industry use case"""
        industries = await self.get_all_industries()
        
        # Find matching industry (case-insensitive)
        industry = next(
            (i for i in industries if i["name"].lower() == industry_name.lower()),
            None
        )
        
        if not industry:
            return []
        
        # Get theme details using slug
        theme_data = await self.get_theme_details(industry["slug"])
        
        # Extract solutions from all solution areas
        solutions = []
        for area in theme_data.get("themeSolutionAreas", []):
            area_name = area.get("solutionAreaName", "")
            
            for solution in area.get("partnerSolutions", []):
                solutions.append({
                    "id": solution.get("id"),
                    "name": solution.get("solutionName", ""),
                    "partner": solution.get("orgName", ""),
                    "description": solution.get("solutionDescription", ""),
                    "url": solution.get("url", ""),
                    "logo": solution.get("logoUrl", ""),
                    "industries": solution.get("industries", []),
                    "technologies": solution.get("technologies", []),
                    "technology": area_name,
                    "industry": industry["name"],
                    "parent_industry": industry["parent_industry"]
                })
        
        # Also add spotlight solutions
        for solution in theme_data.get("spotLightPartnerSolutions", []):
            solutions.append({
                "id": solution.get("id"),
                "name": solution.get("solutionName", ""),
                "partner": solution.get("orgName", ""),
                "description": solution.get("solutionDescription", ""),
                "url": solution.get("url", ""),
                "logo": solution.get("logoUrl", ""),
                "industries": solution.get("industries", []),
                "technologies": solution.get("technologies", []),
                "technology": "Spotlight",
                "industry": industry["name"],
                "parent_industry": industry["parent_industry"]
            })
        
        return solutions
    
    async def get_solutions_by_technology(self, technology_name: str) -> list[dict]:
        """Get solutions for a specific technology across all industries"""
        industries = await self.get_all_industries()
        all_solutions = []
        seen_ids = set()
        
        # Search through all industries
        for industry in industries:
            try:
                theme_data = await self.get_theme_details(industry["slug"])
                
                for area in theme_data.get("themeSolutionAreas", []):
                    area_name = area.get("solutionAreaName", "")
                    
                    # Check if this is the technology we're looking for
                    if area_name.lower() == technology_name.lower():
                        for solution in area.get("partnerSolutions", []):
                            solution_id = solution.get("id")
                            
                            # Skip duplicates
                            if solution_id in seen_ids:
                                continue
                            seen_ids.add(solution_id)
                            
                            all_solutions.append({
                                "id": solution_id,
                                "name": solution.get("solutionName", ""),
                                "partner": solution.get("orgName", ""),
                                "description": solution.get("solutionDescription", ""),
                                "url": solution.get("url", ""),
                                "logo": solution.get("logoUrl", ""),
                                "industries": solution.get("industries", []),
                                "technologies": solution.get("technologies", []),
                                "technology": area_name,
                                "industry": industry["name"],
                                "parent_industry": industry["parent_industry"]
                            })
            except Exception:
                # Skip industries that fail
                continue
        
        return all_solutions
    
    async def search_all_solutions(
        self,
        query: Optional[str] = None,
        industry_filter: Optional[str] = None,
        technology_filter: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Search across solutions with optional filters
        If industry_filter provided: search within that industry
        If technology_filter provided: search across all industries for that technology
        If query provided: keyword search within results
        """
        all_solutions = []
        seen_ids = set()
        
        if industry_filter:
            # Search specific industry
            solutions = await self.get_solutions_by_industry(industry_filter)
            all_solutions.extend(solutions)
        
        elif technology_filter:
            # Search across all industries for technology
            solutions = await self.get_solutions_by_technology(technology_filter)
            all_solutions.extend(solutions)
        
        else:
            # Search first 5 industries for performance
            industries = await self.get_all_industries()
            for industry in industries[:5]:
                try:
                    solutions = await self.get_solutions_by_industry(industry["name"])
                    for sol in solutions:
                        if sol["id"] not in seen_ids:
                            seen_ids.add(sol["id"])
                            all_solutions.append(sol)
                except Exception:
                    continue
        
        # Apply keyword filter if provided
        if query:
            query_lower = query.lower()
            filtered_solutions = []
            
            for solution in all_solutions:
                searchable_text = (
                    f"{solution.get('name', '')} "
                    f"{solution.get('partner', '')} "
                    f"{solution.get('description', '')}"
                ).lower()
                
                if query_lower in searchable_text:
                    filtered_solutions.append(solution)
            
            all_solutions = filtered_solutions
        
        return all_solutions[:limit]


# Initialize MCP server
server = Server("isd-server")
isd_client = ISDClient()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools for ISD"""
    return [
        types.Tool(
            name="list_industries",
            description="Get a list of all available industries in the Microsoft Industry Solutions Directory",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_technologies",
            description="Get a list of all available technology categories in the Microsoft Industry Solutions Directory",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_solutions_by_industry",
            description="Get all partner solutions for a specific industry vertical",
            inputSchema={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "The industry name (e.g., 'Financial Services', 'Healthcare & Life Sciences', 'Manufacturing & Mobility')"
                    }
                },
                "required": ["industry"]
            }
        ),
        types.Tool(
            name="get_solutions_by_technology",
            description="Get all partner solutions for a specific technology category",
            inputSchema={
                "type": "object",
                "properties": {
                    "technology": {
                        "type": "string",
                        "description": "The technology category name (e.g., 'AI Business Solutions', 'Cloud and AI Platforms', 'Security')"
                    }
                },
                "required": ["technology"]
            }
        ),
        types.Tool(
            name="search_solutions",
            description="Search for partner solutions by keyword with optional industry or technology filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query keyword(s) to match against solution name, partner, or description"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Optional: Filter by specific industry name"
                    },
                    "technology": {
                        "type": "string",
                        "description": "Optional: Filter by specific technology category"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""
    
    try:
        if name == "list_industries":
            industries = await isd_client.get_all_industries()
            result = {
                "count": len(industries),
                "industries": [ind["name"] for ind in industries]
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "list_technologies":
            technologies = await isd_client.get_all_technologies()
            result = {
                "count": len(technologies),
                "technologies": [tech["name"] for tech in technologies]
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_solutions_by_industry":
            industry = arguments.get("industry", "")
            solutions = await isd_client.get_solutions_by_industry(industry)
            result = {
                "industry": industry,
                "count": len(solutions),
                "solutions": solutions
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_solutions_by_technology":
            technology = arguments.get("technology", "")
            solutions = await isd_client.get_solutions_by_technology(technology)
            result = {
                "technology": technology,
                "count": len(solutions),
                "solutions": solutions
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "search_solutions":
            query = arguments.get("query")
            industry = arguments.get("industry")
            technology = arguments.get("technology")
            limit = arguments.get("limit", 10)
            
            solutions = await isd_client.search_all_solutions(
                query=query,
                industry_filter=industry,
                technology_filter=technology,
                limit=limit
            )
            
            result = {
                "query": query,
                "industry_filter": industry,
                "technology_filter": technology,
                "count": len(solutions),
                "solutions": solutions
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        try:
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="isd-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
        finally:
            await isd_client.close()


if __name__ == "__main__":
    asyncio.run(main())
